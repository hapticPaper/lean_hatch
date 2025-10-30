# Hatch Messaging Service

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

**NEW:** Also includes an ETL utility package for schema-driven data transformation and parquet export with BigQuery compatibility.

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
├── etl/                   # ETL utility package (NEW)
│   ├── __init__.py        # Package exports
│   ├── schema_loader.py   # JSON schema loading with pydantic
│   ├── sql_types.py       # SQL type definitions and handlers
│   ├── data_caster.py     # Type casting and validation
│   ├── parquet_exporter.py # Parquet export with BigQuery compatibility
│   ├── examples/          # Example schema definitions
│   └── README.md          # ETL utility documentation
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
    ├── etl/               # ETL utility tests
    └── ...                # Other test files
    
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

#### **Required Secrets** (`.secrets/.secrets`):
```bash
TWILIO_SECRET = ""
TWILIO_TEST_SECRET = ""
POSTGRES_PASSWORD=
MONGO_PASSWORD=
INFLUXDB_TOKEN = ""
SENDGRID_TOKEN=""
```



## ETL Utility Package

lean_hatch now includes a powerful ETL utility package for data transformation and export operations.

### Features

- **Schema-driven data validation** using JSON and pydantic
- **SQL type support** (STRING, INTEGER, FLOAT, TIMESTAMP, BOOLEAN, etc.)
- **Parquet export** with BigQuery compatibility
- **Consistent timestamp handling** across pandas, parquet, and SQL
- **Structured logging** support

### Quick Example

```python
from etl import SchemaLoader, DataCaster, ParquetExporter
import pandas as pd

# Load schema from JSON
schema = SchemaLoader.load_from_file('schema.json')

# Cast your data to match the schema
caster = DataCaster(schema)
df = pd.DataFrame(your_data)
casted_df = caster.cast_dataframe(df)

# Export to parquet (BigQuery-ready)
exporter = ParquetExporter(schema)
exporter.export_dataframe(casted_df, 'output.parquet')
```

### Schema Example

```json
{
  "name": "customer_data",
  "columns": [
    {"name": "customer_id", "type": "INTEGER", "mode": "REQUIRED"},
    {"name": "name", "type": "STRING", "mode": "NULLABLE"},
    {"name": "signup_date", "type": "TIMESTAMP", "mode": "REQUIRED"},
    {"name": "is_active", "type": "BOOLEAN", "mode": "NULLABLE"}
  ]
}
```

For complete documentation, see [etl/README.md](etl/README.md).

### Testing the ETL Utility

```bash
python -m pytest tests/etl/test_etl_utility.py -v
```


### Fronted as api testing:
1. **Access web interface**: http://localhost:5000
2. **View conversations**: Automatically loads from database
3. **Send messages**: 
   - Phone numbers → Twilio SMS
   - Names → Database only
4. **Send emails**: Click "Compose Email" button for modal popup
