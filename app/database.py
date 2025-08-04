"""
Database initialization and management utilities.

This module provides functions for initializing the database with default data
and managing database operations.
"""

from app import db
from app.models import Role, User, AdminPrompt
from flask import current_app


def init_database():
    """
    Initialize database with tables and default data.
    
    This function should be called after creating the Flask app context.
    """
    # Create all tables
    db.create_all()
    
    # Create default roles
    create_default_roles()
    
    # Create default admin prompts
    create_default_prompts()
    
    # Commit changes
    db.session.commit()
    
    current_app.logger.info("Database initialized successfully")


def create_default_roles():
    """Create default roles if they don't exist."""
    default_roles = [
        {
            'name': Role.SCRUM_MASTER,
            'description': 'Scrum Master role with access to sprint management, capacity planning, and team analytics features'
        },
        {
            'name': Role.PRODUCT_OWNER,
            'description': 'Product Owner role with access to ticket creation, validation, epic breakdown, and release management features'
        },
        {
            'name': Role.BUSINESS_ANALYST,
            'description': 'Business Analyst role with access to ticket creation, validation, test case generation, and requirements analysis features'
        },
        {
            'name': Role.TECH_MANAGER,
            'description': 'Technical Manager role with administrative access to user management, system configuration, and all features'
        },
        {
            'name': Role.STAKEHOLDER,
            'description': 'Stakeholder role with read-only access to dashboards, reports, and sprint health information'
        }
    ]
    
    for role_data in default_roles:
        existing_role = Role.query.filter_by(name=role_data['name']).first()
        if not existing_role:
            role = Role(**role_data)
            db.session.add(role)
            current_app.logger.info(f"Created default role: {role_data['name']}")


def create_default_prompts():
    """Create default AI prompts for various features."""
    default_prompts = [
        {
            'feature_name': 'ticket_creation',
            'prompt_template': '''You are an expert Jira ticket creator. Based on the user's natural language input, create a well-structured ticket with the following format:

User Input: {user_input}
Target Location: {target_location}
Board: {board_name}

Please create a ticket with:
1. Clear, concise summary
2. Detailed description
3. Acceptance criteria (if applicable)
4. Appropriate ticket type (Story, Task, Bug, etc.)

Output the result as JSON with fields: summary, description, ticket_type, acceptance_criteria.''',
            'output_format': 'json',
            'is_active': True
        },
        {
            'feature_name': 'ticket_validation',
            'prompt_template': '''You are a ticket validation expert. Analyze the provided tickets against the given criteria and provide detailed validation results.

Tickets: {tickets}
Validation Criteria: {criteria}

For each ticket, check against all criteria and provide:
1. Overall compliance score (0-100)
2. List of passed criteria
3. List of failed criteria
4. Specific recommendations for improvement

Output as JSON with validation results for each ticket.''',
            'output_format': 'json',
            'is_active': True
        },
        {
            'feature_name': 'sprint_capacity',
            'prompt_template': '''You are a sprint capacity planning expert. Based on the team's historical data and current availability, provide capacity recommendations.

Historical Velocity: {historical_velocity}
Team Availability: {team_availability}
Planned Leave: {planned_leave}
Sprint Duration: {sprint_duration}

Provide:
1. Recommended story point capacity
2. Confidence level
3. Risk factors
4. Rationale for the recommendation

Output as natural language explanation with specific numbers.''',
            'output_format': 'text',
            'is_active': True
        },
        {
            'feature_name': 'spillover_prediction',
            'prompt_template': '''You are a sprint spillover prediction expert. Analyze the current sprint progress and predict spillover risks.

Sprint Data: {sprint_data}
Current Progress: {current_progress}
Historical Patterns: {historical_patterns}

Identify:
1. Tickets at risk of spillover
2. Risk level (High/Medium/Low)
3. Reasons for the risk
4. Recommended actions

Output as JSON with risk analysis for each at-risk ticket.''',
            'output_format': 'json',
            'is_active': True
        },
        {
            'feature_name': 'story_point_estimation',
            'prompt_template': '''You are a story point estimation expert. Based on the ticket description and similar historical tickets, provide estimation recommendations.

Ticket Description: {ticket_description}
Similar Tickets: {similar_tickets}

Provide:
1. Recommended story points
2. Confidence level
3. Reasoning based on complexity, effort, and uncertainty
4. References to similar tickets

Output as JSON with estimation details.''',
            'output_format': 'json',
            'is_active': True
        }
    ]
    
    for prompt_data in default_prompts:
        existing_prompt = AdminPrompt.query.filter_by(
            feature_name=prompt_data['feature_name']
        ).first()
        if not existing_prompt:
            prompt = AdminPrompt(**prompt_data)
            db.session.add(prompt)
            current_app.logger.info(f"Created default prompt: {prompt_data['feature_name']}")


def create_admin_user(username: str, email: str, password: str):
    """
    Create an admin user with tech_manager role.
    
    Args:
        username: Admin username
        email: Admin email
        password: Admin password (will be hashed)
    
    Returns:
        User: Created admin user or None if user already exists
    """
    # Check if user already exists
    existing_user = User.query.filter(
        (User.username == username) | (User.email == email)
    ).first()
    
    if existing_user:
        current_app.logger.warning(f"User with username '{username}' or email '{email}' already exists")
        return None
    
    # Get tech_manager role
    tech_manager_role = Role.query.filter_by(name=Role.TECH_MANAGER).first()
    if not tech_manager_role:
        current_app.logger.error("Tech manager role not found. Please run init_database() first.")
        return None
    
    # Create admin user
    admin_user = User(
        username=username,
        email=email,
        is_active=True
    )
    admin_user.set_password(password)
    admin_user.roles.append(tech_manager_role)
    
    db.session.add(admin_user)
    db.session.commit()
    
    current_app.logger.info(f"Created admin user: {username}")
    return admin_user


def reset_database():
    """
    Reset database by dropping all tables and recreating them.
    
    WARNING: This will delete all data!
    """
    db.drop_all()
    init_database()
    current_app.logger.warning("Database has been reset - all data deleted!")


def get_database_stats():
    """
    Get basic database statistics.
    
    Returns:
        dict: Database statistics
    """
    stats = {
        'users': User.query.count(),
        'roles': Role.query.count(),
        'mcp_configurations': db.session.execute(
            db.text("SELECT COUNT(*) FROM mcp_configurations")
        ).scalar(),
        'ai_configurations': db.session.execute(
            db.text("SELECT COUNT(*) FROM ai_configurations")
        ).scalar(),
        'validation_criteria': db.session.execute(
            db.text("SELECT COUNT(*) FROM validation_criteria")
        ).scalar(),
        'admin_prompts': AdminPrompt.query.count()
    }
    
    return stats