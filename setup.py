#!/usr/bin/env python3
"""
JIA (Jira Intelligent Agent) Setup Script
==========================================

This script automates the setup process for the JIA project on any device.
It handles virtual environment creation, dependency installation, database setup,
and initial configuration.

Usage:
    python setup.py [--dev] [--skip-venv] [--help]

Options:
    --dev       Install development dependencies
    --skip-venv Skip virtual environment creation
    --help      Show this help message
"""

import os
import sys
import subprocess
import platform
import argparse
from pathlib import Path

class Colors:
    """ANSI color codes for terminal output"""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_colored(message, color=Colors.OKGREEN):
    """Print colored message to terminal"""
    print(f"{color}{message}{Colors.ENDC}")

def print_step(step_num, message):
    """Print step with formatting"""
    print_colored(f"\n{'='*60}", Colors.HEADER)
    print_colored(f"STEP {step_num}: {message}", Colors.HEADER)
    print_colored(f"{'='*60}", Colors.HEADER)

def run_command(command, shell=True, check=True):
    """Run command and handle errors"""
    try:
        print_colored(f"Running: {command}", Colors.OKBLUE)
        # Handle command as list for better path handling with spaces
        if isinstance(command, str) and shell:
            result = subprocess.run(command, shell=shell, check=check, 
                                  capture_output=True, text=True)
        else:
            result = subprocess.run(command, shell=shell, check=check, 
                                  capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
        return result
    except subprocess.CalledProcessError as e:
        print_colored(f"Error running command: {command}", Colors.FAIL)
        print_colored(f"Error: {e.stderr}", Colors.FAIL)
        return None

def check_python_version():
    """Check if Python version is compatible"""
    print_step(1, "Checking Python Version")
    
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print_colored("Error: Python 3.8 or higher is required!", Colors.FAIL)
        print_colored(f"Current version: {version.major}.{version.minor}.{version.micro}", Colors.WARNING)
        sys.exit(1)
    
    print_colored(f"✓ Python {version.major}.{version.minor}.{version.micro} is compatible", Colors.OKGREEN)

def create_virtual_environment(skip_venv=False):
    """Create and activate virtual environment"""
    if skip_venv:
        print_colored("Skipping virtual environment creation", Colors.WARNING)
        return
    
    print_step(2, "Creating Virtual Environment")
    
    venv_path = Path("venv")
    if venv_path.exists():
        print_colored("Virtual environment already exists", Colors.WARNING)
        return
    
    # Create virtual environment
    result = run_command(f'"{sys.executable}" -m venv venv')
    if not result:
        print_colored("Failed to create virtual environment", Colors.FAIL)
        sys.exit(1)
    
    print_colored("✓ Virtual environment created successfully", Colors.OKGREEN)
    
    # Provide activation instructions
    system = platform.system().lower()
    if system == "windows":
        activate_cmd = "venv\\Scripts\\activate"
    else:
        activate_cmd = "source venv/bin/activate"
    
    print_colored(f"\nTo activate the virtual environment, run:", Colors.OKCYAN)
    print_colored(f"  {activate_cmd}", Colors.BOLD)

def install_dependencies(dev=False):
    """Install Python dependencies"""
    print_step(3, "Installing Dependencies")
    
    # Determine pip command
    system = platform.system().lower()
    if system == "windows" and Path("venv/Scripts/pip.exe").exists():
        pip_cmd = '"venv\\Scripts\\pip"'
    elif Path("venv/bin/pip").exists():
        pip_cmd = '"venv/bin/pip"'
    else:
        pip_cmd = "pip"
    
    # Upgrade pip first
    run_command(f"{pip_cmd} install --upgrade pip")
    
    # Install main dependencies
    if Path("requirements.txt").exists():
        result = run_command(f"{pip_cmd} install -r requirements.txt")
        if not result:
            print_colored("Failed to install dependencies", Colors.FAIL)
            sys.exit(1)
    else:
        print_colored("requirements.txt not found, installing basic dependencies", Colors.WARNING)
        basic_deps = [
            "Flask>=2.3.0",
            "Flask-SQLAlchemy>=3.0.0",
            "Flask-Migrate>=4.0.0",
            "Flask-Login>=0.6.0",
            "bcrypt>=4.0.0",
            "python-dotenv>=1.0.0",
            "cryptography>=41.0.0"
        ]
        for dep in basic_deps:
            run_command(f"{pip_cmd} install {dep}")
    
    # Install development dependencies if requested
    if dev:
        dev_deps = ["pytest>=7.0.0", "pytest-flask>=1.2.0", "black>=23.0.0", "flake8>=6.0.0"]
        for dep in dev_deps:
            run_command(f"{pip_cmd} install {dep}")
        print_colored("✓ Development dependencies installed", Colors.OKGREEN)
    
    print_colored("✓ Dependencies installed successfully", Colors.OKGREEN)

def setup_environment_file():
    """Create .env file from template"""
    print_step(4, "Setting up Environment Configuration")
    
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if env_file.exists():
        print_colored(".env file already exists", Colors.WARNING)
        return
    
    if env_example.exists():
        # Copy from example
        with open(env_example, 'r') as src, open(env_file, 'w') as dst:
            content = src.read()
            dst.write(content)
        print_colored("✓ .env file created from .env.example", Colors.OKGREEN)
    else:
        # Create basic .env file
        env_content = """# JIA Configuration
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
"""
        with open(env_file, 'w') as f:
            f.write(env_content)
        print_colored("✓ Basic .env file created", Colors.OKGREEN)
    
    print_colored("\n⚠️  Please edit .env file with your actual configuration values", Colors.WARNING)

def setup_database():
    """Initialize database and run migrations"""
    print_step(5, "Setting up Database")
    
    # Determine python command
    system = platform.system().lower()
    if system == "windows" and Path("venv/Scripts/python.exe").exists():
        python_cmd = '"venv\\Scripts\\python"'
    elif Path("venv/bin/python").exists():
        python_cmd = '"venv/bin/python"'
    else:
        python_cmd = "python"
    
    # Create instance directory
    instance_dir = Path("instance")
    instance_dir.mkdir(exist_ok=True)
    
    # Initialize database
    if Path("manage_db.py").exists():
        print_colored("Running database initialization...", Colors.OKBLUE)
        result = run_command(f"{python_cmd} manage_db.py init-db")
        if not result:
            print_colored("Database initialization failed, trying alternative method...", Colors.WARNING)
            # Try to create tables directly
            result = run_command(f"{python_cmd} -c \"from app import create_app, db; app = create_app(); app.app_context().push(); db.create_all(); print('Tables created successfully')\"")
        
        if result:
            print_colored("✓ Database initialized successfully", Colors.OKGREEN)
        else:
            print_colored("⚠️ Database initialization had issues, but continuing...", Colors.WARNING)
    else:
        print_colored("manage_db.py not found, creating tables directly...", Colors.WARNING)
        result = run_command(f"{python_cmd} -c \"from app import create_app, db; app = create_app(); app.app_context().push(); db.create_all(); print('Tables created successfully')\"")
        if result:
            print_colored("✓ Database tables created successfully", Colors.OKGREEN)
    
    # Run migrations if available
    if Path("migrations").exists():
        print_colored("Running database migrations...", Colors.OKBLUE)
        run_command(f"{python_cmd} -m flask db upgrade")
        print_colored("✓ Database migrations completed", Colors.OKGREEN)

def create_admin_user():
    """Create initial admin user"""
    print_step(6, "Creating Admin User")
    
    # Determine python command
    system = platform.system().lower()
    if system == "windows" and Path("venv/Scripts/python.exe").exists():
        python_cmd = '"venv\\Scripts\\python"'
    elif Path("venv/bin/python").exists():
        python_cmd = '"venv/bin/python"'
    else:
        python_cmd = "python"
    
    if Path("create_admin.py").exists():
        print_colored("Creating admin user...", Colors.OKBLUE)
        result = run_command(f"{python_cmd} create_admin.py", check=False)
        if result and result.returncode == 0:
            print_colored("✓ Admin user created successfully", Colors.OKGREEN)
        else:
            print_colored("⚠️ Admin user creation failed, you can create it manually later", Colors.WARNING)
            print_colored("Run: python create_admin.py", Colors.OKCYAN)
    else:
        print_colored("create_admin.py not found, skipping admin user creation", Colors.WARNING)
        print_colored("You can create an admin user later by running the create_admin.py script", Colors.OKCYAN)

def run_tests():
    """Run basic tests to verify setup"""
    print_step(7, "Running Basic Tests")
    
    # Determine python command
    system = platform.system().lower()
    if system == "windows" and Path("venv/Scripts/python.exe").exists():
        python_cmd = '"venv\\Scripts\\python"'
    elif Path("venv/bin/python").exists():
        python_cmd = '"venv/bin/python"'
    else:
        python_cmd = "python"
    
    if Path("tests").exists():
        print_colored("Running tests...", Colors.OKBLUE)
        result = run_command(f"{python_cmd} -m pytest tests/ -v", check=False)
        if result and result.returncode == 0:
            print_colored("✓ All tests passed", Colors.OKGREEN)
        else:
            print_colored("⚠️  Some tests failed, but setup can continue", Colors.WARNING)
    else:
        print_colored("No tests directory found, skipping tests", Colors.WARNING)

def print_completion_message():
    """Print setup completion message with next steps"""
    print_colored(f"\n{'='*60}", Colors.HEADER)
    print_colored("🎉 JIA SETUP COMPLETED SUCCESSFULLY! 🎉", Colors.HEADER)
    print_colored(f"{'='*60}", Colors.HEADER)
    
    system = platform.system().lower()
    if system == "windows":
        activate_cmd = "venv\\Scripts\\activate"
        python_cmd = '"venv\\Scripts\\python"'
    else:
        activate_cmd = "source venv/bin/activate"
        python_cmd = '"venv/bin/python"'
    
    print_colored("\nNext Steps:", Colors.OKCYAN)
    print_colored("1. Activate the virtual environment:", Colors.OKBLUE)
    print_colored(f"   {activate_cmd}", Colors.BOLD)
    
    print_colored("\n2. Edit the .env file with your configuration:", Colors.OKBLUE)
    print_colored("   - Set your SECRET_KEY", Colors.BOLD)
    print_colored("   - Configure MCP server URLs", Colors.BOLD)
    print_colored("   - Set AI API credentials", Colors.BOLD)
    
    print_colored("\n3. Start the application:", Colors.OKBLUE)
    print_colored(f"   {python_cmd} jia.py", Colors.BOLD)
    
    print_colored("\n4. Open your browser and go to:", Colors.OKBLUE)
    print_colored("   http://localhost:5000", Colors.BOLD)
    
    print_colored("\nFor more information, check the README.md file", Colors.OKCYAN)

def main():
    """Main setup function"""
    parser = argparse.ArgumentParser(description="JIA Setup Script")
    parser.add_argument("--dev", action="store_true", help="Install development dependencies")
    parser.add_argument("--skip-venv", action="store_true", help="Skip virtual environment creation")
    args = parser.parse_args()
    
    print_colored("🚀 JIA (Jira Intelligent Agent) Setup Script", Colors.HEADER)
    print_colored("This script will set up the JIA project on your system\n", Colors.OKCYAN)
    
    try:
        check_python_version()
        create_virtual_environment(args.skip_venv)
        install_dependencies(args.dev)
        setup_environment_file()
        setup_database()
        create_admin_user()
        run_tests()
        print_completion_message()
        
    except KeyboardInterrupt:
        print_colored("\n\nSetup interrupted by user", Colors.WARNING)
        sys.exit(1)
    except Exception as e:
        print_colored(f"\n\nSetup failed with error: {str(e)}", Colors.FAIL)
        sys.exit(1)

if __name__ == "__main__":
    main()