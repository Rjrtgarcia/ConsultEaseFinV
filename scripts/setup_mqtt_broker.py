#!/usr/bin/env python3
"""
MQTT Broker Setup Script for ConsultEase System.
Installs and configures Mosquitto MQTT broker on Raspberry Pi.
"""

import os
import sys
import subprocess
import logging
import time
import socket
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def run_command(command, check=True, capture_output=True):
    """Run a shell command and return the result."""
    try:
        logger.info(f"Running command: {command}")
        result = subprocess.run(
            command,
            shell=True,
            check=check,
            capture_output=capture_output,
            text=True
        )
        if result.stdout:
            logger.debug(f"Command output: {result.stdout.strip()}")
        return result
    except subprocess.CalledProcessError as e:
        logger.error(f"Command failed: {command}")
        logger.error(f"Error: {e}")
        if e.stdout:
            logger.error(f"Stdout: {e.stdout}")
        if e.stderr:
            logger.error(f"Stderr: {e.stderr}")
        raise


def check_mqtt_broker_running():
    """Check if MQTT broker is already running."""
    try:
        # Check if port 1883 is open
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex(('localhost', 1883))
        sock.close()
        
        if result == 0:
            logger.info("✅ MQTT broker is already running on port 1883")
            return True
        else:
            logger.info("❌ MQTT broker is not running on port 1883")
            return False
    except Exception as e:
        logger.error(f"Error checking MQTT broker: {e}")
        return False


def install_mosquitto():
    """Install Mosquitto MQTT broker."""
    try:
        logger.info("🔄 Installing Mosquitto MQTT broker...")
        
        # Update package list
        run_command("sudo apt update")
        
        # Install mosquitto and mosquitto-clients
        run_command("sudo apt install -y mosquitto mosquitto-clients")
        
        logger.info("✅ Mosquitto MQTT broker installed successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to install Mosquitto: {e}")
        return False


def configure_mosquitto():
    """Configure Mosquitto MQTT broker."""
    try:
        logger.info("🔄 Configuring Mosquitto MQTT broker...")
        
        # Create mosquitto configuration
        config_content = """# Mosquitto configuration for ConsultEase
# Basic configuration
pid_file /var/run/mosquitto.pid
persistence true
persistence_location /var/lib/mosquitto/
log_dest file /var/log/mosquitto/mosquitto.log
log_type error
log_type warning
log_type notice
log_type information

# Network configuration
port 1883
bind_address 0.0.0.0

# Security configuration
allow_anonymous true

# Connection limits
max_connections 100
max_inflight_messages 20
max_queued_messages 100

# Logging
connection_messages true
log_timestamp true

# Performance tuning
sys_interval 10
"""
        
        # Write configuration file
        config_path = "/etc/mosquitto/conf.d/consultease.conf"
        logger.info(f"Writing configuration to {config_path}")
        
        with open("/tmp/consultease_mosquitto.conf", "w") as f:
            f.write(config_content)
        
        # Copy to mosquitto config directory
        run_command(f"sudo cp /tmp/consultease_mosquitto.conf {config_path}")
        run_command("sudo chown root:root {config_path}")
        run_command("sudo chmod 644 {config_path}")
        
        logger.info("✅ Mosquitto configuration created successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to configure Mosquitto: {e}")
        return False


def start_mosquitto_service():
    """Start and enable Mosquitto service."""
    try:
        logger.info("🔄 Starting Mosquitto service...")
        
        # Enable mosquitto service
        run_command("sudo systemctl enable mosquitto")
        
        # Start mosquitto service
        run_command("sudo systemctl start mosquitto")
        
        # Wait a moment for service to start
        time.sleep(2)
        
        # Check service status
        result = run_command("sudo systemctl is-active mosquitto", check=False)
        if result.returncode == 0 and "active" in result.stdout:
            logger.info("✅ Mosquitto service started successfully")
            return True
        else:
            logger.error("❌ Mosquitto service failed to start")
            # Show service status for debugging
            run_command("sudo systemctl status mosquitto", check=False)
            return False
            
    except Exception as e:
        logger.error(f"❌ Failed to start Mosquitto service: {e}")
        return False


def test_mqtt_connection():
    """Test MQTT broker connection."""
    try:
        logger.info("🔄 Testing MQTT broker connection...")
        
        # Test with mosquitto_pub and mosquitto_sub
        import threading
        import time
        
        # Start subscriber in background
        def run_subscriber():
            try:
                run_command(
                    "timeout 5 mosquitto_sub -h localhost -t test/topic",
                    check=False,
                    capture_output=False
                )
            except:
                pass
        
        subscriber_thread = threading.Thread(target=run_subscriber)
        subscriber_thread.start()
        
        # Wait a moment then publish
        time.sleep(1)
        result = run_command(
            "mosquitto_pub -h localhost -t test/topic -m 'ConsultEase MQTT Test'",
            check=False
        )
        
        if result.returncode == 0:
            logger.info("✅ MQTT broker connection test successful")
            return True
        else:
            logger.error("❌ MQTT broker connection test failed")
            return False
            
    except Exception as e:
        logger.error(f"❌ MQTT connection test failed: {e}")
        return False


def setup_mqtt_broker():
    """Main function to set up MQTT broker."""
    logger.info("🚀 Starting MQTT broker setup for ConsultEase...")
    
    # Check if already running
    if check_mqtt_broker_running():
        logger.info("✅ MQTT broker is already running. Setup complete!")
        return True
    
    # Install Mosquitto
    if not install_mosquitto():
        return False
    
    # Configure Mosquitto
    if not configure_mosquitto():
        return False
    
    # Start service
    if not start_mosquitto_service():
        return False
    
    # Test connection
    if not test_mqtt_connection():
        logger.warning("⚠️ MQTT connection test failed, but broker may still be working")
    
    # Final check
    if check_mqtt_broker_running():
        logger.info("🎉 MQTT broker setup completed successfully!")
        logger.info("📡 MQTT broker is running on localhost:1883")
        logger.info("🔧 Configuration file: /etc/mosquitto/conf.d/consultease.conf")
        logger.info("📋 Service status: sudo systemctl status mosquitto")
        logger.info("📝 Logs: sudo journalctl -u mosquitto -f")
        return True
    else:
        logger.error("❌ MQTT broker setup failed")
        return False


if __name__ == "__main__":
    try:
        success = setup_mqtt_broker()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("Setup interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)
