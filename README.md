# Hatch - Real-time Messaging Service

A comprehensive messaging service application built with Python, Flask, PostgreSQL, and Twilio SMS integration. Features real-time updates, structured logging, and a modern web interface.

## 🏗️ Architecture Overview

### High-Level Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Web Frontend  │    │   Flask API      │    │   PostgreSQL    │
│   (HTML/JS)     │◄──►│   (REST + SSE)   │◄──►│   Database      │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                               │                         │
                               ▼                         ▼
                       ┌──────────────┐         ┌─────────────────┐
                       │   Twilio     │         │   Real-time     │
                       │   SMS API    │         │   Triggers      │
                       └──────────────┘         └─────────────────┘
```

### Real-time Updates Flow

1. **Message Creation** → Database INSERT/UPDATE
2. **PostgreSQL Triggers** → Send NOTIFY to `message_changes` channel
3. **Real-time Listener** → Receives notification via `psycopg2`
4. **Server-Sent Events** → Broadcasts update to web clients
5. **Frontend** → Automatically updates UI without polling

## 📁 Project Structure

```
lean_hatch/
├── api/                    # Flask web application
│   ├── api.py             # Main Flask app with REST endpoints
│   ├── realtime.py        # Real-time updates via PostgreSQL LISTEN/NOTIFY
│   └── templates/
│       └── index.html     # Web interface with messaging UI
│
├── data_model/            # Data models and handlers
│   ├── application_model.py    # Pydantic V2 models for business logic
│   ├── database_model.py       # SQLAlchemy ORM models
│   └── api_message_handler.py  # Message conversion & DB operations
│
├── db/                    # Database connectivity
│   └── postgres_connector.py   # PostgreSQL connection management
│
├── providers/             # External service integrations
│   └── rest_connector.py       # Twilio SMS client
│
├── utils/                 # Utilities and configuration
│   ├── logger_config.py        # Structured logging with Rich
│   └── exceptions.py           # Custom exception classes
│
└── sql/                   # Database scripts
    └── realtime_triggers.sql   # PostgreSQL triggers for real-time updates
```

## 🔄 Module Interactions

### 1. Message Flow Architecture

```
User Input → Flask API → Data Models → Database → Real-time Updates → Frontend
```

**Detailed Flow:**
1. **User sends message** via web interface
2. **Flask API** (`api.py`) receives REST request
3. **Message Handler** (`api_message_handler.py`) converts formats:
   - JSON → Pydantic models → SQLAlchemy models
4. **Database** stores message with auto-generated `conversation_id`
5. **PostgreSQL triggers** send NOTIFY event
6. **Real-time module** broadcasts to connected clients
7. **Frontend** receives SSE event and updates UI

### 2. Data Model Relationships

```
Twilio JSON ──► hatchMessage ──► Message (DB)
     │              │              │
     │              │              ▼
     │              │         conversation_id
     │              │         (generated from participants)
     │              │
     ▼              ▼
twilioSMS ────► APIMessageHandler ────► PostgreSQL
```

## 📊 Data Models

### Core Models

#### 1. **Application Models** (`application_model.py`)
- **Purpose**: Business logic and API contract definitions
- **Technology**: Pydantic V2 with field validators
- **Key Models**:
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
  
  class twilioSMS(BaseModel):
      to: str = Field(regex=r'^\+\d{10,15}$')
      from_: str = Field(alias='from', regex=r'^\+\d{10,15}$')
      body: str = Field(max_length=1600)
  ```

#### 2. **Database Models** (`database_model.py`)
- **Purpose**: ORM mapping and database schema
- **Technology**: SQLAlchemy with PostgreSQL
- **Key Features**:
  - Auto-generated UUIDs
  - Timestamp tracking
  - Conversation grouping via `conversation_id`

#### 3. **Conversation ID Generation**
- **Algorithm**: SHA256 hash of sorted participant IDs → UUID
- **Purpose**: Groups messages between same participants
- **Implementation**:
  ```python
  def generate_conversation_id(participant1: str, participant2: str) -> UUID:
      participants = sorted([participant1, participant2])
      hash_input = ''.join(participants)
      hash_digest = hashlib.sha256(hash_input.encode()).hexdigest()
      return UUID(hash_digest[:32])
  ```

