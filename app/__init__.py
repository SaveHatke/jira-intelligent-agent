"""
JIA (Jira Intelligent Agent) Flask Application

A comprehensive web application that integrates with Atlassian Jira and Confluence
through the mcp-atlassian MCP server, providing AI-powered automation for Jira tasks.
"""

import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from dotenv import load_dotenv

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
csrf = CSRFProtect()

def create_app(config_name=None):
    """
    Flask application factory pattern.
    
    Args:
        config_name: Configuration name ('development', 'production', 'testing')
        
    Returns:
        Flask application instance
    """
    # Load environment variables
    load_dotenv()
    
    # Create Flask app with correct template and static folders
    app = Flask(__name__, 
                template_folder='../templates',
                static_folder='../static')
    
    # Load configuration
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')
    
    app.config.from_object(f'app.config.{config_name.title()}Config')
    
    # Initialize extensions with app
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)
    
    # Configure login manager
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    
    # Register blueprints
    register_blueprints(app)
    
    # Register error handlers
    register_error_handlers(app)
    
    return app

def register_blueprints(app):
    """Register application blueprints."""
    # Import blueprints here to avoid circular imports
    from app.main import bp as main_bp
    from app.auth import bp as auth_bp
    from app.admin import bp as admin_bp
    from app.config_mgmt import bp as config_bp
    
    # Import models to register user_loader
    from app import models
    
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(config_bp, url_prefix='/config')

def register_error_handlers(app):
    """Register application error handlers."""
    
    @app.errorhandler(403)
    def forbidden_error(error):
        from flask import render_template
        return render_template('errors/403.html'), 403
    
    @app.errorhandler(404)
    def not_found_error(error):
        from flask import render_template
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        from flask import render_template
        db.session.rollback()
        return render_template('errors/500.html'), 500