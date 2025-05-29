# Hatch - Real-time Messaging Service

## Quickstart

```bash
git clone https://github.com/hapticPaper/lean_hatch

cd lean_hatch

python -m pip install -r requirements.txt

docker-compose up -d 

python db/postgres_connector.py ## Running this as main will ensure the messages and email tables are created from the ORM. 

python app.py
```

The api can be tested by running
```bash
pytest pytests.py
```

It tests 3 endpoints:

- `http://{FLASK_HOST}:{FLASK_PORT}/api/send_email`
- `http://{FLASK_HOST}:{FLASK_PORT}/api/send_message`
- `http://{FLASK_HOST}:{FLASK_PORT}/api/conversations`

An API built with Python, Flask, Pydantic, SQLAlchemy, PostgreSQL supporting Twilio SMS and SendGrid. 

## 📁 Project Structure

```
lean_hatch/
├── app.py                 # Main application entry point
├── pytests.py            # Pytest test suite for API endpoints
├── requirements.txt      # Python dependencies
├── docker-compose.yaml   # Docker services configuration
│
├── api/                    # Flask web application
│   ├── api.py             # Main Flask app with REST endpoints
│   └── templates/
│       └── index.html     # Web interface with messaging UI and email composer
│
├── data_model/            # Data models and handlers
│   ├── application_model.py    # Pydantic V2 models for business logic
│   ├── database_model.py       # SQLAlchemy ORM models (Messages & Emails)
│   └── api_message_handler.py  # Message/Email conversion & DB operations
│
├── db/                    # Database connectivity
│   └── postgres_connector.py   # PostgreSQL connection management
│
├── providers/             # External service integrations
│   ├── rest_connector.py       # Twilio SMS client
│   └── sendgrid_email_connector.py  # SendGrid email client
│
├── utils/                 # Utilities and configuration
│   ├── logger_config.py        # Structured logging with Rich
│   └── exceptions.py           # Custom exception classes
│
└── tests/                 # Test files and templates
    
```


## 🔌 API Endpoints

### REST API (`/api/...`)

| Endpoint | Method | Purpose | Response |
|----------|---------|---------|----------|
| `/api/conversations` | GET | List all conversations | `{conversations: [...]}` |
| `/api/conversation/<id>/messages` | GET | Get messages for conversation | `{messages: [...]}` |
| `/api/send_message` | POST | Send new message | `{success: true, message_id: "..."}` |
| `/api/send_email` | POST | Send email via SendGrid | `{success: true, email_id: "..."}` |


## 🔄 Module Interactions

```
User Input → Flask API → Data Models → Database 
```


## 📊 Data Models


#### 1. **Application Models** (`application_model.py`)

  ```python
  class hatchMessage(BaseModel):
      id: UUID4
      to_contact: str
      from_contact: str
      body: str
      conversation_id: UUID4  # Auto-generated from participants
      timestamp: datetime
      status: str
      direction: str
  
  class EmailMessage(BaseModel):
      id: UUID4
      to_email: str
      from_email: str
      subject: str
      body: str
      html_content: Optional[str]
      cc: Optional[str]
      bcc: Optional[str]
      reply_to: Optional[str]
      attachments: Optional[str]
      timestamp: datetime
      status: str
      provider_response: Optional[str]
  
  class twilioSMS(BaseModel):
      to: str = Field(regex=r'^\+\d{10,15}$')
      from_: str = Field(alias='from', regex=r'^\+\d{10,15}$')
      body: str = Field(max_length=1600)
  
      from_contact: str
      body: str
      conversation_id: UUID4  # Auto-generated from participants
      timestamp: datetime
      status: str
      direction: str
  
  class twilioSMS(BaseModel):
      to: str = Field(regex=r'^\+\d{10,15}$')
      from_: str = Field(alias='from', regex=r'^\+\d{10,15}$')
      body: str = Field(max_length=1600)
  ```

#### 2. **Database Models** (`database_model.py`)
**Tables:**
- `messages` - SMS/chat messages with conversation grouping
- `emails` - Email records with SendGrid integration


#### 3. Handlers (`data_model\api_message_handler.py`)
handles conversions between datamodels and postgres writes. 

**Conversation IDs**<br>
 Groups messages between same participants<br>
- **Algorithm**: SHA256 hash of sorted participant IDs → UUID
- **Implementation**:
  ```python
  def generate_conversation_id(participant1: str, participant2: str) -> UUID:
      participants = sorted([participant1, participant2])
      hash_input = ''.join(participants)
      hash_digest = hashlib.sha256(hash_input.encode()).hexdigest()
      return UUID(hash_digest[:32])
  ```

### Environment Configuration

#### **Required Environment Variables** (`.env`):
```bash
# PostgreSQL
POSTGRES_USER=hatchuser
POSTGRES_DB=hatchapp

# Application
FLASK_ENV=development
FLASK_PORT=5000

# Optional services
MONGO_USER=hatchuser
INFLUXDB_USER=hatchuser
INFLUXDB_ORGANIZATION=hatch
INFLUXDB_BUCKET=messages
```

#### **Required Secrets** (`.secrets/` directory):
```bash
.secrets/
├── POSTGRES_PASSWORD      # PostgreSQL password
├── MONGO_PASSWORD         # MongoDB password (if enabled)
├── INFLUX_TOKEN          # InfluxDB token (if enabled)
├── INFLUXDB_PASSWORD     # InfluxDB password (if enabled)
└── TWILIO_AUTH_TOKEN     # Twilio authentication token
```



### Fronted as api testing:
1. **Access web interface**: http://localhost:5000
2. **View conversations**: Automatically loads from database
3. **Send messages**: 
   - Phone numbers → Twilio SMS
   - Names → Database only
4. **Send emails**: Click "Compose Email" button for modal popup
