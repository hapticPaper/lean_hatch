import requests

from utils import logger
from data_model import hatchMessage, twilioSMS, createTwilioSMS, twilioHeaderHandler, twilioSMSResponse, twilioResponseHeader, twilioSMSResponseHandler, APIMessageHandler
import os
import sys
import dotenv
from pathlib import Path
import time

l = logger
# Add parent directory to path for VS Code debugging
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent))


dotenv.load_dotenv()  # Load environment variables from .env file
dotenv.load_dotenv(os.path.join('.secrets', '.secrets'))

# Environment variables will be read by get_twilio_client() or are used directly
DEFAULT_TWILIO_NUMBER = os.getenv('TWILIO_NUMBER')
TEST_DESTINATION_NUMBER = os.getenv('TEST_NUMBER', DEFAULT_TWILIO_NUMBER)  
TWILIO_SID = os.getenv('TWILIO_SID')
TWILIO_SECRET = os.getenv('TWILIO_SECRET')

TWILIO_URL = "https://api.twilio.com/2010-04-01"



class twilioAPI():
    def __init__(self):
        """Initialize the Twilio API client."""
        self.client = None
        self.session = requests.Session()
    
    def get_client(self):
        """Get the Twilio API client."""
        self.session.auth=(TWILIO_SID, TWILIO_SECRET)
        return self.session
    
    def exponential_backoff(self, retries: int = 5, base_delay: float = 1.0):
        """
        Exponential backoff strategy for retrying requests.
        
        Args:
            retries (int): Number of retries before giving up.
            base_delay (float): Base delay in seconds for the first retry.
        
        Returns:
            None
        """
        global backoff_counter
        
        delay = base_delay * (2 ** retries)
        l.info(f"Waiting {delay} seconds...")
        time.sleep(delay)

    def send_sms(self, msg:twilioSMS) -> tuple[hatchMessage, twilioResponseHeader]:
        """
        Send an SMS message using the Twilio API.
        
        Args:
            to (str): The recipient's phone number.
            body (str): The message body.
            from_number (str): The sender's phone number. Defaults to DEFAULT_TWILIO_NUMBER.
        
        Returns:
            twilioSMSResponse: The response from the Twilio API.
        """
        client = self.get_client()
        
        request_data = createTwilioSMS.twilioRequest(msg)
        
        try:
            response = client.post(url=f"{TWILIO_URL}/Accounts/{TWILIO_SID}/Messages.json",
                                data=request_data)
            rc = response.json()
            
            retry_counter =0
            while response.status_code == 429 and retry_counter < 5:
                
                l.warn("Rate limited...", 
                    code=rc['code'],
                    message=rc['message'],
                    more_info=rc['more_info'],
                    status=rc['status'])
                retry_counter += 1
                self.exponential_backoff(retry_counter)

            
            sms_response = twilioSMSResponseHandler.from_response_dict(rc)

            delivery_status = sms_response.status

            delivery_counter = 0 
            while delivery_status not in ['delivered', 'undelivered', 'failed'] and delivery_counter < 5:
                self.exponential_backoff(delivery_counter+1)
                status_check = self.check_delivery(sms_response.sid)
                delivery_status = status_check.json().get('status', delivery_status)
                delivery_counter += 1
                if status_check.status_code == 200:
                    sms_response = twilioSMSResponseHandler.from_response_dict(status_check.json())
                    header = twilioHeaderHandler.from_headers_dict(status_check.headers)

            if status_check.status_code != 200:
                l.error(f"Failed to retrieve message status: {status_check.json().get('message', 'Unknown error')}", 
                    code=status_check.json().get('code', 'Unknown'),
                    more_info=status_check.json().get('more_info', 'Unknown'),
                    status=status_check.status_code)
                raise Exception(f"Failed to retrieve message status: {status_check.json().get('message', 'Unknown error')}")
            
            
            msg_object, db_message = APIMessageHandler.process_twilio_response(sms_response, save_to_db=True)

            l.info(f"Message sent successfully! SID: {sms_response.sid}", 
            conversation_id=str(msg_object.conversation_id), 
            application_message_id=str(msg_object.id),
            database_message_id=str(db_message.id),
            concurrent_requests=header.twilio_concurrent_requests, duration=header.twilio_request_duration, request_id=header.twilio_request_id,
            delivery_status = sms_response.status, twilio_timestamp=sms_response.date_created.isoformat())



        except requests.RequestException as e:
            l.error(f"Request to Twilio API failed: {e}", exc_info=True)
            raise Exception(f"Failed to send SMS: {str(e)}")
        
        
        return msg_object, header

    def check_delivery(self, sid):
        """
        Check the delivery status of a message using its SID.
        GET https://serverless.twilio.com/Logs/{Sid}

        Args:
            sid (str): The SID of the message to check.
        
        Returns:
            twilioSMSResponse: The response from the Twilio API containing the message status.
        """
        client = self.get_client()
        
        try:
            response = client.get(url=f"{TWILIO_URL}/Accounts/{TWILIO_SID}/Messages/{sid}.json", 
                                  auth=(TWILIO_SID, TWILIO_SECRET))
            rc = response.json()
            
            if response.status_code != 200:
                
                l.error(f"Failed to retrieve message status: {rc['message']}", 
                    code=rc['code'], 
                    more_info=rc['more_info'], 
                    status=rc['status'])
                raise Exception(f"Failed to retrieve message status: {rc['message']}")
            
            return response
        
        except requests.RequestException as e:
            l.error(f"Request to Twilio API failed: {e}", exc_info=True)
            raise Exception(f"Failed to check delivery status: {str(e)}")







if __name__ == "__main__":
    msg = twilioSMS(to=TEST_DESTINATION_NUMBER,
            from_=DEFAULT_TWILIO_NUMBER,
            body='Test message from Hatch!'
            )
    tw = twilioAPI()
    l.info("Sending message", to=msg.to, from_=msg.from_, body=msg.body)
    result, header = tw.send_sms(msg)
    #l.info("Result", data=result)
    # l.info("Message sent successfully!", 
    #     conversation_id=str(result.conversation_id), 
    #     application_message_id=str(result.id),
    #     status_code=result.status, 
    #     twilio_concurrent_requests=header.twilio_concurrent_requests, 
    #     twilio_request_duration=header.twilio_request_duration, 
    #     twilio_request_id=header.twilio_request_id)



