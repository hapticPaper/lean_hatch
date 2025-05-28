#!/bin/bash

# Hatch Setup Script
# This script will guide you through setting up the Hatch messaging application

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to prompt for input with default value
prompt_with_default() {
    local prompt="$1"
    local default="$2"
    local result
    
    if [ -n "$default" ]; then
        read -p "$prompt [$default]: " result
        echo "${result:-$default}"
    else
        read -p "$prompt: " result
        echo "$result"
    fi
}

# Function to prompt for optional input (allows empty input for debugging)
prompt_optional() {
    local prompt="$1"
    local default="$2"
    local result
    
    if [ -n "$default" ]; then
        read -p "$prompt [$default] (Enter to skip): " result
        if [ -n "$result" ]; then
            echo "$result"
        elif [ -n "$default" ]; then
            echo "$default"
        else
            echo ""
        fi
    else
        read -p "$prompt (Enter to skip): " result
        echo "$result"
    fi
}

# Function to prompt for sensitive input (hidden)
prompt_hidden() {
    local prompt="$1"
    local result
    
    read -s -p "$prompt: " result
    echo ""  # New line after hidden input
    echo "$result"
}

# Function to ask yes/no question
ask_yes_no() {
    local prompt="$1"
    local default="$2"
    local result
    
    if [ "$default" = "y" ]; then
        read -p "$prompt (Y/n): " result
        case "${result:-y}" in
            [Yy]* ) return 0;;
            [Nn]* ) return 1;;
            * ) return 0;;
        esac
    else
        read -p "$prompt (y/N): " result
        case "${result:-n}" in
            [Yy]* ) return 0;;
            [Nn]* ) return 1;;
            * ) return 1;;
        esac
    fi
}

# Banner
echo -e "${BLUE}"
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║                    🚀 HATCH SETUP SCRIPT 🚀                   ║"
echo "║                                                               ║"
echo "║        Welcome to the Hatch messaging platform setup!        ║"
echo "║        This script will guide you through configuration       ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Python Environment Selection
print_step "Python Environment Setup"
echo ""
echo "Choose your Python environment setup:"
echo "1. Conda Virtual Environment (Full-featured)"
echo "2. Python venv Virtual Environment (Lightweight)"
echo "3. Host Python Installation (Not Recommended)"
echo ""
echo "💡 Virtual environments (options 1 & 2) isolate dependencies and prevent conflicts."
echo ""

ENV_CHOICE=""
while [[ "$ENV_CHOICE" != "1" && "$ENV_CHOICE" != "2" && "$ENV_CHOICE" != "3" ]]; do
    read -p "Select option (1, 2, or 3): " ENV_CHOICE
    case $ENV_CHOICE in
        1)
            USE_CONDA=true
            USE_VENV=false
            USE_HOST=false
            PYTHON_CMD="python"
            PIP_CMD="pip"
            print_success "Selected: Conda Virtual Environment"
            ;;
        2)
            USE_CONDA=false
            USE_VENV=true
            USE_HOST=false
            PYTHON_CMD="python"
            PIP_CMD="pip"
            print_success "Selected: Python venv Virtual Environment"
            ;;
        3)
            USE_CONDA=false
            USE_VENV=false
            USE_HOST=true
            PYTHON_CMD="python"
            PIP_CMD="pip"
            print_warning "Selected: Host Python (not recommended - may cause dependency conflicts)"
            ;;
        *)
            print_error "Invalid choice. Please select 1, 2, or 3."
            ;;
    esac
done

# Check prerequisites
print_step "Checking prerequisites..."

MISSING_DEPS=()

if [ "$USE_CONDA" = true ]; then
    if ! command_exists "conda"; then
        MISSING_DEPS+=("conda")
    fi
elif [ "$USE_VENV" = true ]; then
    if ! command_exists "python3"; then
        MISSING_DEPS+=("python3")
    fi
    # Check if venv module is available
    if ! python3 -c "import venv" 2>/dev/null; then
        print_error "Python venv module not found. Please install python3-venv package."
        echo "On Ubuntu/Debian: sudo apt install python3-venv"
        echo "On other systems, venv should be included with Python 3.3+"
        exit 1
    fi
