# JIA (Jira Intelligent Agent)

A comprehensive Flask web application that integrates with Atlassian Jira and Confluence through the mcp-atlassian MCP server, providing AI-powered automation for Jira tasks, natural language query processing, and intelligent insights for agile teams.

## 🚀 Quick Setup

We provide automated setup scripts for easy installation on any system:

### Option 1: Automated Setup (Recommended)

**Windows:**
```cmd
python setup.py
```
or
```cmd
setup.bat
```

**Linux/macOS:**
```bash
python3 setup.py
```
or
```bash
./setup.sh
```

### Option 2: Manual Setup

See the [Manual Installation](#manual-installation) section below.

## ✨ Features

- **Multi-user Environment**: Role-based access control with individual configurations
- **AI-Powered Ticket Creation**: Create Jira tickets from natural language input
- **Smart Validation**: Validate tickets against DoR, DoD, and custom criteria
- **Sprint Intelligence**: Capacity recommendations and spillover predictions
- **Jira Time Machine**: Comprehensive ticket history analysis
- **Natural Language Queries**: Query Jira using plain English
- **Automated Insights**: Sprint health dashboards with AI commentary
- **Story Point Estimation**: AI-powered estimation based on historical data
- **Test Case Generation**: Automated test case creation from requirements
- **Epic Breakdown**: Intelligent decomposition of large stories
- **Bug Triage**: Automated duplicate detection and severity assessment
- **Release Automation**: Automated release notes and sprint reviews
- **Dependency Mapping**: Visual dependency tracking and management
- **SLA Monitoring**: Automated escalation and breach prevention

## 🛠 Technology Stack

- **Backend**: Flask (Python 3.8+)
- **Frontend**: HTML5, CSS3, JavaScript with Bootstrap 5
- **Database**: SQLite (dev) / PostgreSQL (prod)
- **Authentication**: Flask-Login with bcrypt
- **MCP Integration**: mcp-atlassian server communication
- **AI Integration**: Configurable AI API support

## 📋 Prerequisites

- Python 3.8 or higher
- Git
- Access to Jira Data Center instance
- (Optional) Confluence Data Center instance
- (Optional) AI API credentials

## 🔧 Manual Installation

If you prefer to set up manually or the automated scripts don't work for your system:

### 1. Clone the Repository
```bash
git clone https://github.com/SaveHatke/jira-intelligent-agent.git
cd jira-intelligent-agent
```

### 2. Create Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/macOS
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Environment Configuration
```bash
# Copy environment template
cp .env.example .env

# Edit .env with your settings
# Required: SECRET_KEY, DATABASE_URL
# Optional: MCP and AI configurations
```

### 5. Database Setup
```bash
# Create instance directory
mkdir instance

# Initialize database
python manage_db.py

# Run migrations (if available)
flask db upgrade
```

### 6. Create Admin User
```bash
python create_admin.py
```

### 7. Start Application
```bash
python jia.py
```

Visit `http://localhost:5000` to access the application.

## ⚙️ Configuration

### Environment Variables (.env file)

```bash
# Flask Configuration
FLASK_APP=jia.py
FLASK_ENV=development
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///instance/jia-dev.db

# MCP Server Configuration
MCP_SERVER_URL=your-mcp-server-url
DEFAULT_JIRA_URL=https://your-jira-instance.com
DEFAULT_CONFLUENCE_URL=https://your-confluence-instance.com

# AI Service Configuration
AI_API_URL=your-ai-api-url
AI_API_KEY=your-ai-api-key

# Security
ENCRYPTION_KEY=your-encryption-key-here
```

### User Roles

The system supports these roles with specific permissions:

| Role | Permissions |
|------|-------------|
| **Scrum Master** | Sprint management, capacity planning, health dashboards |
| **Product Owner** | Ticket creation, validation, epic breakdown |
| **Business Analyst** | Requirements analysis, ticket validation, test case generation |
| **Tech Manager** | Technical oversight, reporting, SLA monitoring |
| **Stakeholder** | Read-only access to reports and dashboards |

### MCP Server Setup

JIA requires the mcp-atlassian server for Jira/Confluence integration:

1. Install and configure mcp-atlassian server
2. Ensure it's accessible from your JIA instance
3. Configure connection details in user settings

## 🎯 Usage Guide

### First Time Setup

1. **Access Application**: Navigate to `http://localhost:5000`
2. **Login**: Use admin credentials created during setup
3. **User Management**: Create users and assign roles (Admin → User Management)
4. **Individual Configuration**: Each user configures their MCP and AI settings
5. **Test Connections**: Verify Jira/Confluence connectivity

### Key Features

#### Ticket Creation
- Navigate to "Create Tickets" from dashboard
- Select board and sprint/backlog
- Enter requirements in natural language
- AI generates structured tickets with acceptance criteria

#### Ticket Validation
- Go to "Validate Tickets" feature
- Configure DoR/DoD criteria
- Select tickets or sprints to validate
- Review AI-generated validation reports

#### Sprint Analytics
- Access "Sprint Health" dashboard
- View capacity recommendations
- Monitor spillover predictions
- Get AI-powered insights

## 🧪 Development

### Running Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app tests/

# Run specific test file
pytest tests/test_models.py -v
```

### Database Operations
```bash
# Create migration
flask db migrate -m "Description"

# Apply migrations
flask db upgrade

# Reset database (development only)
python manage_db.py --reset
```

### Code Quality
```bash
# Format code
black app/ tests/

# Lint code
flake8 app/ tests/

# Type checking (if using mypy)
mypy app/
```

## 📁 Project Structure

```
jira-intelligent-agent/
├── app/                    # Main application package
│   ├── admin/             # Admin interface
│   ├── auth/              # Authentication
│   ├── config_mgmt/       # Configuration management
│   ├── main/              # Main routes
│   └── models.py          # Database models
├── migrations/            # Database migrations
├── static/               # Static files (CSS, JS)
├── templates/            # Jinja2 templates
├── tests/                # Test suite
├── instance/             # Instance-specific files
├── .kiro/specs/          # Project specifications
├── setup.py              # Cross-platform setup script
├── setup.bat             # Windows setup script
├── setup.sh              # Linux/macOS setup script
├── jia.py                # Application entry point
├── manage_db.py          # Database management
├── create_admin.py       # Admin user creation
└── requirements.txt      # Python dependencies
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes and add tests
4. Ensure tests pass: `pytest`
5. Commit changes: `git commit -m 'Add amazing feature'`
6. Push to branch: `git push origin feature/amazing-feature`
7. Submit a Pull Request

### Development Guidelines

- Follow PEP 8 style guidelines
- Add tests for new functionality
- Update documentation for new features
- Use meaningful commit messages
- Keep PRs focused and atomic

## 🐛 Troubleshooting

### Common Issues

**Setup Script Fails**
- Ensure Python 3.8+ is installed and in PATH
- Check internet connectivity for package downloads
- Run with `--dev` flag for additional debugging

**Database Errors**
- Delete `instance/jia-dev.db` and run `python manage_db.py`
- Check file permissions in instance directory
- Verify DATABASE_URL in .env file

**MCP Connection Issues**
- Verify mcp-atlassian server is running
- Check network connectivity to Jira/Confluence
- Validate Personal Access Tokens
- Review MCP server logs

**Authentication Problems**
- Clear browser cookies and cache
- Check SECRET_KEY in .env file
- Verify user exists in database
- Reset password if needed

### Getting Help

- Check the [Issues](https://github.com/SaveHatke/jira-intelligent-agent/issues) page
- Review the project specifications in `.kiro/specs/`
- Enable debug mode: set `FLASK_ENV=development` in .env
- Check application logs for detailed error messages

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Flask community for the excellent web framework
- mcp-atlassian project for Jira/Confluence integration
- Bootstrap team for the responsive UI framework
- All contributors and users of this project

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/SaveHatke/jira-intelligent-agent/issues)
- **Discussions**: [GitHub Discussions](https://github.com/SaveHatke/jira-intelligent-agent/discussions)
- **Documentation**: Check the `.kiro/specs/` directory for detailed specifications

---

**Made with ❤️ for agile teams everywhere**