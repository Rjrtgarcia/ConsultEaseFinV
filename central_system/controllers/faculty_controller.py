import logging
import datetime
from sqlalchemy import or_
from ..services import get_mqtt_service
from ..models import Faculty, get_db
from ..utils.mqtt_topics import MQTTTopics

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FacultyController:
    """
    Controller for managing faculty data and status.
    """

    def __init__(self):
        """
        Initialize the faculty controller.
        """
        self.mqtt_service = get_mqtt_service()
        self.callbacks = []

    def start(self):
        """
        Start the faculty controller and subscribe to faculty status updates.
        """
        logger.info("Starting Faculty controller")

        # Subscribe to faculty status updates using standardized topic
        self.mqtt_service.register_topic_handler(
            "consultease/faculty/+/status",
            self.handle_faculty_status_update
        )

        # Subscribe to legacy faculty desk unit status updates for backward compatibility
        self.mqtt_service.register_topic_handler(
            MQTTTopics.LEGACY_FACULTY_STATUS,
            self.handle_faculty_status_update
        )

        # Connect MQTT service
        if not self.mqtt_service.is_connected:
            self.mqtt_service.connect()

    def stop(self):
        """
        Stop the faculty controller.
        """
        logger.info("Stopping Faculty controller")

    def register_callback(self, callback):
        """
        Register a callback to be called when faculty status changes.

        Args:
            callback (callable): Function that takes a Faculty object as argument
        """
        self.callbacks.append(callback)
        logger.info(f"Registered Faculty controller callback: {callback.__name__}")

    def _notify_callbacks(self, faculty):
        """
        Notify all registered callbacks with the updated faculty information.

        Args:
            faculty (Faculty): Updated faculty object
        """
        for callback in self.callbacks:
            try:
                callback(faculty)
            except Exception as e:
                logger.error(f"Error in Faculty controller callback: {str(e)}")

    def handle_faculty_status_update(self, topic, data):
        """
        Handle faculty status update from MQTT.

        Args:
            topic (str): MQTT topic
            data (dict or str): Status update data
        """
        faculty_id = None
        status = None
        faculty_name = None

        # Handle different topic formats
        if topic == MQTTTopics.LEGACY_FACULTY_STATUS:
            # This is from the faculty desk unit using the legacy topic
            # Check if this is a string message (keychain_connected or keychain_disconnected)
            if isinstance(data, str):
                if data == "keychain_connected":
                    status = True
                    # Extract faculty name from client ID (DeskUnit_FacultyName)
                    # This is more flexible than hardcoding a specific faculty name
                    db = get_db()

                    # Try to find the faculty from the MQTT client ID if available
                    # If not available, look for faculty with BLE beacons configured
                    faculty = None

                    # First, try to find any faculty with BLE configured and status=False
                    # This assumes the BLE connection is for a faculty that was previously disconnected
                    faculty = db.query(Faculty).filter(
                        Faculty.ble_id.isnot(None),
                        Faculty.status == False
                    ).first()

                    if faculty:
                        faculty_id = faculty.id
                        faculty_name = faculty.name
                        logger.info(f"BLE beacon connected for faculty desk unit (ID: {faculty_id}, Name: {faculty_name})")
                    else:
                        # If no disconnected faculty found, look for any faculty with BLE configured
                        faculty = db.query(Faculty).filter(
                            Faculty.ble_id.isnot(None)
                        ).first()

                        if faculty:
                            faculty_id = faculty.id
                            faculty_name = faculty.name
                            logger.info(f"BLE beacon connected for faculty desk unit (ID: {faculty_id}, Name: {faculty_name})")
                        else:
                            logger.error("No faculty with BLE configuration found in database")
                            return
                elif data == "keychain_disconnected":
                    status = False
                    # Similar approach as above for finding the faculty
                    db = get_db()

                    # First, try to find any faculty with BLE configured and status=True
                    # This assumes the BLE disconnection is for a faculty that was previously connected
                    faculty = db.query(Faculty).filter(
                        Faculty.ble_id.isnot(None),
                        Faculty.status == True
                    ).first()

                    if faculty:
                        faculty_id = faculty.id
                        faculty_name = faculty.name
                        logger.info(f"BLE beacon disconnected for faculty desk unit (ID: {faculty_id}, Name: {faculty_name})")
                    else:
                        # If no connected faculty found, look for any faculty with BLE configured
                        faculty = db.query(Faculty).filter(
                            Faculty.ble_id.isnot(None)
                        ).first()

                        if faculty:
                            faculty_id = faculty.id
                            faculty_name = faculty.name
                            logger.info(f"BLE beacon disconnected for faculty desk unit (ID: {faculty_id}, Name: {faculty_name})")
                        else:
                            logger.error("No faculty with BLE configuration found in database")
                            return
            else:
                # This is a JSON message
                status = data.get('status', False)
                faculty_id = data.get('faculty_id')
                faculty_name = data.get('faculty_name')

                if faculty_id is None and faculty_name is not None:
                    # Try to find faculty by name
                    db = get_db()
                    faculty = db.query(Faculty).filter(Faculty.name == faculty_name).first()
                    if faculty:
                        faculty_id = faculty.id
                    else:
                        logger.error(f"Faculty '{faculty_name}' not found in database")
                        return
                elif faculty_id is None:
                    # No faculty ID or name provided, try to find any faculty with BLE configured
                    db = get_db()
                    faculty = db.query(Faculty).filter(
                        Faculty.ble_id.isnot(None)
                    ).first()

                    if faculty:
                        faculty_id = faculty.id
                        faculty_name = faculty.name
                    else:
                        logger.error("No faculty with BLE configuration found in database")
                        return
        else:
            # Extract faculty ID from topic (e.g., "consultease/faculty/123/status")
            parts = topic.split('/')
            if len(parts) != 4:
                logger.error(f"Invalid topic format: {topic}")
                return

            try:
                faculty_id = int(parts[2])
            except ValueError:
                logger.error(f"Invalid faculty ID in topic: {parts[2]}")
                return

            # Get status from data
            if isinstance(data, dict):
                status = data.get('status', False)
                faculty_name = data.get('faculty_name')

                # Check if this is a BLE beacon status update
                if 'keychain_connected' in data:
                    status = True
                    logger.info(f"BLE beacon connected for faculty {faculty_id}")
                elif 'keychain_disconnected' in data:
                    status = False
                    logger.info(f"BLE beacon disconnected for faculty {faculty_id}")
            else:
                logger.error(f"Invalid data format for topic {topic}: {data}")
                return

        # If we couldn't determine faculty ID or status, return
        if faculty_id is None or status is None:
            logger.error(f"Could not determine faculty ID or status from topic {topic} and data {data}")
            return

        logger.info(f"Received status update for faculty {faculty_id}: {status}")

        # Update faculty status in database
        faculty = self.update_faculty_status(faculty_id, status)

        if faculty:
            # Notify callbacks
            self._notify_callbacks(faculty)

            # Publish a notification about faculty availability using standardized topic
            try:
                notification = {
                    'type': 'faculty_status',
                    'faculty_id': faculty.id,
                    'faculty_name': faculty.name,
                    'status': status,
                    'timestamp': faculty.last_seen.isoformat() if faculty.last_seen else None
                }
                self.mqtt_service.publish(MQTTTopics.SYSTEM_NOTIFICATIONS, notification)
            except Exception as e:
                logger.error(f"Error publishing faculty status notification: {str(e)}")

    def update_faculty_status(self, faculty_id, status):
        """
        Update faculty status in the database.

        Args:
            faculty_id (int): Faculty ID
            status (bool): New status (True = Available, False = Unavailable)

        Returns:
            Faculty: Updated faculty object or None if not found
        """
        try:
            db = get_db()
            faculty = db.query(Faculty).filter(Faculty.id == faculty_id).first()

            if not faculty:
                logger.error(f"Faculty not found: {faculty_id}")
                return None

            # Always update status based on BLE connection
            # The always_available flag is no longer used

            # Otherwise, update status normally
            faculty.status = status
            faculty.last_seen = datetime.datetime.now()

            db.commit()

            logger.info(f"Updated status for faculty {faculty.name} (ID: {faculty.id}): {status}")

            return faculty
        except Exception as e:
            logger.error(f"Error updating faculty status: {str(e)}")
            return None

    def get_all_faculty(self, filter_available=None, search_term=None):
        """
        Get all faculty, optionally filtered by availability or search term.

        Args:
            filter_available (bool, optional): Filter by availability status
            search_term (str, optional): Search term for name or department

        Returns:
            list: List of Faculty objects
        """
        try:
            db = get_db()
            query = db.query(Faculty)

            # Apply filters
            if filter_available is not None:
                query = query.filter(Faculty.status == filter_available)

            if search_term:
                search_term = f"%{search_term}%"
                query = query.filter(
                    or_(
                        Faculty.name.ilike(search_term),
                        Faculty.department.ilike(search_term)
                    )
                )

            # Execute query
            faculties = query.all()

            return faculties
        except Exception as e:
            logger.error(f"Error getting faculty list: {str(e)}")
            return []

    def get_faculty_by_id(self, faculty_id):
        """
        Get a faculty member by ID.

        Args:
            faculty_id (int): Faculty ID

        Returns:
            Faculty: Faculty object or None if not found
        """
        try:
            db = get_db()
            faculty = db.query(Faculty).filter(Faculty.id == faculty_id).first()
            return faculty
        except Exception as e:
            logger.error(f"Error getting faculty by ID: {str(e)}")
            return None

    def get_faculty_by_ble_id(self, ble_id):
        """
        Get a faculty member by BLE ID.

        Args:
            ble_id (str): BLE beacon ID

        Returns:
            Faculty: Faculty object or None if not found
        """
        try:
            db = get_db()
            faculty = db.query(Faculty).filter(Faculty.ble_id == ble_id).first()

            if faculty:
                logger.info(f"Found faculty with BLE ID {ble_id}: {faculty.name} (ID: {faculty.id})")
            else:
                logger.warning(f"No faculty found with BLE ID: {ble_id}")

            return faculty
        except Exception as e:
            logger.error(f"Error getting faculty by BLE ID: {str(e)}")
            return None

    def add_faculty(self, name, department, email, ble_id, image_path=None, always_available=False):
        """
        Add a new faculty member.

        Args:
            name (str): Faculty name
            department (str): Faculty department
            email (str): Faculty email
            ble_id (str): Faculty BLE beacon ID
            image_path (str, optional): Path to faculty image
            always_available (bool, optional): Deprecated parameter, no longer used

        Returns:
            Faculty: New faculty object or None if error
        """
        try:
            db = get_db()

            # Check if email or BLE ID already exists
            existing = db.query(Faculty).filter(
                or_(
                    Faculty.email == email,
                    Faculty.ble_id == ble_id
                )
            ).first()

            if existing:
                logger.error(f"Faculty with email {email} or BLE ID {ble_id} already exists")
                return None

            # Create new faculty
            faculty = Faculty(
                name=name,
                department=department,
                email=email,
                ble_id=ble_id,
                image_path=image_path,
                status=False,  # Initial status is False, will be updated by BLE
                always_available=False  # Always set to False
            )

            db.add(faculty)
            db.commit()

            logger.info(f"Added new faculty: {faculty.name} (ID: {faculty.id})")

            # Publish a notification about the new faculty
            logger.info(f"Faculty {faculty.name} (ID: {faculty.id}) created with BLE-based availability")
            try:
                notification = {
                    'type': 'faculty_status',
                    'faculty_id': faculty.id,
                    'faculty_name': faculty.name,
                    'status': faculty.status,
                    'timestamp': faculty.last_seen.isoformat() if faculty.last_seen else None
                }
                self.mqtt_service.publish(MQTTTopics.SYSTEM_NOTIFICATIONS, notification)
            except Exception as e:
                logger.error(f"Error publishing faculty status notification: {str(e)}")

            return faculty
        except Exception as e:
            logger.error(f"Error adding faculty: {str(e)}")
            return None

    def update_faculty(self, faculty_id, name=None, department=None, email=None, ble_id=None, image_path=None, always_available=None):
        """
        Update an existing faculty member.

        Args:
            faculty_id (int): Faculty ID
            name (str, optional): New faculty name
            department (str, optional): New faculty department
            email (str, optional): New faculty email
            ble_id (str, optional): New faculty BLE beacon ID
            image_path (str, optional): New faculty image path
            always_available (bool, optional): Deprecated parameter, no longer used

        Returns:
            Faculty: Updated faculty object or None if error
        """
        try:
            db = get_db()
            faculty = db.query(Faculty).filter(Faculty.id == faculty_id).first()

            if not faculty:
                logger.error(f"Faculty not found: {faculty_id}")
                return None

            # Update fields if provided
            if name is not None:
                faculty.name = name

            if department is not None:
                faculty.department = department

            if email is not None and email != faculty.email:
                # Check if email already exists
                existing = db.query(Faculty).filter(Faculty.email == email).first()
                if existing and existing.id != faculty_id:
                    logger.error(f"Faculty with email {email} already exists")
                    return None
                faculty.email = email

            if ble_id is not None and ble_id != faculty.ble_id:
                # Check if BLE ID already exists
                existing = db.query(Faculty).filter(Faculty.ble_id == ble_id).first()
                if existing and existing.id != faculty_id:
                    logger.error(f"Faculty with BLE ID {ble_id} already exists")
                    return None
                faculty.ble_id = ble_id

            if image_path is not None:
                faculty.image_path = image_path

            # Set always_available to False regardless of input
            # Status is always determined by BLE connection
            if faculty.always_available:
                faculty.always_available = False
                logger.info(f"Faculty {faculty.name} (ID: {faculty.id}) status will be determined by BLE connection")

            db.commit()

            logger.info(f"Updated faculty: {faculty.name} (ID: {faculty.id})")

            return faculty
        except Exception as e:
            logger.error(f"Error updating faculty: {str(e)}")
            return None

    def delete_faculty(self, faculty_id):
        """
        Delete a faculty member.

        Args:
            faculty_id (int): Faculty ID

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            db = get_db()
            faculty = db.query(Faculty).filter(Faculty.id == faculty_id).first()

            if not faculty:
                logger.error(f"Faculty not found: {faculty_id}")
                return False

            db.delete(faculty)
            db.commit()

            logger.info(f"Deleted faculty: {faculty.name} (ID: {faculty.id})")

            return True
        except Exception as e:
            logger.error(f"Error deleting faculty: {str(e)}")
            return False

    def ensure_available_faculty(self):
        """
        Ensure at least one faculty member is available for testing.
        If no faculty is available, make Dr. John Smith available.

        Returns:
            Faculty: The available faculty member or None if error
        """
        try:
            db = get_db()

            # Check if any faculty is available
            available_faculty = db.query(Faculty).filter(Faculty.status == True).first()

            if available_faculty:
                logger.info(f"Found available faculty: {available_faculty.name} (ID: {available_faculty.id})")
                return available_faculty

            # If no faculty is available, make Dr. John Smith available
            dr_john = db.query(Faculty).filter(Faculty.name == "Dr. John Smith").first()

            if dr_john:
                logger.info(f"Making Dr. John Smith (ID: {dr_john.id}) available for testing")
                dr_john.status = True
                db.commit()
                return dr_john

            # If Dr. John Smith doesn't exist, make the first faculty available
            first_faculty = db.query(Faculty).first()

            if first_faculty:
                logger.info(f"Making {first_faculty.name} (ID: {first_faculty.id}) available for testing")
                first_faculty.status = True
                db.commit()
                return first_faculty

            logger.warning("No faculty found in the database")
            return None
        except Exception as e:
            logger.error(f"Error ensuring available faculty: {str(e)}")
            return None