elif [ "$USE_HOST" = true ]; then
    if ! command_exists "python"; then
        MISSING_DEPS+=("python")
    fi
fi

if ! command_exists "docker"; then
    MISSING_DEPS+=("docker")
fi

if ! command_exists "docker-compose"; then
    MISSING_DEPS+=("docker-compose")
fi

if [ ${#MISSING_DEPS[@]} -gt 0 ]; then
    print_error "Missing required dependencies: ${MISSING_DEPS[*]}"
    echo "Please install the missing dependencies and run this script again."
    echo ""
    echo "Installation guides:"
    if [[ " ${MISSING_DEPS[@]} " =~ " conda " ]]; then
        echo "- Conda: https://docs.conda.io/en/latest/miniconda.html"
    fi
    echo "- Python 3: https://www.python.org/downloads/"
    echo "- Docker: https://docs.docker.com/get-docker/"
    echo "- Docker Compose: https://docs.docker.com/compose/install/"
    exit 1
fi

print_success "All prerequisites found!"

# Setup Python Environment
if [ "$USE_CONDA" = true ]; then
    print_step "Setting up Conda virtual environment..."
    
    # List existing environments
    echo ""
    echo "Existing conda environments:"
    conda env list
    echo ""
    
    # Ask user to choose existing or create new
    if ask_yes_no "Do you want to use an existing conda environment?" "n"; then
        read -p "Enter the name of the existing environment: " CONDA_ENV_NAME
        
        # Verify the environment exists
        if conda env list | grep -q "^${CONDA_ENV_NAME} "; then
            print_success "Using existing conda environment: $CONDA_ENV_NAME"
        else
            print_error "Environment '$CONDA_ENV_NAME' not found!"
            echo "Available environments:"
            conda env list
            exit 1
        fi
    else
        # Create new environment
        CONDA_ENV_NAME=$(prompt_with_default "Name for new conda environment" "hatch")
        
        if conda env list | grep -q "^${CONDA_ENV_NAME} "; then
            print_warning "Environment '$CONDA_ENV_NAME' already exists. Using existing environment."
        else
            print_step "Creating conda environment '$CONDA_ENV_NAME' with Python 3.11..."
            conda create -n "$CONDA_ENV_NAME" python=3.11 -y
            print_success "Conda environment '$CONDA_ENV_NAME' created"
        fi
    fi
    
    # Activate conda environment for this script
    print_step "Activating conda environment '$CONDA_ENV_NAME'..."
    eval "$(conda shell.bash hook)"
    conda activate "$CONDA_ENV_NAME"
    print_success "Conda environment activated"
    
    echo ""
    print_warning "Remember to activate the conda environment in future sessions:"
    echo "conda activate $CONDA_ENV_NAME"
    echo ""

elif [ "$USE_VENV" = true ]; then
    print_step "Setting up Python venv virtual environment..."
    
    VENV_NAME=$(prompt_with_default "Name for venv directory" "hatch-venv")
    
    if [ -d "$VENV_NAME" ]; then
        print_warning "Virtual environment directory '$VENV_NAME' already exists."
        if ask_yes_no "Do you want to use the existing venv?" "y"; then
            print_success "Using existing venv: $VENV_NAME"
        else
            print_step "Removing existing venv and creating new one..."
            rm -rf "$VENV_NAME"
            python3 -m venv "$VENV_NAME"
            print_success "New venv created: $VENV_NAME"
        fi
    else
        print_step "Creating Python venv: $VENV_NAME"
        python3 -m venv "$VENV_NAME"
        print_success "Python venv created: $VENV_NAME"
    fi
    
    # Activate venv for this script
    print_step "Activating venv..."
    source "$VENV_NAME/bin/activate"
    print_success "Virtual environment activated"
    
    echo ""
    print_warning "Remember to activate the venv in future sessions:"
    echo "source $VENV_NAME/bin/activate"
    echo ""

elif [ "$USE_HOST" = true ]; then
    print_step "Using host Python installation..."
    print_warning "No virtual environment isolation - dependencies will be installed globally"
    echo ""
fi

# Check if we're in the right directory
if [ ! -f "docker-compose.yaml" ]; then
    print_error "docker-compose.yaml not found. Please run this script from the lean_hatch directory."
    exit 1
fi

# Read existing configuration
print_step "Reading existing configuration..."

# Initialize variables with defaults
EXISTING_POSTGRES_USER=""
EXISTING_POSTGRES_DB=""
EXISTING_FLASK_ENV=""
EXISTING_FLASK_PORT=""
EXISTING_TWILIO_ACCOUNT_SID=""
EXISTING_TWILIO_PHONE_NUMBER=""
EXISTING_SENDGRID_FROM_EMAIL=""

# Read existing .env file if it exists
if [ -f ".env" ]; then
    print_success "Found existing .env file"
    # Source the .env file to get existing values
    while IFS='=' read -r key value; do
        # Skip comments and empty lines
        [[ $key =~ ^[[:space:]]*# ]] && continue
        [[ -z "$key" ]] && continue
        
        # Remove quotes from value
        value=$(echo "$value" | sed 's/^"//;s/"$//')
        
        case "$key" in
            "POSTGRES_USER") EXISTING_POSTGRES_USER="$value" ;;
            "POSTGRES_DB") EXISTING_POSTGRES_DB="$value" ;;
            "FLASK_ENV") EXISTING_FLASK_ENV="$value" ;;
            "FLASK_PORT") EXISTING_FLASK_PORT="$value" ;;
            "TWILIO_ACCOUNT_SID") EXISTING_TWILIO_ACCOUNT_SID="$value" ;;
            "TWILIO_PHONE_NUMBER") EXISTING_TWILIO_PHONE_NUMBER="$value" ;;
            "SENDGRID_FROM_EMAIL") EXISTING_SENDGRID_FROM_EMAIL="$value" ;;
        esac
    done < .env
