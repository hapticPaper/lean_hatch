
from utils import *
from data_model import hatchUser, MessageType, Message, SMSMessage, EmailMessage, User, modelMetaData, APIMessageHandler, dbEmail


l = logger
import os
import dotenv

import sqlalchemy
from sqlalchemy import create_engine, exc, Executable, text, Connection
from sqlalchemy.orm import declarative_base, sessionmaker


dotenv.load_dotenv()
dotenv_secrets = os.path.join('.secrets', '.secrets')
dotenv.load_dotenv(dotenv_secrets, override=True)



class hatchPostgres():
    def __init__(self):
        self.engine = self.connect()
        self.conn: Connection | None = None

    def get_database_url(self) -> str:
        """Retrieves the database URL from environment variables."""
        db_user = os.environ.get('POSTGRES_USER')
        db_password = os.environ.get('POSTGRES_PASSWORD')
        db_host = os.environ.get('POSTGRES_HOST')
        db_port = os.environ.get('POSTGRES_PORT', '5432')
        self.db_name = os.environ.get('POSTGRES_DB')

            
        return f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}"
    


    def connect(self, debug=False):
        """Creates a PostgreSQL database engine and session."""
        try:
            db_url = self.get_database_url()
            self.engine = create_engine(f"{db_url}/{self.db_name}", future=True)
            
            # Create session
            Session = sessionmaker(bind=self.engine)
            self.session = Session()
            
            if debug:
                # Test the connection using ORM
                result = self.session.execute(text("SELECT 1"))
                l.info(f"Connection test result: {result.scalar()}")
            
            return self.session
        except exc.OperationalError as e:
            l.error(f"Failed to connect to the PostgreSQL database: {e}")
            return None

    def create_tables(self):
        """Create all tables using ORM metadata (CREATE IF NOT EXISTS behavior)."""
        if self.engine is None:
            l.error("No engine available. Connect first.")
            return False
            
        try:
            # checkfirst=True is the default and provides CREATE IF NOT EXISTS behavior
            modelMetaData.create_all(self.engine, checkfirst=True)
            l.info("Database schema created/updated successfully using ORM.")
            return True
        except Exception as e:
            l.error("Failed to create database schema.", error=e)
            return False
    
    def create_database(self, database_name):
        self.conn = self.connect()
        try:
            self.conn.execute(text(f"CREATE DATABASE {database_name}"))
            self.db_name = database_name
            l.info(f"Database '{self.db_name}' created successfully.")
            return 
        except exc.ProgrammingError as e:
            l.error(f"Couldnt create database '{self.db_name}'",error=e)



if __name__ == "__main__":
    # Example usage
    pg = hatchPostgres()
    
    # Connect to the database
    session = pg.connect(debug=True)
    
    if session is not None:
        # Create tables using ORM
        if pg.create_tables():
            l.info("Tables created successfully.")
        else:
            l.error("Failed to create tables.")
    else:
        l.error("Failed to establish database connection.")