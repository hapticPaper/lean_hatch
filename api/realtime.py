# Real-time updates using PostgreSQL LISTEN/NOTIFY + Server-Sent Events
import json
import threading
import time
import psycopg2
from flask import Response

# Import utilities
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils import logger

l = logger

class RealtimeUpdates:
    def __init__(self, postgres_connector):
        """
        Initialize RealtimeUpdates with an existing PostgreSQL connector instance.
        
        Args:
            postgres_connector: An instance of hatchPostgres
        """
        self.clients = set()
        self.listener_thread = None
        self.running = False
        self.connection = None
        self.pg = postgres_connector  # Use the passed connector instance
    
    def _get_connection_params(self):
        """Get connection parameters from the existing PostgreSQL connector"""
        try:
            # Use the existing connector to get database URL components
            db_url = self.pg.get_database_url()
            db_name = self.pg.db_name
            
            # Parse the database URL to extract connection parameters
            # Format: postgresql://user:password@host:port
            import re
            match = re.match(r'postgresql://([^:]+):([^@]+)@([^:]+):(\d+)', db_url)
            if not match:
                l.error("Could not parse database URL from PostgreSQL connector")
                return None
                
            user, password, host, port = match.groups()
            
            return {
                'host': host,
                'port': int(port),
                'database': db_name,
                'user': user,
                'password': password
            }
        except Exception as e:
            l.error("Failed to get connection parameters from PostgreSQL connector", error=str(e))
            return None
    
    
    def start_listener(self):
        """Start listening for PostgreSQL notifications"""
        if self.listener_thread and self.listener_thread.is_alive():
            return
            
        self.running = True
        self.listener_thread = threading.Thread(target=self._listen_for_notifications)
        self.listener_thread.daemon = True
        self.listener_thread.start()
    
    def _listen_for_notifications(self):
        """Listen for PostgreSQL NOTIFY events using psycopg2 directly"""
        connection = None
        
        while self.running:
            try:
                # Create a direct psycopg2 connection if needed
                if connection is None or connection.closed != 0:
                    l.info("Creating new PostgreSQL connection for notifications...")
                    
                    # Close old connection if it exists
                    if connection:
                        try:
                            connection.close()
                        except Exception:
                            pass
                    
                    # Get connection parameters from existing connector
                    conn_params = self._get_connection_params()
                    if not conn_params:
                        l.error("Could not get connection parameters, retrying in 10 seconds...")
                        time.sleep(10)
                        continue
                    
                    # Create new connection using the same credentials as your app
                    connection = psycopg2.connect(**conn_params)
                    connection.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
                    
                    # Set up LISTEN for message changes
                    cursor = connection.cursor()
                    cursor.execute("LISTEN message_changes;")
                    cursor.close()
                    l.info("Successfully set up PostgreSQL LISTEN for message_changes")
                
                # Check for notifications
                connection.poll()
                while connection.notifies:
                    notify = connection.notifies.pop(0)
                    try:
                        payload = json.loads(notify.payload) if notify.payload else {}
                        l.info("Received notification", payload=payload)
                        
                        # Broadcast to all connected clients
                        self._broadcast_update({
                            'type': 'message_update',
                            'conversation_id': payload.get('conversation_id'),
                            'action': payload.get('action'),  # 'INSERT', 'UPDATE', 'DELETE'
                            'message_id': payload.get('message_id'),
                            'timestamp': time.time()
                        })
                    except json.JSONDecodeError as e:
                        l.error("Error parsing notification payload", error=str(e))
                
                time.sleep(0.1)  # Small delay to prevent excessive CPU usage
                
            except psycopg2.OperationalError as e:
                l.error("PostgreSQL connection error", error=str(e))
                connection = None
                time.sleep(5)  # Wait before retrying
                
            except Exception as e:
                l.error("Error in notification listener", error=str(e))
                # Reset connection on error
                if connection:
                    try:
                        connection.close()
                    except Exception:
                        pass
                connection = None
                time.sleep(5)  # Wait before retrying
                
        # Cleanup when stopping
        if connection:
            try:
                connection.close()
                l.info("Closed PostgreSQL notification listener connection")
            except Exception as e:
                l.error("Error closing connection", error=str(e))
    
    
    def _broadcast_update(self, data):
        """Send update to all connected SSE clients"""
        message = f"data: {json.dumps(data)}\n\n"
        l.info("Broadcasting to SSE clients", client_count=len(self.clients), data=data)
        
        # Remove disconnected clients
        disconnected = set()
        for client in self.clients:
            try:
                client.put(message)
            except Exception as e:
                l.error("Error sending to SSE client", error=str(e))
                disconnected.add(client)
        
        for client in disconnected:
            self.clients.discard(client)
        
        l.info("Successfully broadcast to SSE clients", 
               successful_clients=len(self.clients) - len(disconnected),
               failed_clients=len(disconnected))
    
    def add_client(self, client_queue):
        """Add a new SSE client"""
        self.clients.add(client_queue)
        l.info("Added SSE client", total_clients=len(self.clients))
        if not self.listener_thread or not self.listener_thread.is_alive():
            self.start_listener()
    
    def remove_client(self, client_queue):
        """Remove an SSE client"""
        self.clients.discard(client_queue)
        l.info("Removed SSE client", total_clients=len(self.clients))
    
    def stop(self):
        """Stop the listener thread"""
        self.running = False
        if self.listener_thread:
            self.listener_thread.join()

# Note: No global instance created here - Flask will create and manage the instance
