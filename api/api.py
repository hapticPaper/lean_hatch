# Add parent directory to path for imports
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils import logger
logger_instance = logger
import os
import dotenv
import json
import flask
from flask import request, jsonify, render_template, send_from_directory, Response
from datetime import datetime
from uuid import uuid4
from sqlalchemy import text, func, case


from data_model.application_model import twilioSMS, hatchMessage, MessageType, SMSMessage, EmailMessage
from data_model.database_model import Message,  User, dbEmail
from data_model.api_message_handler import APIMessageHandler
from providers.rest_connector import twilioAPI
from db.postgres_connector import hatchPostgres


dotenv.load_dotenv()
dotenv_secrets = os.path.join(os.path.dirname(__file__), '..', '.secrets', '.secrets')
dotenv.load_dotenv(dotenv_secrets, override=True)


FLASK_HOST = os.getenv('FLASK_HOST', '0.0.0.0')
FLASK_PORT = int(os.getenv('FLASK_PORT', 5000))


app = flask.Flask(__name__)

# Initialize database connection
pg = hatchPostgres()


@app.route('/', methods=['GET'])
def index():
    """
    Landing page for the messaging interface.
    """
    return render_template('index.html'), 200

@app.route('/api/conversations', methods=['GET'])
def get_conversations():
    """
    API endpoint to get all conversations with latest message info.
    Returns: List of conversations with conversation_id, participants, and last message date.
    """
    try:
        session = pg.start_connection()
        if not session:
            return jsonify({"error": "Database connection failed"}), 500

        # Get all conversations (grouped by conversation_id)
        convs = (
            session.query(
                Message.conversation_id,
                case(
                    (Message.direction == 'inbound-api', Message.from_contact ),
                    else_=(Message.to_contact )
                ).label('reply_to'),
                case(
                    (Message.direction == 'inbound-api', Message.from_contact + '->' + Message.to_contact),
                    else_=(Message.to_contact + '->' + Message.from_contact)
                ).label('participants'),
                func.max(Message.timestamp).label('last_message_date'),
                func.count(Message.id).label('messages')
            )
            .group_by(
                Message.conversation_id,
                case(
                    (Message.direction == 'inbound-api', Message.from_contact ),
                    else_=(Message.to_contact )
                ),
                case(
                    (Message.direction == 'inbound-api', Message.from_contact + '->' + Message.to_contact),
                    else_=(Message.to_contact + '->' + Message.from_contact)
                )
            )
            .order_by(func.max(Message.timestamp).desc())
            .all()
        )
        session.close()

        conversation_response = APIMessageHandler.conversation_tuples_to_dicts(convs)


       
        return jsonify({"conversations": conversation_response}), 200

    except Exception as e:
        logger_instance.error("Failed to get conversations", error=str(e))
        return jsonify({"error": str(e)}), 500

@app.route('/api/conversation/<conversation_id>/messages', methods=['GET'])
def get_conversation_messages(conversation_id):
    """
    API endpoint to get all messages for a specific conversation.
    """
    try:
        session = pg.start_connection()
        if not session:
            return jsonify({"error": "Database connection failed"}), 500

        # ORM: Get all messages for this conversation
        messages_query = (
            session.query(Message)
            .filter(Message.conversation_id == conversation_id)
            .order_by(Message.timestamp.asc())
            .all()
        )
        messages = []
        for row in messages_query:
            messages.append({
                'id': str(row.id),
                'to_contact': row.to_contact,
                'from_contact': row.from_contact,
                'body': row.body,
                'type': row.type,
                'timestamp': row.timestamp.isoformat() if row.timestamp else None,
                'status': row.status,
                'external_sid': row.external_sid,
                'direction': row.direction,
                'error_code': row.error_code,
                'error_message': row.error_message,
                'is_delivered': row.status in ['delivered', 'sent'] if row.status else False
            })

        session.close()
        return jsonify({"messages": messages}), 200

    except Exception as e:
        logger_instance.error("Failed to get conversation messages", error=str(e), conversation_id=conversation_id)
        return jsonify({"error": str(e)}), 500




