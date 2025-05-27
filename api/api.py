# Add parent directory to path for imports
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils import logger

import flask
from flask import request, jsonify, render_template, send_from_directory, Response
from datetime import datetime
from uuid import uuid4
from sqlalchemy import text
import queue
import json


from data_model.application_model import twilioSMS, hatchMessage, MessageType
from data_model.api_message_handler import APIMessageHandler
from providers.rest_connector import twilioAPI
from db.postgres_connector import hatchPostgres
from realtime import RealtimeUpdates

logger_instance = logger
app = flask.Flask(__name__)

# Initialize database connection
pg = hatchPostgres()

# Initialize realtime updates with the PostgreSQL connector instance
realtime_updates = RealtimeUpdates(pg)

def is_phone_number(contact: str) -> bool:
    """Check if a contact string is a phone number (starts with +)."""
    return contact.startswith('+')

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
        session = pg.connect()
        if not session:
            return jsonify({"error": "Database connection failed"}), 500
        
        # Query to get conversations with latest message info
        query = """
        SELECT 
            conversation_id,
            MAX(timestamp) as last_message_date,
            COUNT(*) as messages,
            CASE WHEN direction = 'inbound-api' THEN CONCAT(from_contact, ', ',to_contact) ELSE CONCAT(to_contact, ', ',from_contact) END as participants
        FROM messages 
        GROUP BY conversation_id,4
        ORDER BY last_message_date DESC
        """
        
        result = session.execute(text(query))
        conversations = []
        
        for row in result:
            # Check if any participant is a phone number (split the participants string)
            participants_list = row.participants.split(', ') if row.participants else []
            has_phone_numbers = any(is_phone_number(p) for p in participants_list)
            
            conversations.append({
                'conversation_id': str(row.conversation_id),
                'participants': row.participants,  # Use the string directly from PostgreSQL
                'last_message_date': row.last_message_date.isoformat() if row.last_message_date else None,
                'message_count': row.messages,
                'has_phone_numbers': has_phone_numbers
            })
        
        session.close()
        return jsonify({"conversations": conversations}), 200
        
    except Exception as e:
        logger_instance.error("Failed to get conversations", error=str(e))
        return jsonify({"error": str(e)}), 500

@app.route('/api/conversation/<conversation_id>/messages', methods=['GET'])
def get_conversation_messages(conversation_id):
    """
    API endpoint to get all messages for a specific conversation.
    """
    try:
        session = pg.connect()
        if not session:
            return jsonify({"error": "Database connection failed"}), 500
        
        # Query to get all messages for this conversation
        query = """
        SELECT 
            id, to_contact, from_contact, body, type, timestamp, status,
            external_sid, direction, error_code, error_message
        FROM messages 
        WHERE conversation_id = :conversation_id
        ORDER BY timestamp ASC
        """
        
        result = session.execute(text(query), {"conversation_id": conversation_id})
        messages = []
        
        for row in result:
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
    API endpoint to send a new message in a conversation.
    Handles both phone number conversations (via Twilio) and name-based conversations (database only).
    """
    try:
        data = request.json
        if not data or not all(k in data for k in ('conversation_id', 'to', 'content')):
            return jsonify({"error": "Missing required fields: conversation_id, to, content"}), 400
        
        conversation_id = data['conversation_id']
        to_contact = data['to']
        body = data['content']
        
        # Get conversation details to find the from_contact
        session = pg.connect()
        if not session:
            return jsonify({"error": "Database connection failed"}), 500
            
        query = """
        SELECT DISTINCT from_contact, to_contact
        FROM messages 
        WHERE conversation_id = :conversation_id
        LIMIT 1
        """
        
        result = session.execute(text(query), {"conversation_id": conversation_id})
        conv_row = result.fetchone()
        session.close()
        
        if not conv_row:
            return jsonify({"error": "Conversation not found"}), 404
            
        # Determine from_contact (the contact that's not the to_contact)
        from_contact = conv_row.from_contact if conv_row.to_contact == to_contact else conv_row.to_contact
        
        # Check if both contacts are phone numbers
        if is_phone_number(to_contact) and is_phone_number(from_contact):
            # Send via Twilio
            logger_instance.info("Sending SMS via Twilio", to=to_contact, from_=from_contact)
            
            sms = twilioSMS(to=to_contact, from_=from_contact, body=body)
            twilio_client = twilioAPI()
            
            try:
                app_message, header = twilio_client.send_sms(sms)
                
                return jsonify({
                    "success": True,
                    "message_id": str(app_message.id),
                    "conversation_id": str(app_message.conversation_id),
                    "status": app_message.status,
                    "method": "twilio"
                }), 200
                
            except Exception as twilio_error:
                logger_instance.error("Twilio SMS failed", error=str(twilio_error))
                return jsonify({"error": f"Failed to send SMS: {str(twilio_error)}"}), 500
        
        else:
            # Save directly to database (name-based conversation)
            logger_instance.info("Saving message directly to database", to=to_contact, from_=from_contact)
            
            # Create a hatchMessage directly
            message = hatchMessage(
                id=uuid4(),
                to_contact=to_contact,
                from_contact=from_contact,
                body=body,
                type=MessageType.SMS,
                timestamp=datetime.now(),
                status="sent"
            )
            
            # Save to database
            handler = APIMessageHandler()
            handler.save_message(message, auto_commit=True)
            handler.close_connection()
            
            return jsonify({
                "success": True,
                "message_id": str(message.id),
                "conversation_id": str(message.conversation_id),
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
        
        session = pg.connect()
        if not session:
            return jsonify({"error": "Database connection failed"}), 500
        
        # Query for messages newer than the given timestamp
        query = """
        SELECT 
            id, to_contact, from_contact, body, type, timestamp, status,
            external_sid, direction, error_code, error_message
        FROM messages 
        WHERE conversation_id = :conversation_id 
        AND timestamp > :since_timestamp
        ORDER BY timestamp ASC
        """
        
        result = session.execute(text(query), {
            "conversation_id": conversation_id,
            "since_timestamp": since_timestamp
        })
        
        messages = []
        for row in result:
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

@app.route('/api/events')
def stream_events():
    """
    Server-Sent Events endpoint for real-time updates
    """
    def event_generator():
        client_queue = queue.Queue()
        realtime_updates.add_client(client_queue)
        
        try:
            # Send initial connection message
            yield f"data: {json.dumps({'type': 'connected', 'timestamp': datetime.now().isoformat()})}\n\n"
            
            while True:
                try:
                    # Get message from queue with timeout
                    message = client_queue.get(timeout=30)  # 30 second keepalive
                    yield message
                except queue.Empty:
                    # Send keepalive
                    yield f"data: {json.dumps({'type': 'keepalive', 'timestamp': datetime.now().isoformat()})}\n\n"
                except GeneratorExit:
                    break
        finally:
            realtime_updates.remove_client(client_queue)
    
    return Response(
        event_generator(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Access-Control-Allow-Origin': '*'
        }
    )

@app.route('/favicon.ico', methods=['GET'])
def favicon():
    return send_from_directory('static', 'favicon.ico', mimetype='image/vnd.microsoft.icon')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002, debug=True)
