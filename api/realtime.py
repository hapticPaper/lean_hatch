# Real-time updates using PostgreSQL LISTEN/NOTIFY + Server-Sent Events
import json

# Import utilities
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils import logger
from _realtime_listener import PostgreSQLListener

log = logger

class RealtimeUpdates:
    def __init__(self, postgres_connector):
        """
        Initialize RealtimeUpdates with an existing PostgreSQL connector instance.
        
        Args:
            postgres_connector: An instance of hatchPostgres
        """
        self.clients = set()
        self.pg = postgres_connector
        
        # Initialize the PostgreSQL listener with callback
        self.listener = PostgreSQLListener(postgres_connector, self._handle_notification)
    
    def _handle_notification(self, event_data):
        self._broadcast_update(event_data)
    
    def start_listener(self):
        self.listener.start()
    
    def stop_listener(self):
        self.listener.stop()
    
    
    def _broadcast_update(self, data):
        """Send update to all connected SSE clients"""
        message = f"data: {json.dumps(data)}\n\n"
        log.info("Broadcasting to SSE clients", client_count=len(self.clients), data=data)
        
        # Remove disconnected clients
        disconnected = set()
        for client in self.clients:
            try:
                client.put(message)
            except Exception as e:
                log.error("Error sending to SSE client", error=str(e))
                disconnected.add(client)
        
        for client in disconnected:
            self.clients.discard(client)
        
        log.info("Successfully broadcast to SSE clients", 
               successful_clients=len(self.clients) - len(disconnected),
               failed_clients=len(disconnected))
    
    def add_client(self, client_queue):
        """Add a new SSE client"""
        self.clients.add(client_queue)
        log.info("Added SSE client", total_clients=len(self.clients))
        
        # Start listener if not already running
        self.start_listener()
    
    def remove_client(self, client_queue):
        self.clients.discard(client_queue)
        log.info("Removed SSE client", total_clients=len(self.clients))
        
        # Stop listener if no clients remain
        if not self.clients:
            self.stop_listener()
    
    def stop(self):
        self.stop_listener()
        self.clients.clear()
        log.info("Realtime updates stopped")

# Note: No global instance created here - Flask will create and manage the instance