## 🔌 API Endpoints

### REST API (`/api/...`)

| Endpoint | Method | Purpose | Response |
|----------|---------|---------|----------|
| `/api/conversations` | GET | List all conversations | `{conversations: [...]}` |
| `/api/conversation/<id>/messages` | GET | Get messages for conversation | `{messages: [...]}` |
| `/api/send_message` | POST | Send new message | `{success: true, message_id: "..."}` |
| `/api/events` | GET | Server-Sent Events stream | `text/event-stream` |

### Real-time Events (`/api/events`)

**Event Types:**
- `connected` - Client connected to SSE stream
- `message_update` - New/updated message in database
- `keepalive` - Connection heartbeat (every 30s)

**Event Format:**
```javascript
{
  "type": "message_update",
  "conversation_id": "uuid",
  "action": "INSERT|UPDATE|DELETE",
  "message_id": "uuid",
  "timestamp": 1234567890
}
```

## 🐳 Docker Deployment

### Quick Start with Docker Compose

The application includes a complete Docker Compose setup for easy deployment:

```bash
# Clone the repository
git clone <repository>
cd lean_hatch

# Setup environment variables
cp .env.example .env
# Edit .env with your configuration

# Setup secrets
mkdir -p .secrets
echo "your_postgres_password" > .secrets/POSTGRES_PASSWORD
echo "your_mongo_password" > .secrets/MONGO_PASSWORD
echo "your_twilio_token" > .secrets/TWILIO_AUTH_TOKEN

# Start the application
docker-compose up -d
```

### Docker Services

The `docker-compose.yaml` includes the following services:

#### **PostgreSQL Database**
```yaml
services:
  db:
    image: postgres:15
    container_name: hatchapp_postgres
    ports:
      - "5432:5432"
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD_FILE: /run/secrets/pg_password
      POSTGRES_DB: ${POSTGRES_DB}
    volumes:
      - pgdata:/var/lib/postgresql/data
    secrets:
      - pg_password
```

- **Purpose**: Primary data store for messages and conversations
- **Version**: PostgreSQL 15
- **Persistence**: Data stored in `pgdata` volume
- **Security**: Password loaded from Docker secret

#### **Available Extensions** (Commented out, enable as needed):
- **MongoDB**: Alternative NoSQL storage option
- **InfluxDB**: Time-series data and analytics
- **Nginx**: Reverse proxy and load balancing
- **Mongo Express**: MongoDB web UI

### Environment Configuration

#### **Required Environment Variables** (`.env`):
```bash
# PostgreSQL
POSTGRES_USER=hatchuser
POSTGRES_DB=hatchapp

# Application
FLASK_ENV=production
FLASK_PORT=5002

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

### Docker Network

All services run on the `hatch-network` bridge network, allowing:
- **Internal communication** between services
- **Service discovery** by container name
- **Isolated networking** from other Docker applications

### Production Deployment

#### **1. Application Dockerfile** (Create if needed):
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 5002

# Run application
CMD ["python", "api/api.py"]
```

#### **2. Update docker-compose.yaml** to include the app:
```yaml
services:
  app:
    build: .
    container_name: hatchapp_flask
    restart: always
    ports:
      - "5002:5002"
    environment:
      POSTGRES_HOST: db
      POSTGRES_PORT: 5432
    env_file:
      - .env
    secrets:
      - twilio_auth_token
    depends_on:
      - db
    networks:
      - hatch-network
```

#### **3. Database Initialization**:
```bash
# After starting containers, initialize the database
docker-compose exec app python -c "
from db.postgres_connector import hatchPostgres
pg = hatchPostgres()
pg.create_tables()
"

# Apply real-time triggers
docker-compose exec db psql -U ${POSTGRES_USER} -d ${POSTGRES_DB} -f /app/sql/realtime_triggers.sql
```

### Development with Docker

#### **Local Development Override**:
Create `docker-compose.override.yml`:
```yaml
services:
  app:
    volumes:
      - .:/app
    environment:
      FLASK_ENV: development
      FLASK_DEBUG: "1"
    command: ["python", "api/api.py"]
  
  db:
    ports:
      - "5433:5432"  # Use different port to avoid conflicts
```

