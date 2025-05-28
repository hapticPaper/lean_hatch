import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))


import requests
import os
from utils import *
from requests.auth import HTTPBasicAuth
import dotenv
import json
import argparse


from data_model import hatchUser, MessageType, Message, SMSMessage, EmailMessage, User, modelMetaData, APIMessageHandler
from db.postgres_connector import hatchPostgres


dotenv.load_dotenv()
dotenv_secrets = os.path.join(os.path.dirname(__file__), '.secrets', '.secrets')
dotenv.load_dotenv(dotenv_secrets, override=True)

l = logger

parser = argparse.ArgumentParser(description="Send SMS messages using Twilio API")
parser.add_argument('--test_file', type=str, required=True, default="tests/test_messages.json",
                    help="Path to the JSON file containing test messages")
args = parser.parse_args()


def send_sms(to, from_, body):
    url = 'https://api.twilio.com/2010-04-01/Accounts/ACd67d920e2f8354696051a98d2d444815/Messages.json'
    data = {
        'To': to,
        'From': from_,
        'Body': body
    }
    auth = HTTPBasicAuth('ACd67d920e2f8354696051a98d2d444815', '72bad703cab77f165d3841184f5890f9')
    
    response = requests.post(url, data=data, auth=auth)
    
    if response.status_code == 201:
        print("Message sent successfully!")
    else:
        print(f"Failed to send message: {response.status_code} - {response.text}")



if __name__ == "__main__":
    to = '+18777804236'  # Replace with the recipient's phone number
    from_ = '+18333450761'  # Replace with your Twilio phone number
    body = 'Hello, this is a test message!'
    

    with open(args.test_file, "r") as f:
        test_messages = json.load(f)
        f.close()
    for message in test_messages:          
        message['message_type'] = MessageType.SMS
        api_msg, app_msg, db_msg  = APIMessageHandler.process_json_message(message)
        l.info("Raw message:",**message)
        l.info("Processed", **app_msg.__dict__)
        l.info("Database model:", **db_msg.__dict__) 
        print("")

        




