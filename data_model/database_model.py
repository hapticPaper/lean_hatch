from sqlalchemy import Column, Integer, String, Uuid, DateTime, Float, Text

from sqlalchemy.orm import declarative_base
from sqlalchemy.schema import MetaData


modelMetaData = MetaData(schema="public")
Base = declarative_base(metadata=modelMetaData)

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Uuid, primary_key=True)
    name = Column(String)
    email = Column(String)


class Message(Base):
    __tablename__ = 'messages'
    id = Column(Uuid, primary_key=True)
    to_contact = Column(String)
    from_contact = Column(String)
    body = Column(String)
    type = Column(String)
    timestamp = Column(DateTime)
    status = Column(String)
    conversation_id = Column(Uuid)  # Generated from sorted to/from IDs
    
    # Additional Twilio-specific fields
    external_sid = Column(String)  # Twilio message SID
    direction = Column(String)  # inbound-api, outbound-api, etc.
    error_code = Column(Integer)  # Twilio error code if any
    error_message = Column(String)  # Twilio error message if any
    num_media = Column(Integer, default=0)  # Number of media attachments
    num_segments = Column(Integer, default=1)  # Number of SMS segments
    price = Column(Float)  # Cost of the message
    price_unit = Column(String, default='USD')  # Currency unit
    date_sent = Column(DateTime)  # When message was actually sent
    date_updated = Column(DateTime)  # When message was last updated

    def __repr__(self):
        return f"<Message(id={self.id}, from={self.from_contact}, to={self.to_contact}, content={self.body}, status={self.status}, sid={self.external_sid})>"


class dbEmail(Base):
    __tablename__ = 'emails'
    
    id = Column(Uuid, primary_key=True)
    to_contact = Column(String, nullable=False)
    from_contact = Column(String, nullable=False)
    subject = Column(String, nullable=False)
    body = Column(Text)  # Plain text content
    html_content = Column(Text)  # HTML content
    type = Column(String, default='email')
    timestamp = Column(DateTime)
    status = Column(String)
    conversation_id = Column(Uuid)  # Generated from sorted to/from IDs
    direction = Column(String)  # inbound-api, outbound-api, etc.
    
    # Email-specific fields
    cc = Column(String)  # JSON string for list of CC emails
    bcc = Column(String)  # JSON string for list of BCC emails
    reply_to = Column(String)
    attachments = Column(String)  # JSON string for list of attachments
    
    # Provider-specific fields
    external_message_id = Column(String)  # SendGrid message ID
    provider = Column(String, default='sendgrid')
    provider_response = Column(Text)  # JSON string for full provider response
    
    # Tracking fields
    date_sent = Column(DateTime)
    date_updated = Column(DateTime)
    error_code = Column(Integer)
    error_message = Column(String)

    def __repr__(self):
        return f"<dbEmail(id={self.id}, from={self.from_contact}, to={self.to_contact}, subject={self.subject}, status={self.status}, message_id={self.external_message_id})>"