@app.route('/api/send_message', methods=['POST'])
def send_message():
    """
    Straight API endpoint to send a message.
    Expects: to, from, body in JSON payload.
    Sends via Twilio if both are phone numbers, otherwise saves to database.
    """
    try:
        data = request.json
        if not data or not all(k in data for k in ('to', 'from', 'body')):
            return jsonify({"error": "Missing required fields: to, from, body"}), 400

        to_contact = data['to']
        from_contact = data['from']
        body = data['body']
        conversation_id = data.get('conversation_id', str(uuid4()))

        if is_phone_number(to_contact):
            # Send via Twilio
            logger_instance.info("Sending SMS via Twilio", to=to_contact, from_=from_contact)

            twilio_client = twilioAPI()
            sms = twilioSMS(to=to_contact, from_=from_contact, body=body)

            try:
                app_message, header = twilio_client.send_sms(sms)
                return jsonify({
                    "success": True,
                    "message_id": str(app_message.id),
                    "status": app_message.status,
                    "method": "twilio"
                }), 200

            except Exception as twilio_error:
                logger_instance.error("Twilio SMS failed", error=str(twilio_error))
                return jsonify({"error": f"Failed to send SMS: {str(twilio_error)}"}), 500

        else:
            # Save directly to database
            logger_instance.info("Saving message directly to database", to=to_contact, from_=from_contact)

            message = Message(
                id=uuid4(),
                to_contact=to_contact,
                from_contact=from_contact,
                body=body,
                type=MessageType.SMS,
                timestamp=datetime.now(),
                status="sent",
                conversation_id=conversation_id,
                direction="outbound-api"
            )

            session = pg.start_connection()
            session.add(message)
            session.commit()
            session.close()

            return jsonify({
                "success": True,
                "message_id": str(message.id),
                "status": "sent",
                "method": "database"
            }), 200

    except Exception as e:
        logger_instance.error("Failed to send message", error=str(e))
        return jsonify({"error": str(e)}), 500


@app.route('/api/conversation/<conversation_id>/new_messages', methods=['GET'])
def get_new_messages(conversation_id):
    """
    API endpoint to get new messages for a conversation since a given timestamp.
    Used for real-time updates.
    """
    try:
        since_timestamp = request.args.get('since')
        if not since_timestamp:
            return jsonify({"error": "Missing 'since' parameter"}), 400

        session = pg.start_connection()
        if not session:
            return jsonify({"error": "Database connection failed"}), 500

        # ORM: Query for messages newer than the given timestamp
        messages_query = (
            session.query(Message)
            .filter(
                Message.conversation_id == conversation_id,
                Message.timestamp > since_timestamp
            )
            .order_by(Message.timestamp.asc())
            .all()
        )

        messages = []
        for row in messages_query:
            messages.append({
                'id': str(row.id),
                'to_contact': row.to_contact,
                'from_contact': row.from_contact,
                'body': row.body,
                'type': row.type,
                'timestamp': row.timestamp.isoformat() if row.timestamp else None,
                'status': row.status,
                'external_sid': row.external_sid,
                'direction': row.direction,
                'error_code': row.error_code,
                'error_message': row.error_message,
                'is_delivered': row.status in ['delivered', 'sent'] if row.status else False
            })

        session.close()
        return jsonify({"messages": messages}), 200

    except Exception as e:
        logger_instance.error("Failed to get new messages", error=str(e), conversation_id=conversation_id)
        return jsonify({"error": str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint to verify the service is running.
    """
    return jsonify({"status": "ok"}), 200


def is_phone_number(contact)-> bool:
    return contact.startswith('+')  

@app.route('/favicon.ico', methods=['GET'])
def favicon():
    return send_from_directory('static', 'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/api/send_email', methods=['POST'])
def send_email():
    """
    API endpoint to send an email.
    Handles email sending through the application's message handling system.
    """
    try:
        data = request.json
        if not data or not all(k in data for k in ('to_email', 'subject', 'body')):
            return jsonify({"error": "Missing required fields: to_email, subject, body"}), 400
        
        to_email = data['to_email']
        subject = data['subject']
        body = data['body']
        from_email = data.get('from_email', 'ian@hapticpaper.com')  # Default sender
        
        logger_instance.info("Sending email via API", to=to_email, subject=subject)
        
        # Send email through the message handler
        email_msg, response_data = APIMessageHandler.send_email_via_sendgrid(
            to_email=to_email,
            subject=subject,
            body=body,
            from_email=from_email,
            save_to_db=True
        )
        
        return jsonify({
            "success": True,
            "email_id": str(email_msg.id),
            "status": email_msg.status,
            "message_id": response_data.get('message_id'),
            "method": "sendgrid"
        }), 200
        
    except Exception as e:
        logger_instance.error("Failed to send email via API", error=str(e))
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host=FLASK_HOST, port=FLASK_PORT, debug=True)
