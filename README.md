# Hatch - Real-time Messaging Service

A comprehensive messaging service application built with Python, Flask, PostgreSQL, Twilio SMS integration, and SendGrid email functionality. Features real-time updates, structured logging, a modern web interface, and email composition with countdown timers.

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
                               │
                               ▼
                       ┌──────────────┐
                       │   SendGrid   │
                       │   Email API  │
                       └──────────────┘
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
├── setup.sh               # 🚀 Automated setup script (recommended!)
├── api/                    # Flask web application
│   ├── api.py             # Main Flask app with REST endpoints
│   ├── realtime.py        # Real-time updates via PostgreSQL LISTEN/NOTIFY
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
├── tests/                 # Test files and templates
│   ├── html_email_compatible.html  # Email-client-compatible template
│   └── test_email_system.py       # Email system test script
│
└── sql/                   # Database scripts
    └── realtime_triggers.sql   # PostgreSQL triggers for real-time updates
```


## 🚀 Getting Started

### ⚡ Quick Setup with Automated Setup Script (Recommended)

The **easiest and fastest** way to get started is using our comprehensive automated setup script. The script handles everything from dependency checking to application startup with **zero manual configuration required**:

```bash
# Clone the repository
git clone <repository>
cd lean_hatch

# Make the setup script executable (if needed)
chmod +x setup.sh

# Run the automated setup script
./setup.sh
```

**✨ The setup script is a complete solution that:**
-  **Detects your system** and guides you through optimal configuration choices
-  **Handles all dependencies** including Python environments, Docker, and packages
-  **Manages secrets securely** with file-based encryption and proper permissions
-  **Sets up databases** with automatic table creation and real-time triggers
-  **Starts your application** and opens it in your browser automatically
-  **Tests everything** to ensure your installation works correctly

#### 🎯 What the Setup Script Does

The setup script provides a **complete guided installation** with the following features:

**1. Environment Setup Options:**
- **🐍 Conda Virtual Environment** (Recommended for data science workflows)
  - Lists existing environments and allows reuse
  - Creates new environments with Python 3.11+
  - Automatic activation and dependency management
- **🐍 Python venv Virtual Environment** (Lightweight, built-in)
  - Creates isolated virtual environments with custom names
  - Built-in Python module, no additional installation required
- **⚠️ Host Python Installation** (Not recommended, but available)
  - Direct installation to system Python for quick testing

**2. Smart Prerequisite Checking:**
- **Python 3.11+** installation verification
- **Docker and Docker Compose** availability testing
- **Virtual environment modules** (venv/conda) validation
- **Helpful installation guides** for missing dependencies with direct links
- **Platform detection** (macOS, Linux, Windows Git Bash support)

**3. Intelligent Python Environment Management:**
-  **Conda**: Lists existing environments, option to reuse or create new
-  **venv**: Creates isolated virtual environment with custom name
-  **Dependencies**: Automatically installs all required Python packages from `requirements.txt`
-  **Activation guidance**: Clear instructions for future sessions

**4. Interactive Configuration with Smart Defaults:**
- 🔧 **PostgreSQL**: Database credentials and connection settings
  - Default user: `hatchuser`, database: `hatchapp`
  - Secure password prompting with hidden input
  - Existing configuration detection and preservation
- 📱 **Twilio SMS**: Account SID, Auth Token, and phone number
  - Direct links to Twilio Console for easy credential retrieval
  - Secure token storage with masked display
- 📧 **SendGrid Email**: API key and verified sender email
  - Direct links to SendGrid API key management
  - Validation prompts for required fields
- 🔐 **Secrets Management**: Automatically creates `.env` and `.secrets/` files
  - Proper file permissions (600) for security
  - Smart credential update handling (keeps existing vs. updates)

**5. Comprehensive Database Setup:**
- **Docker Compose**: Optional PostgreSQL container startup
- **Schema Creation**: Automatic table creation for messages and emails
- **Real-time Triggers**: PostgreSQL triggers for live updates via LISTEN/NOTIFY
- **Connection Testing**: Verifies database connectivity and table creation
- **Migration Support**: Handles existing databases gracefully

**6. Complete Application Startup:**
- **Flask Server**: Optional automatic server startup in background
- **Browser Launch**: Cross-platform browser opening (macOS/Linux/Windows)
- **Usage Instructions**: Clear next steps and usage guidance
- **Process Management**: Server PID tracking for easy shutdown

#### 🎮 Interactive Setup Experience

The script provides a **user-friendly interactive experience** with colored output and helpful guidance:

```bash
╔═══════════════════════════════════════════════════════════════╗
║                    🚀 HATCH SETUP SCRIPT 🚀                   ║
║                                                               ║
║        Welcome to the Hatch messaging platform setup!        ║
║        This script will guide you through configuration       ║
╚═══════════════════════════════════════════════════════════════╝

