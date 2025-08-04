#!/bin/bash

# JIA (Jira Intelligent Agent) Linux/macOS Setup Script
# ====================================================
# This script automates the setup process for Unix-like systems

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Function to print colored output
print_color() {
    printf "${1}${2}${NC}\n"
}

print_step() {
    echo
    print_color $PURPLE "========================================"
    print_color $PURPLE "STEP $1: $2"
    print_color $PURPLE "========================================"
}

print_success() {
    print_color $GREEN "✓ $1"
}

print_warning() {
    print_color $YELLOW "⚠️  $1"
}

print_error() {
    print_color $RED "❌ $1"
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

echo
print_color $PURPLE "🚀 JIA (Jira Intelligent Agent) Setup Script"
print_color $CYAN "This script will set up the JIA project on your system"
echo

# Step 1: Check Python version
print_step 1 "Checking Python Version"

if ! command_exists python3; then
    print_error "Python 3 is not installed"
    echo "Please install Python 3.8 or higher"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
REQUIRED_VERSION="3.8"

if ! python3 -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)"; then
    print_error "Python 3.8 or higher is required"
    print_color $RED "Current version: $PYTHON_VERSION"
    exit 1
fi

print_success "Python $PYTHON_VERSION is compatible"

# Step 2: Create virtual environment
print_step 2 "Creating Virtual Environment"

if [ -d "venv" ]; then
    print_warning "Virtual environment already exists"
else
    python3 -m venv venv
    print_success "Virtual environment created"
fi

# Step 3: Activate virtual environment and install dependencies
print_step 3 "Installing Dependencies"

source venv/bin/activate

print_color $BLUE "Upgrading pip..."
pip install --upgrade pip

if [ -f "requirements.txt" ]; then
    print_color $BLUE "Installing dependencies from requirements.txt..."
    pip install -r requirements.txt
    print_success "Dependencies installed from requirements.txt"
else
    print_warning "requirements.txt not found, installing basic dependencies"
    pip install Flask>=2.3.0 Flask-SQLAlchemy>=3.0.0 Flask-Migrate>=4.0.0 Flask-Login>=0.6.0 bcrypt>=4.0.0 python-dotenv>=1.0.0 cryptography>=41.0.0
    print_success "Basic dependencies installed"
fi

# Step 4: Setup environment file
print_step 4 "Setting up Environment Configuration"

if [ -f ".env" ]; then
    print_warning ".env file already exists"
else
    if [ -f ".env.example" ]; then
        cp .env.example .env
        print_success ".env file created from template"
    else
        print_color $BLUE "Creating basic .env file..."
        cat > .env << EOF
# JIA Configuration
FLASK_APP=jia.py
FLASK_ENV=development
SECRET_KEY=your-secret-key-change-this-in-production
DATABASE_URL=sqlite:///instance/jia-dev.db

# MCP Configuration
MCP_SERVER_URL=
DEFAULT_JIRA_URL=
DEFAULT_CONFLUENCE_URL=

# AI Configuration
AI_API_URL=
AI_API_KEY=

# Security
ENCRYPTION_KEY=generate-a-secure-key-here
EOF
        print_success "Basic .env file created"
    fi
fi

print_warning "Please edit .env file with your actual configuration values"

# Step 5: Setup database
print_step 5 "Setting up Database"

mkdir -p instance

if [ -f "manage_db.py" ]; then
    print_color $BLUE "Initializing database..."
    python manage_db.py
    print_success "Database initialized"
else
    print_warning "manage_db.py not found, skipping database initialization"
fi

if [ -d "migrations" ]; then
    print_color $BLUE "Running database migrations..."
    python -m flask db upgrade
    print_success "Database migrations completed"
fi

# Step 6: Create admin user
print_step 6 "Creating Admin User"

if [ -f "create_admin.py" ]; then
    print_color $BLUE "Creating admin user..."
    python create_admin.py
    print_success "Admin user setup completed"
else
    print_warning "create_admin.py not found, skipping admin user creation"
    print_color $CYAN "You can create an admin user later by running the create_admin.py script"
fi

# Step 7: Run tests
print_step 7 "Running Basic Tests"

if [ -d "tests" ]; then
    print_color $BLUE "Running tests..."
    if python -m pytest tests/ -v; then
        print_success "All tests passed"
    else
        print_warning "Some tests failed, but setup can continue"
    fi
else
    print_warning "No tests directory found, skipping tests"
fi

# Completion message
echo
print_color $PURPLE "========================================"
print_color $PURPLE "🎉 SETUP COMPLETED SUCCESSFULLY! 🎉"
print_color $PURPLE "========================================"
echo

print_color $CYAN "Next Steps:"
print_color $BLUE "1. Activate the virtual environment:"
print_color $GREEN "   source venv/bin/activate"
echo

print_color $BLUE "2. Edit the .env file with your configuration:"
print_color $GREEN "   - Set your SECRET_KEY"
print_color $GREEN "   - Configure MCP server URLs"
print_color $GREEN "   - Set AI API credentials"
echo

print_color $BLUE "3. Start the application:"
print_color $GREEN "   python jia.py"
echo

print_color $BLUE "4. Open your browser and go to:"
print_color $GREEN "   http://localhost:5000"
echo

print_color $CYAN "For more information, check the README.md file"
echo