else
    print_warning "No existing .env file found"
fi

# Check for existing secrets
EXISTING_POSTGRES_PASSWORD=""
EXISTING_TWILIO_AUTH_TOKEN=""
EXISTING_SENDGRID_API_KEY=""

if [ -d ".secrets" ]; then
    print_success "Found existing .secrets directory"
    
    if [ -f ".secrets/POSTGRES_PASSWORD" ]; then
        EXISTING_POSTGRES_PASSWORD="***configured***"
        print_success "PostgreSQL password already configured"
    fi
    
    if [ -f ".secrets/TWILIO_AUTH_TOKEN" ] || [ -f ".secrets/TWILIO_SECRET" ]; then
        EXISTING_TWILIO_AUTH_TOKEN="***configured***"
        print_success "Twilio auth token already configured"
    fi
    
    if [ -f ".secrets/SENDGRID_API_KEY" ] || [ -f ".secrets/SENDGRID_TOKEN" ]; then
        EXISTING_SENDGRID_API_KEY="***configured***"
        print_success "SendGrid API key already configured"
    fi
else
    print_warning "No existing .secrets directory found"
fi

# Create .secrets directory if it doesn't exist
print_step "Creating .secrets directory..."
mkdir -p .secrets
print_success ".secrets directory created"

# Environment Variables Configuration
print_step "Configuring environment variables..."
echo ""
echo "Let's set up your environment configuration. You can press Enter to use default values."
echo ""

# PostgreSQL Configuration
echo -e "${YELLOW}PostgreSQL Database Configuration:${NC}"
POSTGRES_USER=$(prompt_with_default "PostgreSQL username" "${EXISTING_POSTGRES_USER:-hatchuser}")
POSTGRES_DB=$(prompt_with_default "PostgreSQL database name" "${EXISTING_POSTGRES_DB:-hatchapp}")

if [ -n "$EXISTING_POSTGRES_PASSWORD" ]; then
    echo "PostgreSQL password: $EXISTING_POSTGRES_PASSWORD (already configured)"
    if ask_yes_no "Do you want to update the PostgreSQL password?" "n"; then
        POSTGRES_PASSWORD=$(prompt_hidden "New PostgreSQL password")
        if [ -z "$POSTGRES_PASSWORD" ]; then
            print_warning "Empty password entered, keeping existing password"
            POSTGRES_PASSWORD="keep_existing"
        fi
    else
        POSTGRES_PASSWORD="keep_existing"
    fi
