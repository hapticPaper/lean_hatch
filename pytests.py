import pytest
from utils import logger
from requests import Session
import os
import dotenv




logger_instance = logger
dotenv.load_dotenv()

FLASK_HOST = os.getenv('FLASK_HOST', 'localhost')
FLASK_PORT = os.getenv('FLASK_PORT', '5000')
FROM_NUMBER = os.getenv('TWILIO_NUMBER', '+18333450761')

email_test_session = Session()

def test_email():
    response = email_test_session.post(f"http://{FLASK_HOST}:{FLASK_PORT}/api/send_email", json={
        "from_email": "ian@hapticpaper.com",
        "to_email": "rubenstein.ian@gmail.com",
        "subject": "Test Email from pytests",
        "body": "This is a test email sent from the Flask application using the requests library."
    })
    assert response.status_code == 200
    

    
def test_sms():
    sms_test_session = Session()
    response = sms_test_session.post(f"http://{FLASK_HOST}:{FLASK_PORT}/api/send_message", json={
        "from": "+1234567890",
        "to": "+18777804236",
        "body": "test message from pytests",
    })
    assert response.status_code == 200


def test_get_conversations():
    response = email_test_session.get(f"http://{FLASK_HOST}:{FLASK_PORT}/api/conversations")
    data = response.json()
    assert response.status_code == 200