[STEP] Python Environment Setup

Choose your Python environment setup:
1. Conda Virtual Environment (Full-featured)
2. Python venv Virtual Environment (Lightweight)  
3. Host Python Installation (Not Recommended)

💡 Virtual environments (options 1 & 2) isolate dependencies and prevent conflicts.

Select option (1, 2, or 3): 2
[SUCCESS] Selected: Python venv Virtual Environment

[STEP] Checking prerequisites...
[SUCCESS] All prerequisites found!

[STEP] Setting up Python venv virtual environment...
Name for venv directory [hatch-venv]: 
[SUCCESS] Python venv created: hatch-venv
[SUCCESS] Virtual environment activated

[WARNING] Remember to activate the venv in future sessions:
source hatch-venv/bin/activate

[STEP] Configuring environment variables...

PostgreSQL Database Configuration:
PostgreSQL username [hatchuser]: 
PostgreSQL database name [hatchapp]: 
PostgreSQL password (will be stored securely): ********

Flask Application Configuration:
Flask environment (development/production) [development]: 
Flask port [5002]: 

Twilio SMS Configuration:
You can get these from your Twilio Console: https://console.twilio.com/
Twilio Account SID: AC1234567890abcdef1234567890abcdef
Twilio Auth Token: ********************************
Twilio Phone Number (with +): +1234567890

SendGrid Email Configuration:
You can get your API key from: https://app.sendgrid.com/settings/api_keys
SendGrid API Key: ****************************************
SendGrid verified sender email: your-email@domain.com

[SUCCESS] .env file created
[SUCCESS] Secrets files processed
[SUCCESS] Secrets file permissions set

[STEP] Installing Python dependencies...
[SUCCESS] Python dependencies installed

Do you want to start the PostgreSQL database container? (Y/n): y
[STEP] Starting PostgreSQL database container...
[STEP] Waiting for database to be ready...
[STEP] Creating database tables and testing connection...
[SUCCESS] Database tables created and connection verified
[STEP] Applying real-time triggers...
[SUCCESS] Real-time triggers applied
[SUCCESS] Database setup complete

Do you want to start the Python server? (Y/n): y
[STEP] Starting Hatch application...
[SUCCESS] Hatch server started successfully (PID: 12345)

Do you want to open the web interface? (Y/n): y
[SUCCESS] Web interface should open in your browser

🎉 Setup complete! 🎉

Your Hatch application is now running!

📱 Web Interface: http://localhost:5002
📧 Email composer: Click 'Compose Email' in the sidebar
💬 Real-time messaging: Send messages to see live updates

🐍 Python venv: 'hatch-venv' (activate with 'source hatch-venv/bin/activate')

To stop the server, press Ctrl+C or run: kill 12345
To stop the database: docker-compose down

Happy messaging! 🚀
```

**Key Interactive Features:**
- **Colored Output**: Green for success, yellow for warnings, red for errors, blue for steps
- **Smart Defaults**: Sensible defaults in brackets, just press Enter to accept
- **Secure Input**: Password and token input is hidden from terminal display
- **Existing Config Detection**: Automatically detects and offers to reuse existing configurations
- **Yes/No Prompts**: Clear (Y/n) prompts with default selections
- *Process Tracking**: Shows server PID for easy management
- **Cross-Platform Browser Opening**: Works on macOS, Linux, and Windows Git Bash


### 🔄 After Setup Completion

Once the setup script completes, you'll have:

- ** Working Application**: Running at `http://localhost:5002`
- ** Database**: PostgreSQL with tables and triggers
- ** Dependencies**: All Python packages installed in virtual environment
- ** Configuration**: Environment variables and secrets properly set
- ** Real-time Features**: Live message updates enabled

#### 📱 Using the Application

**Web Interface**: `http://localhost:5002`
- View message conversations
- Send SMS messages (via Twilio)
- Send emails (via SendGrid)
- Real-time message updates
- Modern, responsive design

**API Endpoints**: `http://localhost:5002/api/`
- RESTful API for all messaging functions
- Server-Sent Events for real-time updates
- JSON responses for easy integration

## 🔄 Module Interactions

### 1. Message Flow Architecture

