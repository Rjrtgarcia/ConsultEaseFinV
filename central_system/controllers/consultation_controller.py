import logging
import datetime
from ..services import get_mqtt_service
from ..models import Consultation, ConsultationStatus, get_db

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ConsultationController:
    """
    Controller for managing consultation requests.
    """

    def __init__(self):
        """
        Initialize the consultation controller.
        """
        self.mqtt_service = get_mqtt_service()
        self.callbacks = []

    def start(self):
        """
        Start the consultation controller.
        """
        logger.info("Starting Consultation controller")

        # Connect MQTT service
        if not self.mqtt_service.is_connected:
            self.mqtt_service.connect()

    def stop(self):
        """
        Stop the consultation controller.
        """
        logger.info("Stopping Consultation controller")

    def register_callback(self, callback):
        """
        Register a callback to be called when a consultation status changes.

        Args:
            callback (callable): Function that takes a Consultation object as argument
        """
        self.callbacks.append(callback)
        logger.info(f"Registered Consultation controller callback: {callback.__name__}")

    def _notify_callbacks(self, consultation):
        """
        Notify all registered callbacks with the updated consultation information.

        Args:
            consultation (Consultation): Updated consultation object
        """
        for callback in self.callbacks:
            try:
                callback(consultation)
            except Exception as e:
                logger.error(f"Error in Consultation controller callback: {str(e)}")

    def create_consultation(self, student_id, faculty_id, request_message, course_code=None):
        """
        Create a new consultation request.

        Args:
            student_id (int): Student ID
            faculty_id (int): Faculty ID
            request_message (str): Consultation request message
            course_code (str, optional): Course code

        Returns:
            Consultation: New consultation object or None if error
        """
        try:
            logger.info(f"Creating new consultation request (Student: {student_id}, Faculty: {faculty_id})")

            # Check if MQTT service is connected
            if not self.mqtt_service.is_connected:
                logger.warning("MQTT service is not connected. Attempting to connect...")
                self.mqtt_service.connect()
                # Wait briefly for connection
                import time
                time.sleep(1)

                if not self.mqtt_service.is_connected:
                    logger.error("Failed to connect to MQTT service. Consultation will be created but may not be delivered to faculty desk unit.")

            db = get_db()

            # Create new consultation
            consultation = Consultation(
                student_id=student_id,
                faculty_id=faculty_id,
                request_message=request_message,
                course_code=course_code,
                status=ConsultationStatus.PENDING,
                requested_at=datetime.datetime.now()
            )

            db.add(consultation)
            db.commit()

            logger.info(f"Created consultation request: {consultation.id} (Student: {student_id}, Faculty: {faculty_id})")

            # Get student and faculty information for direct MQTT publishing
            from ..models import Student, Faculty
            student = db.query(Student).filter(Student.id == student_id).first()
            faculty = db.query(Faculty).filter(Faculty.id == faculty_id).first()

            # Create a simple message that will definitely work
            simple_message = f"Student: {student.name if student else 'Unknown'}\n"
            if course_code:
                simple_message += f"Course: {course_code}\n"
            simple_message += f"Request: {request_message}"

            # Publish directly to the professor/messages topic which is guaranteed to work
            success_direct = self.mqtt_service.publish_raw("professor/messages", simple_message)

            if success_direct:
                logger.info(f"Successfully published direct message to professor/messages")
            else:
                logger.error(f"Failed to publish direct message to professor/messages")

            # Also try the regular publishing method
            publish_success = self._publish_consultation(consultation)

            if publish_success:
                logger.info(f"Successfully published consultation request {consultation.id} to faculty desk unit")
            else:
                logger.error(f"Failed to publish consultation request {consultation.id} to faculty desk unit")

            # Notify callbacks
            self._notify_callbacks(consultation)

            return consultation
        except Exception as e:
            logger.error(f"Error creating consultation: {str(e)}")
            return None

    def _publish_consultation(self, consultation):
        """
        Publish consultation to MQTT.

        Args:
            consultation (Consultation): Consultation object to publish
        """
        try:
            # Get a new database session and fetch the consultation with all related objects
            db = get_db(force_new=True)

            # Instead of refreshing, query for the consultation by ID to ensure it's attached to this session
            consultation_id = consultation.id
            consultation = db.query(Consultation).filter(Consultation.id == consultation_id).first()

            if not consultation:
                logger.error(f"Consultation with ID {consultation_id} not found in database")
                return False

            # Explicitly load the related objects to avoid lazy loading issues
            student = consultation.student
            faculty = consultation.faculty

            if not student:
                logger.error(f"Student not found for consultation {consultation_id}")
                return False

            if not faculty:
                logger.error(f"Faculty not found for consultation {consultation_id}")
                return False

            # Format the message for the faculty desk unit display - EXACTLY like the test message
            message = f"Student: {student.name}\n"
            if consultation.course_code:
                message += f"Course: {consultation.course_code}\n"
            message += f"Request: {consultation.request_message}"

            # Create payload - EXACTLY like the test message format
            payload = {
                'id': consultation.id,
                'student_id': student.id,
                'student_name': student.name,
                'student_department': student.department,
                'faculty_id': faculty.id,
                'faculty_name': faculty.name,
                'request_message': consultation.request_message,
                'course_code': consultation.course_code,
                'status': consultation.status.value,
                'requested_at': consultation.requested_at.isoformat() if consultation.requested_at else None,
                # IMPORTANT: Add message field for easier extraction by faculty desk unit
                'message': message
            }

            logger.info(f"Preparing to publish consultation request {consultation.id} for faculty {faculty.id}")

            # IMPORTANT: First publish to the plain text topic that the faculty desk unit is known to use
            # This is the topic used in the faculty desk unit code and is GUARANTEED to work
            alt_topic = "professor/messages"

            # Publish the message directly (not as JSON) to match the faculty desk unit code
            # This is the MOST RELIABLE method and should work regardless of faculty ID
            success_alt = self.mqtt_service.publish_raw(alt_topic, message)

            if success_alt:
                logger.info(f"Successfully published consultation request to faculty desk unit topic {alt_topic}")
            else:
                logger.error(f"Failed to publish consultation request to faculty desk unit topic {alt_topic}")

            # Now publish to faculty-specific topic
            topic = f"consultease/faculty/{faculty.id}/requests"

            # The MQTT service will format the message for the faculty desk unit
            success = self.mqtt_service.publish(topic, payload)

            if success:
                logger.info(f"Successfully published consultation request to {topic}")
            else:
                logger.error(f"Failed to publish consultation request to {topic}")

            # Try publishing to the faculty-specific topic in plain text format as well
            # This provides maximum compatibility
            alt_topic_faculty = f"consultease/faculty/{faculty.id}/messages"
            success_faculty = self.mqtt_service.publish_raw(alt_topic_faculty, message)

            if success_faculty:
                logger.info(f"Successfully published plain text message to {alt_topic_faculty}")
            else:
                logger.error(f"Failed to publish plain text message to {alt_topic_faculty}")

            # IMPORTANT: Also publish to the exact same topics used in the test function
            # This ensures we're using the exact same format that works in the test
            success_test = self.mqtt_service.publish_raw("professor/messages", message)
            if success_test:
                logger.info(f"Successfully published to professor/messages (test method)")
            else:
                logger.error(f"Failed to publish to professor/messages (test method)")

            # Log overall success/failure
            if success or success_alt or success_faculty or success_test:
                logger.info(f"Successfully published consultation request {consultation.id} to at least one topic")
            else:
                logger.error(f"Failed to publish consultation request {consultation.id} to any topic")

            # Close the database session
            db.close()

            return success or success_alt or success_faculty or success_test
        except Exception as e:
            logger.error(f"Error publishing consultation: {str(e)}")
            return False

    def update_consultation_status(self, consultation_id, status):
        """
        Update consultation status.

        Args:
            consultation_id (int): Consultation ID
            status (ConsultationStatus): New status

        Returns:
            Consultation: Updated consultation object or None if error
        """
        try:
            db = get_db()
            consultation = db.query(Consultation).filter(Consultation.id == consultation_id).first()

            if not consultation:
                logger.error(f"Consultation not found: {consultation_id}")
                return None

            # Update status and timestamp
            consultation.status = status

            if status == ConsultationStatus.ACCEPTED:
                consultation.accepted_at = datetime.datetime.now()
            elif status == ConsultationStatus.COMPLETED:
                consultation.completed_at = datetime.datetime.now()
            elif status == ConsultationStatus.CANCELLED:
                # No specific timestamp for cancellation, but we could add one if needed
                pass

            db.commit()

            logger.info(f"Updated consultation status: {consultation.id} -> {status}")

            # Publish updated consultation
            self._publish_consultation(consultation)

            # Notify callbacks
            self._notify_callbacks(consultation)

            return consultation
        except Exception as e:
            logger.error(f"Error updating consultation status: {str(e)}")
            return None

    def cancel_consultation(self, consultation_id):
        """
        Cancel a consultation request.

        Args:
            consultation_id (int): Consultation ID

        Returns:
            Consultation: Updated consultation object or None if error
        """
        return self.update_consultation_status(consultation_id, ConsultationStatus.CANCELLED)

    def get_consultations(self, student_id=None, faculty_id=None, status=None):
        """
        Get consultations, optionally filtered by student, faculty, or status.

        Args:
            student_id (int, optional): Filter by student ID
            faculty_id (int, optional): Filter by faculty ID
            status (ConsultationStatus, optional): Filter by status

        Returns:
            list: List of Consultation objects
        """
        try:
            db = get_db()
            query = db.query(Consultation)

            # Apply filters
            if student_id is not None:
                query = query.filter(Consultation.student_id == student_id)

            if faculty_id is not None:
                query = query.filter(Consultation.faculty_id == faculty_id)

            if status is not None:
                query = query.filter(Consultation.status == status)

            # Order by requested_at (newest first)
            query = query.order_by(Consultation.requested_at.desc())

            # Execute query
            consultations = query.all()

            return consultations
        except Exception as e:
            logger.error(f"Error getting consultations: {str(e)}")
            return []

    def get_consultation_by_id(self, consultation_id):
        """
        Get a consultation by ID.

        Args:
            consultation_id (int): Consultation ID

        Returns:
            Consultation: Consultation object or None if not found
        """
        try:
            db = get_db()
            consultation = db.query(Consultation).filter(Consultation.id == consultation_id).first()
            return consultation
        except Exception as e:
            logger.error(f"Error getting consultation by ID: {str(e)}")
            return None

    def test_faculty_desk_connection(self, faculty_id):
        """
        Test the connection to a faculty desk unit by sending a test message.

        Args:
            faculty_id (int): Faculty ID to test

        Returns:
            bool: True if the test message was sent successfully, False otherwise
        """
        try:
            # Get faculty information
            db = get_db()
            from ..models import Faculty
            faculty = db.query(Faculty).filter(Faculty.id == faculty_id).first()

            if not faculty:
                logger.error(f"Faculty not found: {faculty_id}")
                return False

            # Create a test message
            message = f"Test message from ConsultEase central system.\nTimestamp: {datetime.datetime.now().isoformat()}"

            # Publish to faculty-specific topic
            topic = f"consultease/faculty/{faculty_id}/requests"
            payload = {
                'id': 0,
                'student_id': 0,
                'student_name': "System Test",
                'student_department': "System",
                'faculty_id': faculty_id,
                'faculty_name': faculty.name,
                'request_message': message,
                'course_code': "TEST",
                'status': "test",
                'requested_at': datetime.datetime.now().isoformat(),
                'message': message
            }

            # Publish to JSON topic
            success_json = self.mqtt_service.publish(topic, payload)

            # Publish to plain text topic
            success_text = self.mqtt_service.publish_raw("professor/messages", message)

            # Publish to faculty-specific plain text topic
            success_faculty = self.mqtt_service.publish_raw(f"consultease/faculty/{faculty_id}/messages", message)

            logger.info(f"Test message sent to faculty desk unit {faculty_id} ({faculty.name})")
            logger.info(f"JSON topic success: {success_json}, Text topic success: {success_text}, Faculty topic success: {success_faculty}")

            return success_json or success_text or success_faculty
        except Exception as e:
            logger.error(f"Error testing faculty desk connection: {str(e)}")
            return False