


import requests
import os
from utils import *
from requests.auth import HTTPBasicAuth
import dotenv
import json

from data_model import hatchUser, MessageType, Message, SMSMessage, EmailMessage, User, modelMetaData, APIMessageHandler
from db.postgres_connector import hatchPostgres


dotenv.load_dotenv()
dotenv_secrets = os.path.join(os.path.dirname(__file__), '.secrets', '.secrets')
dotenv.load_dotenv(dotenv_secrets, override=True)

l = logger




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



def first_run():
    pg = hatchPostgres()
    session = pg.connect(debug=True)
    
    if session is not None:
        # Create tables using ORM
        if pg.create_tables():
            l.info("Tables created successfully.")
            l.info("Database is ready for use.")
        else:
            l.error("Failed to create tables.")
    else:
        l.error("Failed to establish database connection.")

if __name__ == "__main__":
    # to = '+18777804236'  # Replace with the recipient's phone number
    # from_ = '+18333450761'  # Replace with your Twilio phone number
    # body = 'Hello, this is a test message!'
    

    with open("test_jess_messages.json", "r") as f:
        test_messages = json.load(f)
        f.close()
    for message in test_messages:          
        message['message_type'] = MessageType.SMS
        # APIMessageHandler now automatically saves to database
        api_msg, app_msg, db_msg  = APIMessageHandler.process_json_message(message, save_to_db=True)
        l.info("Raw message:",**message)
        l.info("Processed", **app_msg.__dict__)
        l.info("Database model saved with ID:", message_id=str(db_msg.id), conversation_id=str(db_msg.conversation_id)) 
        print("")

        




