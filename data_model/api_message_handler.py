from pydantic import BaseModel
from uuid import uuid4
from datetime import datetime
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils import logger
from data_model.application_model import (
    twilioSMS, twilioResponseHeader, twilioSMSResponse,
    MessageType, hatchMessage, SMSMessage, EmailMessage, apiMessage, MessageStatus, MessageDirection
)
from data_model.database_model import (
    Message, dbEmail
)
from data_model.application_model import generate_conversation_id

logger_instance = logger





class createTwilioSMS(BaseModel):
    @staticmethod
    def to_json_dict(data: twilioSMS) -> dict:
        """Converts a twilioSMS model to a dictionary."""
        return {
                'To': data.to,
                'From': data.from_,
                'Body': data.body
        }
    
    @staticmethod
    def twilioRequest(data: twilioSMS) -> dict:
        """Creates a twilioSMS model from a dictionary."""
        return createTwilioSMS.to_json_dict(data)


class twilioHeaderHandler(BaseModel):
    """Handler for Twilio API response headers - reusable across all Twilio API endpoints."""
    
    @staticmethod
    def from_headers_dict(headers_dict: dict) -> twilioResponseHeader:
        """Converts response headers dictionary to twilioResponseHeader model."""
        # Map header keys to model fields (handle case variations and formatting)
        # Parse date field which can be in HTTP date format (e.g., 'Mon, 26 May 2025 19:22:31 GMT')
        date_value = headers_dict.get('date', headers_dict.get('Date'))
        if date_value:
            try:
                # Try parsing HTTP date format first
                from email.utils import parsedate_to_datetime
                parsed_date = parsedate_to_datetime(date_value)
            except (ValueError, TypeError):
                try:
                    # Fallback to ISO format
                    parsed_date = datetime.fromisoformat(date_value)
                except (ValueError, TypeError):
                    # Last resort - use current time
                    parsed_date = datetime.now()
        else:
            parsed_date = datetime.now()
        
        return twilioResponseHeader(
            content_type=headers_dict.get('content-type', headers_dict.get('Content-Type', '')),
            content_length=int(headers_dict.get('content-length', headers_dict.get('Content-Length', 0))),
            connection=headers_dict.get('connection', headers_dict.get('Connection', '')),
            date=parsed_date,
            twilio_concurrent_requests=int(headers_dict.get('twilio-concurrent-requests', headers_dict.get('Twilio-Concurrent-Requests', 0))),
            twilio_request_id=headers_dict.get('twilio-request-id', headers_dict.get('Twilio-Request-Id', '')),
            twilio_request_duration=float(headers_dict.get('twilio-request-duration', headers_dict.get('Twilio-Request-Duration', 0.0))),
            x_home_region=headers_dict.get('x-home-region', headers_dict.get('X-Home-Region', '')),
            x_api_domain=headers_dict.get('x-api-domain', headers_dict.get('X-Api-Domain', '')),
            strict_transport_security=headers_dict.get('strict-transport-security', headers_dict.get('Strict-Transport-Security', '')),
            x_cache=headers_dict.get('x-cache', headers_dict.get('X-Cache', '')),
            via=headers_dict.get('via', headers_dict.get('Via', '')),
            x_amz_cf_pop=headers_dict.get('x-amz-cf-pop', headers_dict.get('X-Amz-Cf-Pop', '')),
            x_amz_cf_id=headers_dict.get('x-amz-cf-id', headers_dict.get('X-Amz-Cf-Id', '')),
            x_powered_by=headers_dict.get('x-powered-by', headers_dict.get('X-Powered-By', '')),
            x_shenanigans=headers_dict.get('x-shenanigans', headers_dict.get('X-Shenanigans')),
            vary=headers_dict.get('vary', headers_dict.get('Vary'))
        )


