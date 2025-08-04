# JIA (Jira Intelligent Agent)

JIA is a comprehensive web application built with Python Flask that integrates with Atlassian Jira and Confluence through the mcp-atlassian MCP server. The system provides AI-powered automation for Jira tasks, natural language query processing, and intelligent insights for agile teams.

## Features

- **Multi-User Configuration Management**: Individual Jira/Confluence connections and AI settings
- **Role-Based Access Control**: Support for scrum masters, product owners, business analysts, tech managers, and stakeholders
- **AI-Powered Ticket Creation**: Create user stories, tasks, and bugs using natural language
- **Ticket Validation**: Validate tickets against Definition of Ready, Definition of Done, and custom criteria
- **Sprint Analytics**: Capacity recommendations, health dashboards, and spillover predictions
- **Natural Language Queries**: Query Jira using plain English instead of JQL
- **Intelligent Automation**: Story point estimation, test case generation, and release notes

## Quick Start

### Prerequisites

- Python 3.13+
- Redis server
- Access to Jira Data Center with Personal Access Tokens

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd jia
```

2. Create and activate virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. Initialize the database:
```bash
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

6. Run the application:
```bash
flask run
```

## Configuration

Create a `.env` file in the root directory with the following variables:

```env
FLASK_APP=app
FLASK_ENV=development
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///jia.db
REDIS_URL=redis://localhost:6379/0
```

## Architecture

JIA follows a modular Flask architecture with:

- **Flask Application Factory**: Configurable app creation
- **MCP Integration**: Communication with mcp-atlassian server
- **AI Service Integration**: Natural language processing and automation
- **Role-Based Security**: Multi-user support with permission management
- **Responsive UI**: Bootstrap-based interface

## Development

### Running Tests

```bash
pytest
```

### Code Coverage

```bash
pytest --cov=app
```

### Database Migrations

```bash
flask db migrate -m "Description of changes"
flask db upgrade
```

## License

[License information]

## Contributing

[Contributing guidelines]