```
User Input → Flask API → Data Models → Database → Real-time Updates → Frontend
```

**Detailed Flow:**
1. **User sends message/email** via web interface
2. **Flask API** (`api.py`) receives REST request
3. **Message Handler** (`api_message_handler.py`) converts formats:
   - JSON → Pydantic models → SQLAlchemy models
4. **Database** stores message/email with auto-generated `conversation_id`
5. **PostgreSQL triggers** send NOTIFY event (messages only)
6. **Real-time module** broadcasts to connected clients (messages only)
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

### 3. Email System Architecture

```
Email Composer ──► SendGrid API ──► EmailMessage ──► Email (DB)
     │                    │             │             │
     │                    │             │             ▼
     │                    │             │        email_id
     │                    │             │        (UUID)
     │                    │             │
     ▼                    ▼             ▼
Email Modal ────► Flask API ────► SendGrid Connector ────► PostgreSQL
```

**Email Flow:**
1. **User opens email composer** via modal popup
2. **Email form submission** sends data to `/api/send_email`
3. **APIMessageHandler** processes email request
4. **SendGrid Connector** sends email via SendGrid API
5. **Database** stores email record with provider response
6. **Success/Error feedback** displayed with countdown timer
7. **Modal auto-closes** after 5-second countdown

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
- **Purpose**: ORM mapping and database schema
- **Technology**: SQLAlchemy with PostgreSQL
- **Key Features**:
  - Auto-generated UUIDs
  - Timestamp tracking
  - Conversation grouping via `conversation_id` (messages)
  - Separate tables for messages and emails
  - Provider-specific fields for external service responses

**Tables:**
- `messages` - SMS/chat messages with conversation grouping
- `emails` - Email records with SendGrid integration

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
| `/api/send_email` | POST | Send email via SendGrid | `{success: true, email_id: "..."}` |
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

## 📧 Email System

### Email Composer Modal

The application includes a modern email composer accessible via a modal popup:

**Features:**
- **Modal Interface**: Clean popup overlay with form fields
- **Real-time Validation**: Email format validation
- **Success Feedback**: Visual confirmation with countdown timer
- **Auto-close**: Modal automatically closes 5 seconds after success
- **Error Handling**: Clear error messages for failed sends

**Usage:**
1. Click the "Compose Email" button in the sidebar
2. Fill in recipient email, subject, and message body
3. Click "Send Email" to submit
4. Watch the countdown timer and automatic modal closure

### Email API

**Send Email Endpoint:**
```http
POST /api/send_email
Content-Type: application/json

{
  "to_email": "recipient@example.com",
  "subject": "Your Subject",
  "body": "Your message content"
}
```

**Response Format:**
```json
{
  "success": true,
  "email_id": "uuid-here",
  "message": "Email sent successfully"
}
```

**Error Response:**
```json
{
  "success": false,
  "error": "Error description"
}
```

### Email Templates


**Template Location**: `tests/html_email_compatible.html`

### SendGrid Integration

**Provider Configuration:**
- **Service**: SendGrid API v3
- **Authentication**: API key via environment variables
- **Templates**: HTML template injection
- **Response Tracking**: Provider responses stored in database

**Database Storage:**
- **Separate Table**: Emails stored in dedicated `emails` table
- **Provider Data**: SendGrid message IDs and responses saved
- **Metadata**: CC, BCC, reply-to, attachments support

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
EXPOSE 5000

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
      - "5000:5000"
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

4. **Setup Script Issues**:
   ```bash
   # Make sure script is executable
   chmod +x setup.sh
   
   # Run with bash explicitly
   bash setup.sh
   
   # Check prerequisites
   python3 --version
   docker --version
   docker-compose --version
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

# SendGrid Configuration
SENDGRID_API_KEY=your_sendgrid_api_key
SENDGRID_FROM_EMAIL=your_verified_sender@example.com
```

### Database Setup

1. **Install PostgreSQL** and create database
2. **Apply schema**:
   ```bash
   python3 -c "from db.postgres_connector import hatchPostgres; pg = hatchPostgres(); pg.create_tables()"
   ```
   This creates both `messages` and `emails` tables
3. **Apply real-time triggers**:
   ```bash
   psql -d hatchapp -f sql/realtime_triggers.sql
   ```

#### 🔧 Configuration Options

The setup script intelligently handles configuration:

**Smart Defaults:**
- Database: `localhost:5432` with user `hatchuser`
- Application: `localhost:5002` with development mode
- Secrets: Secure file-based storage in `.secrets/` directory

