@echo off
REM JIA (Jira Intelligent Agent) Windows Setup Script
REM ================================================
REM This batch script automates the setup process for Windows users

echo.
echo ========================================
echo JIA (Jira Intelligent Agent) Setup
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8 or higher from https://python.org
    pause
    exit /b 1
)

echo Step 1: Checking Python version...
python -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)"
if errorlevel 1 (
    echo ERROR: Python 3.8 or higher is required
    python --version
    pause
    exit /b 1
)
echo ✓ Python version is compatible

echo.
echo Step 2: Creating virtual environment...
if exist venv (
    echo Virtual environment already exists
) else (
    python -m venv venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
    echo ✓ Virtual environment created
)

echo.
echo Step 3: Activating virtual environment and installing dependencies...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo ERROR: Failed to activate virtual environment
    pause
    exit /b 1
)

echo Upgrading pip...
python -m pip install --upgrade pip

echo Installing dependencies...
if exist requirements.txt (
    pip install -r requirements.txt
    if errorlevel 1 (
        echo ERROR: Failed to install dependencies
        pause
        exit /b 1
    )
) else (
    echo Installing basic dependencies...
    pip install Flask>=2.3.0 Flask-SQLAlchemy>=3.0.0 Flask-Migrate>=4.0.0 Flask-Login>=0.6.0 bcrypt>=4.0.0 python-dotenv>=1.0.0 cryptography>=41.0.0
)
echo ✓ Dependencies installed

echo.
echo Step 4: Setting up environment configuration...
if exist .env (
    echo .env file already exists
) else (
    if exist .env.example (
        copy .env.example .env
        echo ✓ .env file created from template
    ) else (
        echo Creating basic .env file...
        (
            echo # JIA Configuration
            echo FLASK_APP=jia.py
            echo FLASK_ENV=development
            echo SECRET_KEY=your-secret-key-change-this-in-production
            echo DATABASE_URL=sqlite:///instance/jia-dev.db
            echo.
            echo # MCP Configuration
            echo MCP_SERVER_URL=
            echo DEFAULT_JIRA_URL=
            echo DEFAULT_CONFLUENCE_URL=
            echo.
            echo # AI Configuration
            echo AI_API_URL=
            echo AI_API_KEY=
            echo.
            echo # Security
            echo ENCRYPTION_KEY=generate-a-secure-key-here
        ) > .env
        echo ✓ Basic .env file created
    )
)

echo.
echo Step 5: Setting up database...
if not exist instance mkdir instance

if exist manage_db.py (
    echo Initializing database...
    python manage_db.py
    echo ✓ Database initialized
) else (
    echo manage_db.py not found, skipping database initialization
)

if exist migrations (
    echo Running database migrations...
    python -m flask db upgrade
    echo ✓ Database migrations completed
)

echo.
echo Step 6: Creating admin user...
if exist create_admin.py (
    echo Creating admin user...
    python create_admin.py
    echo ✓ Admin user setup completed
) else (
    echo create_admin.py not found, skipping admin user creation
)

echo.
echo Step 7: Running basic tests...
if exist tests (
    echo Running tests...
    python -m pytest tests/ -v
    echo Tests completed
) else (
    echo No tests directory found, skipping tests
)

echo.
echo ========================================
echo 🎉 SETUP COMPLETED SUCCESSFULLY! 🎉
echo ========================================
echo.
echo Next Steps:
echo 1. Edit the .env file with your configuration
echo 2. To start the application, run:
echo    venv\Scripts\activate
echo    python jia.py
echo 3. Open your browser to http://localhost:5000
echo.
echo For more information, check the README.md file
echo.
pause