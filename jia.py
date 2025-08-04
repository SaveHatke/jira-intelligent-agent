"""
JIA (Jira Intelligent Agent) application entry point.

This module creates the Flask application instance and provides
the main entry point for running the application.
"""

import os
from app import create_app, db
from app.models import (
    User, Role, MCPConfiguration, AIConfiguration, 
    ValidationCriteria, AdminPrompt
)

# Create Flask application
app = create_app(os.getenv('FLASK_ENV'))

@app.shell_context_processor
def make_shell_context():
    """Make database models available in Flask shell."""
    return {
        'db': db,
        'User': User,
        'Role': Role,
        'MCPConfiguration': MCPConfiguration,
        'AIConfiguration': AIConfiguration,
        'ValidationCriteria': ValidationCriteria,
        'AdminPrompt': AdminPrompt
    }

if __name__ == '__main__':
    app.run(debug=True)