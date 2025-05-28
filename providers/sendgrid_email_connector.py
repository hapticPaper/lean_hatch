"""
SendGrid Email Connector

Simplified connector that uses the application's message handling pattern
from api_message_handler.py for consistent email processing.

Uses email-client-compatible templates to ensure emails render properly
across all email clients.
"""

import sys
from pathlib import Path
import os
import dotenv
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Content

# Add parent directory to path for imports
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent))

from utils import logger
from data_model.api_message_handler import APIMessageHandler
from data_model.application_model import EmailMessage

logger_instance = logger


class SendGridEmailConnector:
    """Simplified SendGrid connector using application message handling patterns."""
    
    def __init__(self):
        """Initialize the SendGrid API client."""
        self.api_key = os.getenv('SENDGRID_TOKEN')
        if not self.api_key:
            logger_instance.error("SENDGRID_TOKEN environment variable is not set.")
            raise ValueError("SENDGRID_TOKEN is required for SendGridEmailConnector")
        self.sgc = SendGridAPIClient(self.api_key)
        self.message_handler = APIMessageHandler()

    def send_email(self, from_email: str, to_email: str, subject: str, 
                   content: str | None = None, html_content: str | None = None, 
                   save_to_db: bool = True) -> tuple[EmailMessage, dict]:
        """
        Send an email using the SendGrid API with application message handling.
        
        Args:
            from_email (str): Sender's email address
            to_email (str): Recipient's email address  
            subject (str): Email subject
            content (str, optional): Plain text content
            html_content (str, optional): HTML content
            save_to_db (bool): Whether to save message to database
        
        Returns:
            tuple[EmailMessage, dict]: Application model and response data
        """
        try:
            # Create SendGrid mail object
            mail = Mail(
                from_email=from_email,
                to_emails=to_email,
                subject=subject
            )
            
            # Add content using Content objects (prefer HTML if available)
            if html_content:
                mail.content = Content("text/html", html_content)
            elif content:
                mail.content = Content("text/plain", content)
            else:
                mail.content = Content("text/plain", "No content provided")
                
            # Send email via SendGrid
            response = self.sgc.send(mail)
            
            # Prepare data for application message handler
            response_data = {
                'from_email': from_email,
                'to_email': to_email,
                'subject': subject,
                'content': content or '',
                'html_content': html_content,
                'status_code': response.status_code
            }
            
            headers_data = dict(response.headers) if response.headers else {}
            
            # Process through application message handler
            email_msg, db_email = APIMessageHandler.process_sendgrid_response(
                response_data, headers_data, save_to_db=save_to_db
            )
            
            logger_instance.info(
                f"Email sent successfully to {to_email} with subject '{subject}'",
                response_code=response.status_code,
                message_id=headers_data.get('X-Message-Id'),
                email_id=str(email_msg.id)
            )
            
            return email_msg, {
                'status_code': response.status_code,
                'headers': headers_data,
                'message_id': headers_data.get('X-Message-Id')
            }
            
        except Exception as e:
            logger_instance.error(f"Failed to send email: {str(e)}")
            
            # Create failed response data  
            response_data = {
                'from_email': from_email,
                'to_email': to_email,
                'subject': subject,
                'content': content or '',
                'html_content': html_content,
                'status_code': 500
            }
            
            headers_data = {'error': str(e)}
            
            # Process failed response through handler
            email_msg, db_email = APIMessageHandler.process_sendgrid_response(
                response_data, headers_data, save_to_db=save_to_db
            )
            
            return email_msg, {
                'status_code': 500,
                'error': str(e)
            }

    def send_html_template(self, from_email: str, to_email: str, subject: str, 
                          template_path: str, save_to_db: bool = True) -> tuple[EmailMessage, dict]:
        """
        Send email using an HTML template file.
        
        Args:
            from_email (str): Sender's email address
            to_email (str): Recipient's email address
            subject (str): Email subject  
            template_path (str): Path to HTML template file
            save_to_db (bool): Whether to save message to database
            
        Returns:
            tuple[EmailMessage, dict]: Application model and response data
        """
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
                
            return self.send_email(
                from_email=from_email,
                to_email=to_email, 
                subject=subject,
                html_content=html_content,
                save_to_db=save_to_db
            )
            
        except FileNotFoundError:
            logger_instance.error(f"Template file not found: {template_path}")
            raise
        except Exception as e:
            logger_instance.error(f"Failed to send template email: {str(e)}")
            raise

    def close_connection(self):
        """Close database connections."""
        if hasattr(self, 'message_handler'):
            self.message_handler.close_connection()


if __name__ == "__main__":
    dotenv.load_dotenv()  # Load environment variables from .env file
    dotenv.load_dotenv(os.path.join('.secrets', '.secrets'))

    connector = SendGridEmailConnector()
    logger_instance.info("SendGridEmailConnector initialized successfully.")

    # Test with email-compatible template
    try:
        email_msg, response_data = connector.send_html_template(
            from_email="ian@hapticpaper.com",
            to_email="jim@polarcoordinates.org",
            subject="buy me a pizza 🍕, lfgooooo",
            template_path="tests/html_email_compatible.html"
        )
        
        logger_instance.info(
            f"Test email sent successfully. Email ID: {email_msg.id}, Status: {email_msg.status}"
        )
        
    except Exception as e:
        logger_instance.error(f"Test email failed: {str(e)}")
    finally:
        connector.close_connection()