#### **Development Workflow**:
```bash
# Start development environment
docker-compose -f docker-compose.yaml -f docker-compose.override.yml up

# View logs
docker-compose logs -f app

# Execute commands in container
docker-compose exec app python sample.py

# Restart specific service
docker-compose restart app
```

### Monitoring and Troubleshooting

#### **Health Checks**:
```bash
# Check service status
docker-compose ps

# View application logs
docker-compose logs app

# Check database connectivity
docker-compose exec app python -c "
from db.postgres_connector import hatchPostgres
pg = hatchPostgres()
print('Database connection:', pg.test_connection())
"
```

#### **Common Issues**:

1. **Database Connection Refused**:
   ```bash
   # Check if PostgreSQL is running
   docker-compose ps db
   
   # Check environment variables
   docker-compose exec app env | grep POSTGRES
   ```

2. **Real-time Updates Not Working**:
   ```bash
   # Verify triggers are installed
   docker-compose exec db psql -U ${POSTGRES_USER} -d ${POSTGRES_DB} -c "
   SELECT trigger_name FROM information_schema.triggers 
   WHERE trigger_name = 'messages_notify_trigger';
   "
   ```

3. **Application Won't Start**:
   ```bash
   # Check application logs
   docker-compose logs app
   
   # Restart with fresh build
   docker-compose down
   docker-compose build --no-cache
   docker-compose up
   ```

### Scaling and Production Considerations

#### **Horizontal Scaling**:
```yaml
services:
  app:
    deploy:
      replicas: 3
    ports:
      - "5002-5004:5002"  # Multiple port mappings
```

#### **Load Balancing with Nginx**:
Enable the nginx service and configure upstream servers:
```nginx
upstream hatch_app {
    server app_1:5002;
    server app_2:5002;
    server app_3:5002;
}
```

#### **Production Security**:
- Use Docker secrets for all sensitive data
- Enable SSL/TLS termination at nginx
- Implement rate limiting
- Use non-root user in Dockerfile
- Regularly update base images

## 🔧 Configuration

### Environment Variables

Create `.env` and `.secrets/.secrets` files:
```bash
# PostgreSQL Configuration
POSTGRES_USER=your_username
POSTGRES_PASSWORD=your_password
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=hatchapp

# Twilio Configuration  
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_PHONE_NUMBER=+1234567890
```

### Database Setup

1. **Install PostgreSQL** and create database
2. **Apply schema**:
   ```bash
   python3 -c "from db.postgres_connector import hatchPostgres; pg = hatchPostgres(); pg.create_tables()"
   ```
3. **Apply real-time triggers**:
   ```bash
   psql -d hatchapp -f sql/realtime_triggers.sql
   ```

## 🚀 Getting Started

### Prerequisites
- Python 3.11+
- PostgreSQL 13+
- Twilio Account (for SMS)

### Installation
```bash
# Clone and setup
git clone <repository>
cd lean_hatch
pip install -r requirements.txt

# Configure environment
cp .secrets/.secrets.example .secrets/.secrets
# Edit .secrets/.secrets with your credentials

# Setup database
python3 -c "from db.postgres_connector import hatchPostgres; pg = hatchPostgres(); pg.create_tables()"
psql -d hatchapp -f sql/realtime_triggers.sql

# Run application
cd api
python3 api.py
```

### Usage
1. **Access web interface**: http://localhost:5002
2. **View conversations**: Automatically loads from database
3. **Send messages**: 
   - Phone numbers → Twilio SMS
   - Names → Database only
4. **Real-time updates**: Messages appear instantly

## 🔍 Development Guide

### Adding New Features

#### 1. **New Message Types**
1. Add to `MessageType` enum in `application_model.py`
2. Update database schema in `database_model.py`
3. Add handler logic in `api_message_handler.py`
4. Update frontend rendering in `index.html`

#### 2. **New API Endpoints**
1. Add route in `api.py`
2. Follow existing patterns for database session management
3. Use structured logging with `logger_instance`
4. Return consistent JSON format

#### 3. **Database Changes**
1. Update SQLAlchemy models in `database_model.py`
2. Create migration script (manual for now)
3. Update Pydantic models if needed
4. Test with existing data