class twilioSMSResponseHandler(BaseModel):
    """Handler specifically for Twilio SMS API responses."""
    
    @staticmethod
    def from_response_dict(response_dict: dict) -> twilioSMSResponse:
        """Converts SMS response dictionary to twilioSMSResponse model."""
        # Parse datetime fields properly with multiple format support
        def parse_datetime_field(date_value):
            """Parse datetime from various formats including HTTP date format."""
            if not date_value or not isinstance(date_value, str):
                return None
            
            try:
                # Try parsing HTTP date format first (e.g., 'Mon, 26 May 2025 19:22:31 GMT')
                from email.utils import parsedate_to_datetime
                return parsedate_to_datetime(date_value)
            except (ValueError, TypeError):
                try:
                    # Fallback to ISO format with Z replacement
                    return datetime.fromisoformat(date_value.replace('Z', '+00:00'))
                except (ValueError, TypeError):
                    try:
                        # Try direct ISO format
                        return datetime.fromisoformat(date_value)
                    except (ValueError, TypeError):
                        # Last resort - return None for optional fields
                        return None
        
        date_created = parse_datetime_field(response_dict.get('date_created'))
        date_sent = parse_datetime_field(response_dict.get('date_sent'))
        date_updated = parse_datetime_field(response_dict.get('date_updated'))
        
        # Handle price conversion safely
        price_value = response_dict.get('price')
        price = float(price_value) if price_value is not None else None
        
        return twilioSMSResponse(
            account_sid=response_dict.get('account_sid', ''),
            api_version=response_dict.get('api_version', ''),
            body=response_dict.get('body', ''),
            date_created=date_created or datetime.now(),
            date_sent=date_sent,
            date_updated=date_updated or datetime.now(),
            direction=response_dict.get('direction', ''),
            error_code=response_dict.get('error_code'),
            error_message=response_dict.get('error_message'),
            **{'from': response_dict.get('from', '')},  # Use alias for 'from' field
            messaging_service_sid=response_dict.get('messaging_service_sid'),
            num_media=int(response_dict.get('num_media', 0)),
            num_segments=int(response_dict.get('num_segments', 1)),
            price=price,
            price_unit=response_dict.get('price_unit', 'USD'),
            sid=response_dict.get('sid', ''),
            status=response_dict.get('status', ''),
            subresource_uris=response_dict.get('subresource_uris', {}),
            to=response_dict.get('to', ''),
            uri=response_dict.get('uri', '')
        )
    
    @classmethod
    def process_sms_response(cls, response_json: dict, headers_dict: dict) -> tuple[twilioSMSResponse, twilioResponseHeader]:
        """Complete pipeline: JSON SMS response + headers -> Pydantic models."""
        sms_response = cls.from_response_dict(response_json)
        response_headers = twilioHeaderHandler.from_headers_dict(headers_dict)
        
        return sms_response, response_headers


class sendgridEmailResponseHandler(BaseModel):
    """Handler specifically for SendGrid Email API responses."""
    
    @staticmethod
    def from_response_dict(response_dict: dict, headers_dict: dict) -> 'EmailMessage':
        """Converts SendGrid response to EmailMessage model."""
        from data_model.application_model import generate_conversation_id
        
        # Parse datetime fields properly
        def parse_datetime_field(date_value):
            """Parse datetime from various formats including HTTP date format."""
            if not date_value or not isinstance(date_value, str):
                return datetime.now()
            
            try:
                # Try parsing HTTP date format first
                from email.utils import parsedate_to_datetime
                return parsedate_to_datetime(date_value)
            except (ValueError, TypeError):
                try:
                    # Try ISO format
                    return datetime.fromisoformat(date_value)
                except (ValueError, TypeError):
                    return datetime.now()
        
        # Extract essential fields from response
        status_code = response_dict.get('status_code', 202)
        message_id = headers_dict.get('X-Message-Id', headers_dict.get('x-message-id'))
        date_sent = parse_datetime_field(headers_dict.get('Date', headers_dict.get('date')))
        
        # Create conversation ID from from/to emails
        from_email = response_dict.get('from_email', '')
        to_email = response_dict.get('to_email', '')
        conversation_id = generate_conversation_id(to_email, from_email)
        
        return EmailMessage(
            id=uuid4(),
            to_contact=to_email,
            from_contact=from_email,
            body=response_dict.get('content', ''),
            type=MessageType.EMAIL,
            timestamp=date_sent,
            status=MessageStatus.SENT.value if status_code == 202 else MessageStatus.FAILED.value,
            direction=MessageDirection.OUTBOUND_API.value,
            conversation_id=conversation_id,
            subject=response_dict.get('subject', ''),
            html_content=response_dict.get('html_content'),
            external_sid=message_id,
            provider_response={
                'status_code': status_code,
                'headers': headers_dict,
                'message_id': message_id
            }
        )


class createSendGridEmail(BaseModel):
    """Helper for creating SendGrid email requests."""
    
    @staticmethod
    def to_sendgrid_format(from_email: str, to_email: str, subject: str, 
                          content: str | None = None, html_content: str | None = None) -> dict:
        """Creates SendGrid-compatible email data."""
        return {
            'from_email': from_email,
            'to_email': to_email,
            'subject': subject,
            'content': content,
            'html_content': html_content,
            'timestamp': datetime.now()
        }


