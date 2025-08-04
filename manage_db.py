#!/usr/bin/env python3
"""
Database management script for JIA application.

This script provides CLI commands for database initialization, migration,
and management tasks.
"""

import os
import sys
from flask import Flask
from flask.cli import with_appcontext
import click

# Add the app directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.database import init_database, create_admin_user, reset_database, get_database_stats
from app.models import User, Role


def create_cli_app():
    """Create Flask app for CLI commands."""
    app = create_app()
    
    @app.cli.command()
    @with_appcontext
    def init_db():
        """Initialize database with tables and default data."""
        try:
            init_database()
            click.echo("✅ Database initialized successfully!")
            
            # Show stats
            stats = get_database_stats()
            click.echo(f"📊 Database stats: {stats}")
            
        except Exception as e:
            click.echo(f"❌ Error initializing database: {str(e)}")
            sys.exit(1)
    
    @app.cli.command()
    @with_appcontext
    def reset_db():
        """Reset database (WARNING: Deletes all data!)."""
        if click.confirm('⚠️  This will delete ALL data. Are you sure?'):
            try:
                reset_database()
                click.echo("✅ Database reset successfully!")
            except Exception as e:
                click.echo(f"❌ Error resetting database: {str(e)}")
                sys.exit(1)
        else:
            click.echo("Database reset cancelled.")
    
    @app.cli.command()
    @click.option('--username', prompt='Admin username', help='Admin username')
    @click.option('--email', prompt='Admin email', help='Admin email address')
    @click.option('--password', prompt=True, hide_input=True, help='Admin password')
    @with_appcontext
    def create_admin(username, email, password):
        """Create an admin user."""
        try:
            admin_user = create_admin_user(username, email, password)
            if admin_user:
                click.echo(f"✅ Admin user '{username}' created successfully!")
            else:
                click.echo(f"❌ Failed to create admin user. User may already exist.")
        except Exception as e:
            click.echo(f"❌ Error creating admin user: {str(e)}")
            sys.exit(1)
    
    @app.cli.command()
    @with_appcontext
    def db_stats():
        """Show database statistics."""
        try:
            stats = get_database_stats()
            click.echo("📊 Database Statistics:")
            for table, count in stats.items():
                click.echo(f"  {table}: {count}")
        except Exception as e:
            click.echo(f"❌ Error getting database stats: {str(e)}")
            sys.exit(1)
    
    @app.cli.command()
    @with_appcontext
    def list_users():
        """List all users and their roles."""
        try:
            users = User.query.all()
            if not users:
                click.echo("No users found.")
                return
            
            click.echo("👥 Users:")
            for user in users:
                roles = ', '.join([role.name for role in user.roles])
                status = "Active" if user.is_active else "Inactive"
                click.echo(f"  {user.username} ({user.email}) - Roles: {roles} - Status: {status}")
                
        except Exception as e:
            click.echo(f"❌ Error listing users: {str(e)}")
            sys.exit(1)
    
    @app.cli.command()
    @with_appcontext
    def list_roles():
        """List all available roles."""
        try:
            roles = Role.query.all()
            if not roles:
                click.echo("No roles found.")
                return
            
            click.echo("🎭 Roles:")
            for role in roles:
                user_count = len(role.users)
                click.echo(f"  {role.name}: {role.description} ({user_count} users)")
                
        except Exception as e:
            click.echo(f"❌ Error listing roles: {str(e)}")
            sys.exit(1)
    
    return app


if __name__ == '__main__':
    app = create_cli_app()
    
    # If no arguments provided, show help
    if len(sys.argv) == 1:
        with app.app_context():
            click.echo("JIA Database Management CLI")
            click.echo("Available commands:")
            click.echo("  python manage_db.py init-db      - Initialize database")
            click.echo("  python manage_db.py reset-db     - Reset database (deletes all data)")
            click.echo("  python manage_db.py create-admin - Create admin user")
            click.echo("  python manage_db.py db-stats     - Show database statistics")
            click.echo("  python manage_db.py list-users   - List all users")
            click.echo("  python manage_db.py list-roles   - List all roles")
            click.echo("")
            click.echo("Use 'python manage_db.py COMMAND --help' for more info on a command.")
    else:
        app.cli()