else
    POSTGRES_PASSWORD=$(prompt_hidden "PostgreSQL password (will be stored securely)")
    if [ -z "$POSTGRES_PASSWORD" ]; then
        print_error "PostgreSQL password is required"
        exit 1
    fi
fi

# Flask Configuration
echo ""
echo -e "${YELLOW}Flask Application Configuration:${NC}"
FLASK_ENV=$(prompt_with_default "Flask environment (development/production)" "${EXISTING_FLASK_ENV:-development}")
FLASK_PORT=$(prompt_with_default "Flask port" "${EXISTING_FLASK_PORT:-5002}")

# Twilio Configuration
echo ""
echo -e "${YELLOW}Twilio SMS Configuration:${NC}"
echo "You can get these from your Twilio Console: https://console.twilio.com/"
TWILIO_ACCOUNT_SID=$(prompt_with_default "Twilio Account SID" "${EXISTING_TWILIO_ACCOUNT_SID}")

if [ -n "$EXISTING_TWILIO_AUTH_TOKEN" ]; then
    echo "Twilio Auth Token: $EXISTING_TWILIO_AUTH_TOKEN (already configured)"
    if ask_yes_no "Do you want to update the Twilio Auth Token?" "n"; then
        TWILIO_AUTH_TOKEN=$(prompt_hidden "New Twilio Auth Token")
        if [ -z "$TWILIO_AUTH_TOKEN" ]; then
            print_warning "Empty token entered, keeping existing token"
            TWILIO_AUTH_TOKEN="keep_existing"
        fi
    else
        TWILIO_AUTH_TOKEN="keep_existing"
    fi
else
    TWILIO_AUTH_TOKEN=$(prompt_hidden "Twilio Auth Token")
fi

TWILIO_PHONE_NUMBER=$(prompt_with_default "Twilio Phone Number (with +)" "${EXISTING_TWILIO_PHONE_NUMBER}")

# SendGrid Configuration
echo ""
echo -e "${YELLOW}SendGrid Email Configuration:${NC}"
echo "You can get your API key from: https://app.sendgrid.com/settings/api_keys"

if [ -n "$EXISTING_SENDGRID_API_KEY" ]; then
    echo "SendGrid API Key: $EXISTING_SENDGRID_API_KEY (already configured)"
    if ask_yes_no "Do you want to update the SendGrid API Key?" "n"; then
        SENDGRID_API_KEY=$(prompt_hidden "New SendGrid API Key")
        if [ -z "$SENDGRID_API_KEY" ]; then
            print_warning "Empty API key entered, keeping existing key"
            SENDGRID_API_KEY="keep_existing"
        fi
    else
        SENDGRID_API_KEY="keep_existing"
    fi
else
    SENDGRID_API_KEY=$(prompt_hidden "SendGrid API Key")
fi

SENDGRID_FROM_EMAIL=$(prompt_with_default "SendGrid verified sender email" "${EXISTING_SENDGRID_FROM_EMAIL}")

if [ -z "$SENDGRID_FROM_EMAIL" ]; then
    print_warning "SendGrid sender email is required for email functionality"
fi

# Create .env file
print_step "Creating .env file..."
cat > .env << EOF
# PostgreSQL Configuration
POSTGRES_USER=$POSTGRES_USER
POSTGRES_DB=$POSTGRES_DB
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

# Flask Configuration
FLASK_ENV=$FLASK_ENV
FLASK_PORT=$FLASK_PORT

# Twilio Configuration
TWILIO_ACCOUNT_SID=$TWILIO_ACCOUNT_SID
TWILIO_PHONE_NUMBER=$TWILIO_PHONE_NUMBER

# SendGrid Configuration
SENDGRID_FROM_EMAIL=$SENDGRID_FROM_EMAIL

# Optional services (for Docker Compose)
MONGO_USER=hatchuser
INFLUXDB_USER=hatchuser
INFLUXDB_ORGANIZATION=hatch
INFLUXDB_BUCKET=messages
EOF

