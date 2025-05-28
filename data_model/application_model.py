from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID, uuid4
from enum import Enum
from datetime import datetime
import hashlib

def generate_conversation_id(to: str, from_: str) -> UUID:
    """Generate a conversation ID by sorting to/from IDs, concatenating, and hashing to UUID."""
    # Sort the IDs to ensure consistent conversation IDs regardless of message direction
    sorted_ids = sorted([to, from_])
    concatenated = ''.join(sorted_ids)
    
    # Hash the concatenated string and convert to UUID
    hash_object = hashlib.sha256(concatenated.encode())
    hash_hex = hash_object.hexdigest()
    
    # Use first 32 characters of hash to create UUID
    uuid_string = f"{hash_hex[:8]}-{hash_hex[8:12]}-{hash_hex[12:16]}-{hash_hex[16:20]}-{hash_hex[20:32]}"
    return UUID(uuid_string)


class twilioResponseHeader(BaseModel):
    """Model for Twilio API response headers."""
    model_config = ConfigDict(from_attributes=True)
    
    content_type: str
    content_length: int
    connection: str
    date: datetime
    twilio_concurrent_requests: int
    twilio_request_id: str
    twilio_request_duration: float
    x_home_region: str
    x_api_domain: str
    strict_transport_security: str
    x_cache: str
    via: str
    x_amz_cf_pop: str
    x_amz_cf_id: str
    x_powered_by: str
    x_shenanigans: str | None = None  # Optional field for additional headers
    vary: str | None = None  # Optional field for additional headers


class twilioSMSResponse(BaseModel):
    """Model for Twilio API message response."""
    model_config = ConfigDict(from_attributes=True, validate_by_name=True)
    
    account_sid: str
    api_version: str
    body: str
    date_created: datetime
    date_sent: datetime | None = None
    date_updated: datetime
    direction: str
    error_code: int | None = None
    error_message: str | None = None
    from_: str = Field(..., alias='from')
    messaging_service_sid: str | None = None
    num_media: int
    num_segments: int
    price: float | None = None
    price_unit: str | None = 'USD'
    sid: str
    status: str
    subresource_uris: dict[str, str]
    to: str
    uri: str



class twilioSMS(BaseModel):
    """Model for Twilio API messages."""
    model_config = ConfigDict(from_attributes=True)
    
    to: str
    from_: str 
    body: str
    conversation_id: UUID | None = None
    timestamp: datetime | None = None



    def __init__(self, **data):
        super().__init__(**data)
        if self.conversation_id is None:
            self.conversation_id = generate_conversation_id(self.to, self.from_)


class hatchUser(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID 
    username: str
    email: str
    phone_number: str | None = None

class MessageStatus(str, Enum):
    """Supported message statuses."""
    
    SENT = "sent"
    DELIVERED = "delivered"
    RECEIVED = "received"
    FAILED = "failed"
    PENDING = "pending"

class MessageDirection(str, Enum):
    """Supported message directions."""
    
    INBOUND_API = "inbound-api"
    OUTBOUND_API = "outbound-api"


class MessageType(str, Enum):
    """Supported message types."""
    
    SMS = "sms"
    MMS = "mms"
    EMAIL = "email"

class apiMessage(BaseModel):
    """Base model for API messages."""
    
    id: UUID = Field(default_factory=uuid4)
    to: str
    from_: str = Field(..., alias='from')
    body: str
    type: MessageType
    status: MessageStatus | None = MessageStatus.PENDING
    direction: MessageDirection | None = None
    timestamp: datetime | None = None
    conversation_id: UUID | None = None
    
    def __init__(self, **data):
        super().__init__(**data)
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.conversation_id is None:
            self.conversation_id = generate_conversation_id(self.to, self.from_)

class hatchMessage(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID = Field(default_factory=uuid4)
    to_contact: str
    from_contact: str
    body: str
    type: MessageType
    timestamp: datetime | None = None
    status: str | None = None
    conversation_id: UUID | None = None
    
    # Additional Twilio-specific fields
    external_sid: str | None = None  # Twilio message SID
    direction: str | None = None  # inbound-api, outbound-api, etc.
    error_code: int | None = None  # Twilio error code if any
    error_message: str | None = None  # Twilio error message if any
    num_media: int | None = 0  # Number of media attachments
    num_segments: int | None = 1  # Number of SMS segments
    price: float | None = None  # Cost of the message
    price_unit: str | None = 'USD'  # Currency unit
    date_sent: datetime | None = None  # When message was actually sent
    date_updated: datetime | None = None  # When message was last updated

    def __init__(self, **data):
        super().__init__(**data)
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.conversation_id is None:
            self.conversation_id = generate_conversation_id(self.to_contact, self.from_contact)

    def __repr__(self):
        return f"<Message(id={self.id}, recipient={self.to_contact}, sender={self.from_contact}, body={self.body}, type={self.type}, status={self.status})>"
    
class SMSMessage(hatchMessage):
    """SMS message model."""
    
    type: MessageType = MessageType.SMS



class EmailMessage(hatchMessage):
    """Email message model."""
    subject: str
    to_contact: str  # Changed from To to str for consistency
    from_contact: str  # Changed from Email to str for consistency  
    body: str  # Use body instead of content for consistency with parent class
    html_content: str | None = None  # Optional HTML content
    type: MessageType = MessageType.EMAIL
    
    # Email-specific fields
    cc: list[str] | None = None
    bcc: list[str] | None = None
    reply_to: str | None = None
    attachments: list[str] | None = None
    provider_response: dict | None = None  # Store provider response data

    model_config = ConfigDict(from_attributes=True)

    