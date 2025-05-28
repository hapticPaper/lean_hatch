# Real-time PostgreSQL LISTEN/NOTIFY handler
import json
import threading
import time
import psycopg2
import os
import dotenv

# Import utilities
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils import logger

# Load environment variables
dotenv.load_dotenv()
dotenv_secrets = os.path.join(os.path.dirname(__file__), '..', '.secrets', '.secrets')
dotenv.load_dotenv(dotenv_secrets, override=True)

l = logger


class PostgreSQLListener:
    """Handles PostgreSQL LISTEN/NOTIFY operations for real-time updates"""
    
    def __init__(self, postgres_connector, callback_handler):
        """
        Initialize listener with postgres connector and callback handler
        
        Args:
            postgres_connector: Instance of hatchPostgres
            callback_handler: Function to call when notifications are received
        """
        self.pg = postgres_connector
        self.callback = callback_handler
        self.connection = None
        self.running = False
        self.listener_thread = None
    
    def start(self):
        """Start the listener in a background thread"""
        if self.listener_thread and self.listener_thread.is_alive():
            return
            
        self.running = True
        self.listener_thread = threading.Thread(target=self._listen_loop)
        self.listener_thread.daemon = True
        self.listener_thread.start()
        l.info("PostgreSQL listener started")
    
    def stop(self):
        """Stop the listener thread"""
        self.running = False
        if self.listener_thread:
            self.listener_thread.join()
        self._cleanup_connection()
        l.info("PostgreSQL listener stopped")
    
    def _get_raw_connection(self):
        """Get a raw psycopg2 connection from the postgres_connector"""
        try:
            # Get the raw connection from the engine
            raw_conn = self.pg.get_engine().raw_connection()
            return raw_conn
                
        except Exception as e:
            l.error("Failed to get raw connection from postgres_connector", error=str(e))
            return None
    
    def _setup_connection(self):
        """Setup and configure the PostgreSQL connection for LISTEN"""
        try:
            # Close existing connection if any
            self._cleanup_connection()
            
            # Get new connection
            self.connection = self._get_raw_connection()
            if not self.connection:
                l.error("Could not get raw connection from postgres_connector")
                return False
            
            # Configure connection
            self.connection.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
            
            # Set up LISTEN for channels
            cursor = self.connection.cursor()
            cursor.execute("LISTEN message_changes;")
            cursor.execute("LISTEN conversation_changes;")
            cursor.close()
            
            l.info("Successfully set up PostgreSQL LISTEN for message_changes and conversation_changes")
            return True
            
        except Exception as e:
            l.error("Failed to setup PostgreSQL connection", error=str(e))
            self._cleanup_connection()
            return False
    
    def _cleanup_connection(self):
        """Clean up the PostgreSQL connection"""
        if self.connection:
            try:
                self.connection.close()
                l.info("Closed PostgreSQL notification listener connection")
            except Exception as e:
                l.error("Error closing connection", error=str(e))
            finally:
                self.connection = None
    
    def _is_connection_valid(self):
        """Check if the current connection is valid"""
        return self.connection is not None and self.connection.closed == 0
    
    def _process_notification(self, notify):
        """Process a single notification and determine event type"""
        try:
            payload = json.loads(notify.payload) if notify.payload else {}
            l.info("Received notification", channel=notify.channel, payload=payload)
            
            # Determine event type based on channel
            event_type = self._get_event_type(notify.channel)
            
            # Create event data
            event_data = {
                'type': event_type,
                'conversation_id': payload.get('conversation_id'),
                'action': payload.get('action'),  # 'INSERT', 'UPDATE', 'DELETE'
                'message_id': payload.get('message_id'),
                'timestamp': time.time()
            }
            
            # Send to callback handler
            self.callback(event_data)
            
        except json.JSONDecodeError as e:
            l.error("Error parsing notification payload", error=str(e))
        except Exception as e:
            l.error("Error processing notification", error=str(e))
    
    def _get_event_type(self, channel):
        """Map PostgreSQL channel to event type"""
        channel_mapping = {
            'message_changes': 'message_update',
            'conversation_changes': 'conversation_changes'
        }
        return channel_mapping.get(channel, 'unknown')
    
    def _listen_loop(self):
        """Main listening loop that runs in background thread"""
        while self.running:
            try:
                # Ensure connection is valid
                if not self._is_connection_valid():
                    l.info("Setting up PostgreSQL connection...")
                    if not self._setup_connection():
                        l.error("Failed to setup connection, retrying in 10 seconds...")
                        time.sleep(10)
                        continue
                
                # Poll for notifications
                if self.connection:  # Type guard for mypy
                    self.connection.poll()
                    
                    # Process all pending notifications
                    while self.connection.notifies:
                        notify = self.connection.notifies.pop(0)
                        self._process_notification(notify)
                
                # Small delay to prevent excessive CPU usage
                time.sleep(0.1)
                
            except psycopg2.OperationalError as e:
                l.error("PostgreSQL connection error", error=str(e))
                self.connection = None
                time.sleep(5)  # Wait before retrying
                
            except Exception as e:
                l.error("Error in notification listener", error=str(e))
                self._cleanup_connection()
                time.sleep(5)  # Wait before retrying
        
        # Final cleanup when loop exits
        self._cleanup_connection()