print_success ".env file created"

# Create secrets files
print_step "Creating secrets files..."

# Handle PostgreSQL password
if [ "$POSTGRES_PASSWORD" != "keep_existing" ]; then
    echo "$POSTGRES_PASSWORD" > .secrets/POSTGRES_PASSWORD
    print_success "PostgreSQL password updated"
elif [ ! -f ".secrets/POSTGRES_PASSWORD" ]; then
    print_error "No existing PostgreSQL password found and no new password provided"
    exit 1
fi

# Handle Twilio auth token
if [ -n "$TWILIO_AUTH_TOKEN" ] && [ "$TWILIO_AUTH_TOKEN" != "keep_existing" ]; then
    echo "$TWILIO_AUTH_TOKEN" > .secrets/TWILIO_AUTH_TOKEN
    print_success "Twilio auth token updated"
elif [ "$TWILIO_AUTH_TOKEN" = "keep_existing" ]; then
    # Check if we have existing token in either location
    if [ ! -f ".secrets/TWILIO_AUTH_TOKEN" ] && [ ! -f ".secrets/TWILIO_SECRET" ]; then
        print_warning "No existing Twilio auth token found"
    fi
elif [ -n "$TWILIO_AUTH_TOKEN" ]; then
    echo "$TWILIO_AUTH_TOKEN" > .secrets/TWILIO_AUTH_TOKEN
    print_success "Twilio auth token created"
fi

# Handle SendGrid API key
if [ -n "$SENDGRID_API_KEY" ] && [ "$SENDGRID_API_KEY" != "keep_existing" ]; then
    echo "$SENDGRID_API_KEY" > .secrets/SENDGRID_API_KEY
    print_success "SendGrid API key updated"
elif [ "$SENDGRID_API_KEY" = "keep_existing" ]; then
    # Check if we have existing key in either location
    if [ ! -f ".secrets/SENDGRID_API_KEY" ] && [ ! -f ".secrets/SENDGRID_TOKEN" ]; then
        print_warning "No existing SendGrid API key found"
    fi
elif [ -n "$SENDGRID_API_KEY" ]; then
    echo "$SENDGRID_API_KEY" > .secrets/SENDGRID_API_KEY
    print_success "SendGrid API key created"
fi

# Create placeholder files for optional services only if they don't exist
if [ ! -f ".secrets/MONGO_PASSWORD" ]; then
    echo "changeme" > .secrets/MONGO_PASSWORD
fi
if [ ! -f ".secrets/INFLUX_TOKEN" ]; then
    echo "changeme" > .secrets/INFLUX_TOKEN
fi
if [ ! -f ".secrets/INFLUXDB_PASSWORD" ]; then
    echo "changeme" > .secrets/INFLUXDB_PASSWORD
fi

print_success "Secrets files processed"