### Debugging

#### 1. **Logging**
- **Structured logging** with Rich formatting
- **Log levels**: DEBUG, INFO, WARNING, ERROR
- **Context**: All logs include module, function, and line number

#### 2. **Real-time Issues**
- Check PostgreSQL triggers: `SELECT * FROM information_schema.triggers WHERE trigger_name = 'messages_notify_trigger';`
- Monitor SSE connections: Look for "Added/Removed SSE client" logs
- Test notifications: `NOTIFY message_changes, '{"test": true}';`

#### 3. **Database Issues**
- Connection problems: Check `.secrets/.secrets` configuration
- Query debugging: Enable SQLAlchemy logging
- Schema issues: Verify with `\d messages` in psql

### Code Patterns

#### 1. **Database Operations**
```python
# Always use session management
session = pg.connect()
try:
    # Your database operations
    result = session.execute(text("SELECT ..."))
    session.commit()  # For modifications
finally:
    session.close()
```

#### 2. **Error Handling**
```python
try:
    # Operations
    pass
except Exception as e:
    logger_instance.error("Operation failed", error=str(e), context="additional_info")
    return jsonify({"error": str(e)}), 500
```

#### 3. **Real-time Updates**
- Database changes automatically trigger notifications
- No manual notification sending required
- SSE clients receive updates automatically

## 🧪 Testing

### Manual Testing
```bash
# Test API endpoints
curl http://localhost:5002/api/conversations
curl http://localhost:5002/api/conversation/<id>/messages

# Test SSE connection
curl -N http://localhost:5002/api/events

# Test database triggers
psql -d hatchapp -c "INSERT INTO messages (...) VALUES (...);"
```

### Integration Testing
- **Message Flow**: Send message → Check database → Verify SSE event
- **Twilio Integration**: Test with real phone numbers
- **Real-time Updates**: Multiple browser windows should sync

## 📈 Performance Considerations

### Current Optimizations
- **Connection Pooling**: SQLAlchemy handles connection reuse
- **Real-time Efficiency**: PostgreSQL LISTEN/NOTIFY (no polling)
- **Frontend Optimization**: Event-driven updates, minimal DOM manipulation

### Scaling Considerations
- **Database**: Add indexes on `conversation_id`, `timestamp`
- **Real-time**: Consider Redis pub/sub for multi-server deployments
- **Frontend**: Implement message pagination for large conversations

## 🔐 Security Notes

- **Environment Variables**: All secrets in `.secrets/.secrets`
- **SQL Injection**: Using parameterized queries with SQLAlchemy
- **Input Validation**: Pydantic models validate all inputs
- **CORS**: Currently permissive for development

## 🤝 Contributing

### Code Style
- **Python**: Follow PEP 8
- **Imports**: Absolute imports, grouped by type
- **Logging**: Use structured logging with context
- **Comments**: Document complex business logic

### Git Workflow
- **Feature branches**: `feature/description`
- **Commit messages**: Descriptive and focused
- **Pull requests**: Include tests and documentation updates

## 📚 Dependencies

### Core Dependencies
- **Flask**: Web framework and REST API
- **SQLAlchemy**: ORM and database abstraction
- **Pydantic**: Data validation and serialization
- **psycopg2**: PostgreSQL adapter
- **Twilio**: SMS service integration
- **Rich**: Enhanced logging and formatting

### Development Dependencies
- **pytest**: Testing framework
- **black**: Code formatting
- **mypy**: Type checking

## 🔄 Migration Guide

### From Polling to Real-time
- ✅ **Completed**: Removed all polling logic
- ✅ **Completed**: Implemented SSE with PostgreSQL LISTEN/NOTIFY
- ✅ **Completed**: Frontend uses EventSource for real-time updates

### From Pydantic V1 to V2
- ✅ **Completed**: Migrated `@validator` to `@field_validator`
- ✅ **Completed**: Updated `Config` classes to `model_config`
- ✅ **Completed**: Removed deprecated field configurations

---

## 📞 Support

For questions or issues:
1. Check logs in terminal output
2. Verify database connection and triggers
3. Test API endpoints individually
4. Check browser console for frontend issues

**Happy coding! 🚀**