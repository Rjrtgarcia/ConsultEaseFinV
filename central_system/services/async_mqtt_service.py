"""
Asynchronous MQTT service for ConsultEase system.
Provides non-blocking MQTT operations to improve UI responsiveness on Raspberry Pi.
"""

import asyncio
import json
import logging
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from queue import Queue, Empty
from typing import Dict, Callable, Optional, Any
import paho.mqtt.client as mqtt

logger = logging.getLogger(__name__)


class AsyncMQTTService:
    """
    Asynchronous MQTT service that handles publishing and subscribing without blocking the UI.
    Uses a background thread pool and message queuing for optimal performance on Raspberry Pi.
    """

    def __init__(self, broker_host='localhost', broker_port=1883, username=None, password=None, max_queue_size=1000):
        """
        Initialize the asynchronous MQTT service.

        Args:
            broker_host: MQTT broker hostname
            broker_port: MQTT broker port
            username: MQTT username (optional)
            password: MQTT password (optional)
            max_queue_size: Maximum queue size for pending messages
        """
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.username = username
        self.password = password
        self.max_queue_size = max_queue_size

        # MQTT client
        self.client = None
        self.is_connected = False

        # Asynchronous components
        self.executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="mqtt")
        self.publish_queue = Queue()
        self.message_handlers: Dict[str, Callable] = {}

        # Background threads
        self.publish_thread = None
        self.connection_monitor_thread = None
        self.running = False

        # Connection monitoring
        self.last_ping = 0
        self.ping_interval = 30  # seconds
        self.reconnect_delay = 5  # seconds
        self.max_reconnect_attempts = 10

        # Performance metrics
        self.messages_published = 0
        self.messages_received = 0
        self.publish_errors = 0
        self.dropped_messages = 0
        self.last_error = None

        # Initialize client
        self._initialize_client()

    def _initialize_client(self):
        """Initialize MQTT client with callbacks."""
        try:
            self.client = mqtt.Client()

            # Set authentication if provided
            if self.username and self.password:
                self.client.username_pw_set(self.username, self.password)

            # Set callbacks
            self.client.on_connect = self._on_connect
            self.client.on_disconnect = self._on_disconnect
            self.client.on_message = self._on_message
            self.client.on_publish = self._on_publish

            # Configure client options for reliability
            self.client.reconnect_delay_set(min_delay=1, max_delay=120)
            self.client.max_inflight_messages_set(20)
            self.client.max_queued_messages_set(100)

            logger.debug("MQTT client initialized")

        except Exception as e:
            logger.error(f"Error initializing MQTT client: {e}")
            self.last_error = str(e)

    def _on_connect(self, client, userdata, flags, rc):
        """Handle MQTT connection."""
        if rc == 0:
            self.is_connected = True
            self.last_ping = time.time()
            logger.info(f"Connected to MQTT broker at {self.broker_host}:{self.broker_port}")

            # Resubscribe to all topics
            for topic in self.message_handlers.keys():
                try:
                    client.subscribe(topic)
                    logger.debug(f"Resubscribed to topic: {topic}")
                except Exception as e:
                    logger.error(f"Error resubscribing to topic {topic}: {e}")
        else:
            self.is_connected = False
            logger.error(f"Failed to connect to MQTT broker. Return code: {rc}")

    def _on_disconnect(self, client, userdata, rc):
        """Handle MQTT disconnection."""
        self.is_connected = False
        if rc != 0:
            logger.warning(f"Unexpected MQTT disconnection. Return code: {rc}")
        else:
            logger.info("MQTT client disconnected")

    def _on_message(self, client, userdata, msg):
        """Handle incoming MQTT messages."""
        try:
            self.messages_received += 1
            topic = msg.topic

            # Decode payload
            try:
                payload = msg.payload.decode('utf-8')
                data = json.loads(payload)
            except json.JSONDecodeError:
                # If not JSON, treat as string
                data = payload
            except UnicodeDecodeError:
                logger.error(f"Failed to decode message payload for topic {topic}")
                return

            # Find matching handler
            handler = self._find_message_handler(topic)
            if handler:
                # Execute handler in thread pool to avoid blocking
                self.executor.submit(self._execute_handler, handler, topic, data)
            else:
                logger.debug(f"No handler found for topic: {topic}")

        except Exception as e:
            logger.error(f"Error processing MQTT message: {e}")

    def _on_publish(self, client, userdata, mid):
        """Handle successful message publication."""
        logger.debug(f"Message published successfully (mid: {mid})")

    def _find_message_handler(self, topic: str) -> Optional[Callable]:
        """Find the appropriate message handler for a topic."""
        # Exact match first
        if topic in self.message_handlers:
            return self.message_handlers[topic]

        # Wildcard matching
        for pattern, handler in self.message_handlers.items():
            if self._topic_matches(topic, pattern):
                return handler

        return None

    def _topic_matches(self, topic: str, pattern: str) -> bool:
        """Check if topic matches pattern with wildcards."""
        if '+' not in pattern and '#' not in pattern:
            return topic == pattern

        topic_parts = topic.split('/')
        pattern_parts = pattern.split('/')

        # Handle # wildcard
        if pattern.endswith('#'):
            pattern_parts = pattern_parts[:-1]
            return topic_parts[:len(pattern_parts)] == pattern_parts

        # Handle + wildcards
        if len(topic_parts) != len(pattern_parts):
            return False

        for topic_part, pattern_part in zip(topic_parts, pattern_parts):
            if pattern_part != '+' and pattern_part != topic_part:
                return False

        return True

    def _execute_handler(self, handler: Callable, topic: str, data: Any):
        """Execute message handler safely."""
        try:
            handler(topic, data)
        except Exception as e:
            logger.error(f"Error in message handler for topic {topic}: {e}")

    def start(self):
        """Start the asynchronous MQTT service."""
        if self.running:
            logger.warning("MQTT service is already running")
            return

        self.running = True

        # Start background threads
        self.publish_thread = threading.Thread(
            target=self._publish_worker,
            name="mqtt-publisher",
            daemon=True
        )
        self.publish_thread.start()

        self.connection_monitor_thread = threading.Thread(
            target=self._connection_monitor,
            name="mqtt-monitor",
            daemon=True
        )
        self.connection_monitor_thread.start()

        # Connect to broker
        self.connect()

        logger.info("Asynchronous MQTT service started")

    def stop(self):
        """Stop the asynchronous MQTT service."""
        self.running = False

        # Disconnect from broker
        if self.client and self.is_connected:
            self.client.disconnect()

        # Shutdown thread pool
        self.executor.shutdown(wait=True)

        logger.info("Asynchronous MQTT service stopped")

    def connect(self):
        """Connect to MQTT broker asynchronously."""
        if not self.client:
            self._initialize_client()

        def _connect():
            try:
                self.client.connect_async(self.broker_host, self.broker_port, 60)
                self.client.loop_start()
                logger.debug("MQTT connection initiated")
            except Exception as e:
                logger.error(f"Error connecting to MQTT broker: {e}")
                self.last_error = str(e)

        # Execute connection in thread pool
        self.executor.submit(_connect)

    def disconnect(self):
        """Disconnect from MQTT broker."""
        if self.client:
            self.client.loop_stop()
            self.client.disconnect()

    def publish_async(self, topic: str, data: Any, qos: int = 1, retain: bool = False):
        """
        Publish message asynchronously without blocking.

        Args:
            topic: MQTT topic
            data: Data to publish (will be JSON encoded if not string)
            qos: Quality of service level
            retain: Whether to retain the message
        """
        message = {
            'topic': topic,
            'data': data,
            'qos': qos,
            'retain': retain,
            'timestamp': time.time()
        }

        try:
            # Check queue size before adding
            if self.publish_queue.qsize() >= self.max_queue_size:
                # Remove oldest message to make room
                try:
                    self.publish_queue.get_nowait()
                    self.dropped_messages += 1
                    logger.warning(f"Dropped oldest message due to queue overflow. Total dropped: {self.dropped_messages}")
                except Empty:
                    pass

            self.publish_queue.put(message, timeout=1)
            logger.debug(f"Message queued for publication to {topic}")
        except Exception as e:
            logger.error(f"Failed to queue message for topic {topic}: {e}")
            self.publish_errors += 1

    def _publish_worker(self):
        """Background worker for publishing messages."""
        while self.running:
            try:
                # Get message from queue with timeout
                message = self.publish_queue.get(timeout=1)

                if not self.is_connected:
                    logger.warning(f"Cannot publish to {message['topic']}: not connected")
                    self.publish_errors += 1
                    continue

                # Prepare payload
                if isinstance(message['data'], str):
                    payload = message['data']
                else:
                    payload = json.dumps(message['data'])

                # Publish message
                result = self.client.publish(
                    message['topic'],
                    payload,
                    qos=message['qos'],
                    retain=message['retain']
                )

                if result.rc == mqtt.MQTT_ERR_SUCCESS:
                    self.messages_published += 1
                    logger.debug(f"Published message to {message['topic']}")
                else:
                    logger.error(f"Failed to publish to {message['topic']}: {result.rc}")
                    self.publish_errors += 1

            except Empty:
                # Timeout - continue loop
                continue
            except Exception as e:
                logger.error(f"Error in publish worker: {e}")
                self.publish_errors += 1

    def _connection_monitor(self):
        """Monitor connection and handle reconnection."""
        reconnect_attempts = 0

        while self.running:
            try:
                current_time = time.time()

                # Check if we need to reconnect
                if not self.is_connected and reconnect_attempts < self.max_reconnect_attempts:
                    logger.info(f"Attempting to reconnect to MQTT broker (attempt {reconnect_attempts + 1})")
                    self.connect()
                    reconnect_attempts += 1
                    time.sleep(self.reconnect_delay)
                elif self.is_connected:
                    # Reset reconnect attempts on successful connection
                    reconnect_attempts = 0

                    # Update last ping time (ping functionality removed as paho-mqtt doesn't have ping method)
                    if current_time - self.last_ping > self.ping_interval:
                        # Just update the timestamp - the MQTT client handles keepalive automatically
                        self.last_ping = current_time
                        logger.debug("MQTT keepalive check - connection is active")

                time.sleep(5)  # Check every 5 seconds

            except Exception as e:
                logger.error(f"Error in connection monitor: {e}")
                time.sleep(10)

    def register_topic_handler(self, topic: str, handler: Callable):
        """
        Register a handler for a specific topic.

        Args:
            topic: MQTT topic (supports wildcards + and #)
            handler: Callable that takes (topic, data) as arguments
        """
        self.message_handlers[topic] = handler

        # Subscribe to topic if connected
        if self.is_connected and self.client:
            try:
                self.client.subscribe(topic)
                logger.info(f"Subscribed to topic: {topic}")
            except Exception as e:
                logger.error(f"Error subscribing to topic {topic}: {e}")

        logger.debug(f"Registered handler for topic: {topic}")

    def unregister_topic_handler(self, topic: str):
        """Unregister a topic handler."""
        if topic in self.message_handlers:
            del self.message_handlers[topic]

            # Unsubscribe from topic if connected
            if self.is_connected and self.client:
                try:
                    self.client.unsubscribe(topic)
                    logger.info(f"Unsubscribed from topic: {topic}")
                except Exception as e:
                    logger.error(f"Error unsubscribing from topic {topic}: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """Get service statistics."""
        return {
            'connected': self.is_connected,
            'messages_published': self.messages_published,
            'messages_received': self.messages_received,
            'publish_errors': self.publish_errors,
            'dropped_messages': self.dropped_messages,
            'queue_size': self.publish_queue.qsize(),
            'max_queue_size': self.max_queue_size,
            'last_error': self.last_error,
            'last_ping': self.last_ping
        }


# Global service instance
_async_mqtt_service: Optional[AsyncMQTTService] = None


def get_async_mqtt_service() -> AsyncMQTTService:
    """Get the global asynchronous MQTT service instance."""
    global _async_mqtt_service
    if _async_mqtt_service is None:
        # Import configuration
        from ..utils.config_manager import get_config

        _async_mqtt_service = AsyncMQTTService(
            broker_host=get_config('mqtt.broker_host', 'localhost'),
            broker_port=get_config('mqtt.broker_port', 1883),
            username=get_config('mqtt.username'),
            password=get_config('mqtt.password')
        )

    return _async_mqtt_service