# Set proper permissions for secrets
chmod 600 .secrets/*
print_success "Secrets file permissions set"

# Install Python dependencies
print_step "Installing Python dependencies..."
if [ -f "requirements.txt" ]; then
    if [ "$USE_CONDA" = true ]; then
        print_step "Installing dependencies in conda environment..."
        $PIP_CMD install -r requirements.txt
    elif [ "$USE_VENV" = true ]; then
        print_step "Installing dependencies in venv..."
        $PIP_CMD install -r requirements.txt
    else
        print_warning "Installing dependencies globally (not recommended - may cause conflicts)"
        $PIP_CMD install -r requirements.txt
    fi
    print_success "Python dependencies installed"
else
    print_warning "requirements.txt not found, skipping Python dependency installation"
fi

# Ask about database setup
echo ""
if ask_yes_no "Do you want to start the PostgreSQL database container?" "y"; then
    print_step "Starting PostgreSQL database container..."
    docker-compose up -d db
    
    # Wait for database to be ready
    print_step "Waiting for database to be ready..."
    sleep 10
    
    # Create tables and test database connection
    print_step "Creating database tables and testing connection..."
    if PYTHONPATH=. $PYTHON_CMD -m db.postgres_connector; then
        print_success "Database tables created and connection verified"
    else
        print_error "Failed to create tables or connect to database"
        exit 1
    fi
    
    # Apply triggers
    if [ -f "sql/realtime_triggers.sql" ]; then
        print_step "Applying real-time triggers..."
        docker-compose exec -T db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" < sql/realtime_triggers.sql
        print_success "Real-time triggers applied"
    fi
    
    print_success "Database setup complete"
fi

# Ask about starting the application
echo ""
if ask_yes_no "Do you want to start the Python server?" "y"; then
    print_step "Starting Hatch application..."
    
    # Start the server in the background
    cd api
    if [ "$USE_CONDA" = true ]; then
        # Ensure conda environment is still activated
        eval "$(conda shell.bash hook)"
        conda activate "$CONDA_ENV_NAME"
    elif [ "$USE_VENV" = true ]; then
        # Ensure venv is still activated
        source "../$VENV_NAME/bin/activate"
    fi
    $PYTHON_CMD api.py &
    SERVER_PID=$!
    cd ..
    
    # Wait a moment for server to start
    sleep 3
    
    # Check if server is running
    if kill -0 $SERVER_PID 2>/dev/null; then
        print_success "Hatch server started successfully (PID: $SERVER_PID)"
        
        # Ask about opening browser
        if ask_yes_no "Do you want to open the web interface?" "y"; then
            if command_exists "open"; then
                # macOS
                open "http://localhost:$FLASK_PORT"
            elif command_exists "xdg-open"; then
                # Linux
                xdg-open "http://localhost:$FLASK_PORT"
            elif command_exists "start"; then
                # Windows (Git Bash)
                start "http://localhost:$FLASK_PORT"
            else
                echo "Please open http://localhost:$FLASK_PORT in your browser"
            fi
            print_success "Web interface should open in your browser"
        fi
        
        echo ""
        echo -e "${GREEN}🎉 Setup complete! 🎉${NC}"
        echo ""
        echo "Your Hatch application is now running!"
        echo ""
        echo "📱 Web Interface: http://localhost:$FLASK_PORT"
        echo "📧 Email composer: Click 'Compose Email' in the sidebar"
        echo "💬 Real-time messaging: Send messages to see live updates"
        echo ""
        if [ "$USE_CONDA" = true ]; then
            echo "🐍 Conda Environment: '$CONDA_ENV_NAME' (activate with 'conda activate $CONDA_ENV_NAME')"
            echo ""
        elif [ "$USE_VENV" = true ]; then
            echo "🐍 Python venv: '$VENV_NAME' (activate with 'source $VENV_NAME/bin/activate')"
            echo ""
        elif [ "$USE_HOST" = true ]; then
            echo "⚠️  Using host Python (no virtual environment)"
            echo ""
        fi
        echo "To stop the server, press Ctrl+C or run: kill $SERVER_PID"
        echo "To stop the database: docker-compose down"
        echo ""
        echo "Happy messaging! 🚀"
        
        # Keep script running so server stays alive
        echo "Press Ctrl+C to stop the server..."
        wait $SERVER_PID
        
    else
        print_error "Failed to start Hatch server"
        exit 1
    fi
else
    echo ""
    echo -e "${GREEN}Setup complete!${NC}"
    echo ""
    echo "To start the application manually:"
    echo "1. Start database: docker-compose up -d db"
    if [ "$USE_CONDA" = true ]; then
        echo "2. Activate conda environment: conda activate $CONDA_ENV_NAME"
        echo "3. Start server: cd api && $PYTHON_CMD api.py"
        echo "4. Open browser: http://localhost:$FLASK_PORT"
    elif [ "$USE_VENV" = true ]; then
        echo "2. Activate venv: source $VENV_NAME/bin/activate"
        echo "3. Start server: cd api && $PYTHON_CMD api.py"
        echo "4. Open browser: http://localhost:$FLASK_PORT"
    else
        echo "2. Start server: cd api && $PYTHON_CMD api.py"
        echo "3. Open browser: http://localhost:$FLASK_PORT"
    fi
    echo ""
    echo "Happy messaging! 🚀"
fi