**Optional Services:**
- Docker PostgreSQL container (if you don't have PostgreSQL installed)
- Automatic browser opening
- Development vs. production mode selection

**Credential Validation:**
- Tests database connections
- Validates Twilio credentials
- Verifies SendGrid API key

#### 🛠️ Troubleshooting Setup Issues

If you encounter issues with the setup script:

```bash
# Make sure the script is executable
chmod +x setup.sh

# Run with bash explicitly if needed
bash setup.sh

# Check prerequisites manually
python3 --version    # Should be 3.11+
docker --version     # Should be 20.0+
docker-compose --version  # Should be 1.25+

# For conda users, ensure conda is in PATH
conda --version

# For venv users, ensure python3-venv is installed
python3 -c "import venv"  # Should not error
```

**Common Solutions:**
- **Permission Denied**: `chmod +x setup.sh`
- **Python Not Found**: Install Python 3.11+ or update PATH
- **Docker Issues**: Start Docker Desktop or Docker daemon
- **Virtual Environment Issues**: Install `python3-venv` package
- **Network Issues**: Check firewall settings for Docker

### 🛠️ Manual Setup (Advanced Users)

If you prefer manual setup or need custom configuration:

### Manual Setup

If you prefer to set up manually:

#### Prerequisites
- Python 3.11+
- PostgreSQL 13+
- Twilio Account (for SMS)
- SendGrid Account (for Email)

#### Installation
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
1. **Access web interface**: http://localhost:5000
2. **View conversations**: Automatically loads from database
3. **Send messages**: 
   - Phone numbers → Twilio SMS
   - Names → Database only
4. **Send emails**: Click "Compose Email" button for modal popup
5. **Real-time updates**: Messages appear instantly (emails stored separately)

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

# Test email endpoint
curl -X POST http://localhost:5002/api/send_email \
  -H "Content-Type: application/json" \
  -d '{"to_email": "test@example.com", "subject": "Test", "body": "Test message"}'

# Test SSE connection
curl -N http://localhost:5002/api/events

# Test database triggers
psql -d hatchapp -c "INSERT INTO messages (...) VALUES (...);"

# Test email system
python3 tests/test_email_system.py
```

### Integration Testing
- **Message Flow**: Send message → Check database → Verify SSE event
- **Email Flow**: Send email → Check SendGrid response → Verify database storage
- **Twilio Integration**: Test with real phone numbers
- **SendGrid Integration**: Test with verified sender addresses
- **Real-time Updates**: Multiple browser windows should sync (messages only)
- **Email Modal**: Test countdown timer and auto-close functionality

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


## 📚 Dependencies

### Core Dependencies
- **Flask**: Web framework and REST API
- **SQLAlchemy**: ORM and database abstraction
- **Pydantic**: Data validation and serialization
- **psycopg2**: PostgreSQL adapter
- **Twilio**: SMS service integration
- **SendGrid**: Email service integration
- **Rich**: Enhanced logging and formatting


---

## 📧 Email Feature Details

### Email vs Message Separation

The application maintains clear separation between messaging and email functionality:

**Messages Table:**
- SMS and chat messages
- Conversation grouping via `conversation_id`
- Real-time updates via PostgreSQL triggers
- Twilio integration for SMS delivery

**Emails Table:**
- Email records with full metadata
- SendGrid integration for delivery
- No real-time updates (separate workflow)
- Provider response tracking

### Email Client Compatibility

**Technical Implementation:**
- Event-driven JavaScript
- Fetch API for form submission

### SendGrid Integration Notes

**API Usage:**
- SendGrid API v3 for email delivery
- Content object structure for HTML emails
- Response tracking and error handling

**Database Storage:**
- External message IDs from SendGrid
- Provider response data preservation
- Send status and timestamp tracking
- Support for CC, BCC, reply-to, attachments

### Email Development Tips

1. **Template Updates**: Modify `tests/html_email_compatible.html`
2. **Modal Styling**: Update CSS in `templates/index.html`
3. **API Integration**: Extend `sendgrid_email_connector.py`
4. **Database Schema**: Add fields to `dbEmail` in `database_model.py`
5. **Error Handling**: Update response processing in `api_message_handler.py`

## 📞 Support

For questions or issues:
1. Check logs in terminal output
2. Verify database connection and triggers
3. Test API endpoints individually
4. Check browser console for frontend issues
5. **For emails**: Verify SendGrid API key and sender verification
6. **For modal issues**: Check browser developer tools for JavaScript errors

**Happy coding! 🚀**