class APIMessageHandler:
    """Handler for API messages, responsible for converting and saving messages."""
    
    def __init__(self):
        # Initialize database connection
        from db.postgres_connector import hatchPostgres
        self.pg = hatchPostgres()
        self.session = self.pg.connect()
        
        if self.session is None:
            raise Exception("Failed to establish database connection in APIMessageHandler")
       
    
    @staticmethod
    def from_json_dict(data: dict) -> apiMessage:
        """Converts JSON dictionary to apiMessage model."""
        # Map the JSON format to apiMessage format
        api_data = {
            'id': uuid4(),
            'to': data.get('to'),
            'from': data.get('from_'),  # Note: using 'from' as the field name
            'body': data.get('message'),
            'status': data.get('status', MessageStatus.RECEIVED.value),  # Default to RECEIVED if not provided
            'type': MessageType.SMS, 
            'direction': data.get('direction'),  # Default to INBOUND_API
            'timestamp': datetime.now()
        }
        
        return apiMessage(**api_data)
    
    @staticmethod
    def to_application_model(api_msg: apiMessage, message_type: MessageType = MessageType.SMS) -> hatchMessage:
        """Converts apiMessage to application model (hatchMessage or subclass)."""
        
        # Generate conversation_id explicitly
        conversation_id = generate_conversation_id(api_msg.to, api_msg.from_)
        
        if message_type == MessageType.SMS:
            return SMSMessage(
                id=uuid4(),
                to_contact=api_msg.to,
                from_contact=api_msg.from_,
                body=api_msg.body,
                type=api_msg.type,
                timestamp=api_msg.timestamp,
                status=api_msg.status or MessageStatus.RECEIVED.value,
                direction=api_msg.direction,
                conversation_id=conversation_id
            )
        elif message_type == MessageType.EMAIL:
            return EmailMessage(
                id=api_msg.id,
                to_contact=api_msg.to,
                from_contact=api_msg.from_,
                body=api_msg.body,
                subject=getattr(api_msg, 'subject', 'No Subject'),  # Add default subject
                type=api_msg.type,
                timestamp=api_msg.timestamp,
                status=api_msg.status or MessageStatus.RECEIVED.value,
                direction=api_msg.direction,
                conversation_id=conversation_id
            )
        else:
            return hatchMessage(
                id=api_msg.id,
                to_contact=api_msg.to,
                from_contact=api_msg.from_,
                body=api_msg.body,
                type=api_msg.type,
                timestamp=api_msg.timestamp,
                status = api_msg.status or MessageStatus.RECEIVED.value,
                direction=api_msg.direction,
                conversation_id=conversation_id
            )
    
    @staticmethod
    def twilio_to_application_model(twilio_response: 'twilioSMSResponse') -> hatchMessage:
        """Converts Twilio SMS response to application model with all Twilio fields."""
        from data_model.application_model import generate_conversation_id
        
        # Generate conversation_id explicitly
        conversation_id = generate_conversation_id(twilio_response.to, twilio_response.from_)
        
        return hatchMessage(
            id=uuid4(),
            to_contact=twilio_response.to,
            from_contact=twilio_response.from_,
            body=twilio_response.body,
            type=MessageType.SMS,
            timestamp=twilio_response.date_created,
            status=twilio_response.status,
            conversation_id=conversation_id,
            external_sid=twilio_response.sid,
            direction=twilio_response.direction,
            error_code=twilio_response.error_code,
            error_message=twilio_response.error_message,
            num_media=twilio_response.num_media,
            num_segments=twilio_response.num_segments,
            price=twilio_response.price,
            price_unit=twilio_response.price_unit,
            date_sent=twilio_response.date_sent,
            date_updated=twilio_response.date_updated
        )

    def save_message(self, message: hatchMessage, auto_commit: bool = True) -> Message:
        """Converts application model to database model and saves to PostgreSQL."""
        db_message = Message(
            id=message.id,
            to_contact=message.to_contact,
            from_contact=message.from_contact,
            body=message.body,
            type=message.type.value,
            timestamp=message.timestamp,
            status=message.status,
            conversation_id=message.conversation_id,
            external_sid=message.external_sid,
            direction=message.direction,
            error_code=message.error_code,
            error_message=message.error_message,
            num_media=message.num_media,
            num_segments=message.num_segments,
            price=message.price,
            price_unit=message.price_unit,
            date_sent=message.date_sent,
            date_updated=message.date_updated
        )
        
        # Save to database if session is available
        if self.session is not None:
            try:
                self.session.add(db_message)
                if auto_commit:
                    self.session.commit()
                    logger_instance.info("Message saved to database successfully", 
                          message_id=str(db_message.id),
                          conversation_id=str(db_message.conversation_id),
                          to=db_message.to_contact,
                          from_=db_message.from_contact)
            except Exception as e:
                self.session.rollback()
                logger_instance.error("Failed to save message to database", 
                       error=str(e),
                       message_id=str(db_message.id))
                raise
        else:
            logger_instance.warning("No database session available - message not saved to database")
        
        return db_message
    
    def save_email(self, email: EmailMessage, auto_commit: bool = True) -> dbEmail:
        """Converts EmailMessage application model to Email database model and saves to PostgreSQL."""
        import json
        
        db_email = dbEmail(
            id=email.id,
            to_contact=email.to_contact,
            from_contact=email.from_contact,
            subject=email.subject,
            body=email.body,
            html_content=email.html_content,
            type=email.type.value,
            timestamp=email.timestamp,
            status=email.status,
            conversation_id=email.conversation_id,
            direction=email.direction,
            cc=json.dumps(email.cc) if email.cc else None,
            bcc=json.dumps(email.bcc) if email.bcc else None,
            reply_to=email.reply_to,
            attachments=json.dumps(email.attachments) if email.attachments else None,
            external_message_id=email.external_sid,
            provider='sendgrid',
            provider_response=json.dumps(email.provider_response) if email.provider_response else None,
            date_sent=email.date_sent,
            date_updated=email.date_updated,
            error_code=email.error_code,
            error_message=email.error_message
        )
        
        # Save to database if session is available
        if self.session is not None:
            try:
                self.session.add(db_email)
                if auto_commit:
                    self.session.commit()
                    logger_instance.info("Email saved to database successfully", 
                          email_id=str(db_email.id),
                          conversation_id=str(db_email.conversation_id),
                          to=db_email.to_contact,
                          from_=db_email.from_contact,
                          subject=db_email.subject)
            except Exception as e:
                self.session.rollback()
                logger_instance.error("Failed to save email to database", 
                       error=str(e),
                       email_id=str(db_email.id))
                raise
        else:
            logger_instance.warning("No database session available - email not saved to database")
        
        return db_email
    
    @classmethod
    def process_json_message(cls, json_data: dict, save_to_db: bool = True) -> tuple[apiMessage, hatchMessage, Message]:
        """Complete pipeline: JSON -> API model -> Application model -> Database model (with automatic save)."""
        # Step 1: Convert JSON to API message
        api_msg = cls.from_json_dict(json_data)
        
        # Step 2: Convert API message to application model
        app_msg = cls.to_application_model(api_msg)
        
        # Step 3: Convert to database model and optionally save
        handler = cls()
        db_msg = handler.save_message(app_msg, auto_commit=save_to_db)
        
        return api_msg, app_msg, db_msg
    
    @classmethod
    def process_twilio_response(cls, twilio_response: 'twilioSMSResponse', save_to_db: bool = True) -> tuple[hatchMessage, Message]:
        """Complete pipeline: Twilio response -> Application model -> Database model (with automatic save)."""
        # Step 1: Convert Twilio response to application model
        app_data = cls.twilio_to_application_model(twilio_response)
        
        # Step 2: Convert to database model and optionally save
        handler = cls()
        db_msg = handler.save_message(app_data, auto_commit=save_to_db)
        
        return app_data, db_msg
    
    @classmethod
    def process_sendgrid_response(cls, response_dict: dict, headers_dict: dict, save_to_db: bool = True) -> tuple[EmailMessage, dbEmail]:
        """Complete pipeline: SendGrid response -> Application model -> Database model (with automatic save)."""
        # Step 1: Convert SendGrid response to EmailMessage application model
        email_msg = sendgridEmailResponseHandler.from_response_dict(response_dict, headers_dict)
        
        # Step 2: Convert to database model and optionally save to Email table
        handler = cls()
        db_email = handler.save_email(email_msg, auto_commit=save_to_db)
        
        return email_msg, db_email
    
    @classmethod
    def send_email_via_sendgrid(cls, to_email: str, subject: str, body: str, 
                               from_email: str = "ian@hapticpaper.com", 
                               save_to_db: bool = True) -> tuple[EmailMessage, dict]:
        """
        Send email via SendGrid using the application's message handling pattern.
        
        Args:
            to_email (str): Recipient's email address
            subject (str): Email subject
            body (str): Email body content
            from_email (str): Sender's email address (default configured)
            save_to_db (bool): Whether to save to database
            
        Returns:
            tuple[EmailMessage, dict]: Application model and response data
        """
        try:
            from providers.sendgrid_email_connector import SendGridEmailConnector
            
            # Initialize SendGrid connector
            connector = SendGridEmailConnector()
            
            # Send email through connector
            email_msg, response_data = connector.send_email(
                from_email=from_email,
                to_email=to_email,
                subject=subject,
                content=body,
                save_to_db=save_to_db
            )
            
            # Close connector connection
            connector.close_connection()
            
            logger_instance.info(
                "Email sent successfully via SendGrid",
                to=to_email,
                subject=subject,
                email_id=str(email_msg.id),
                status=email_msg.status
            )
            
            return email_msg, response_data
            
        except Exception as e:
            logger_instance.error(f"Failed to send email via SendGrid: {str(e)}")
            raise
    
    def close_connection(self):
        """Close the database session."""
        if self.session:
            self.session.close()
            logger_instance.info("Database session closed")

    def __dict__(self):
        return {
            "api_message": self.from_json_dict,
            "application_message": self.to_application_model,
            "database_message": self.save_message
        }

