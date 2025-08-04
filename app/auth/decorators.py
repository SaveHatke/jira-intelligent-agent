"""
Role-based access control decorators for JIA application.

Provides decorators to restrict access to routes based on user roles.
"""

from functools import wraps
from flask import abort, flash, redirect, url_for, request
from flask_login import current_user
from app.models import Role


def role_required(*roles):
    """
    Decorator to require specific roles for route access.
    
    Args:
        *roles: Variable number of role names that are allowed access
        
    Usage:
        @role_required('admin', 'manager')
        def admin_only_view():
            pass
            
        @role_required(Role.SCRUM_MASTER, Role.PRODUCT_OWNER)
        def scrum_view():
            pass
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Please log in to access this page.', 'error')
                return redirect(url_for('auth.login', next=request.url))
            
            if not current_user.has_any_role(list(roles)):
                flash('You do not have permission to access this page.', 'error')
                abort(403)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def admin_required(f):
    """
    Decorator to require admin (tech_manager) role for route access.
    
    Usage:
        @admin_required
        def admin_view():
            pass
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('auth.login', next=request.url))
        
        if not current_user.is_admin():
            flash('Administrator privileges required to access this page.', 'error')
            abort(403)
        
        return f(*args, **kwargs)
    return decorated_function


def scrum_master_required(f):
    """
    Decorator to require scrum master role for route access.
    
    Usage:
        @scrum_master_required
        def scrum_view():
            pass
    """
    return role_required(Role.SCRUM_MASTER)(f)


def product_owner_required(f):
    """
    Decorator to require product owner role for route access.
    
    Usage:
        @product_owner_required
        def po_view():
            pass
    """
    return role_required(Role.PRODUCT_OWNER)(f)


def business_analyst_required(f):
    """
    Decorator to require business analyst role for route access.
    
    Usage:
        @business_analyst_required
        def ba_view():
            pass
    """
    return role_required(Role.BUSINESS_ANALYST)(f)


def ticket_creation_roles_required(f):
    """
    Decorator for routes that require ticket creation permissions.
    Allows product owners and business analysts.
    
    Usage:
        @ticket_creation_roles_required
        def create_ticket():
            pass
    """
    return role_required(Role.PRODUCT_OWNER, Role.BUSINESS_ANALYST)(f)


def validation_roles_required(f):
    """
    Decorator for routes that require ticket validation permissions.
    Allows product owners, business analysts, scrum masters, and developers.
    
    Usage:
        @validation_roles_required
        def validate_tickets():
            pass
    """
    return role_required(
        Role.PRODUCT_OWNER, 
        Role.BUSINESS_ANALYST, 
        Role.SCRUM_MASTER,
        Role.STAKEHOLDER  # Stakeholders can also validate
    )(f)


def management_roles_required(f):
    """
    Decorator for routes that require management permissions.
    Allows scrum masters and tech managers.
    
    Usage:
        @management_roles_required
        def management_view():
            pass
    """
    return role_required(Role.SCRUM_MASTER, Role.TECH_MANAGER)(f)


def any_authenticated_user(f):
    """
    Decorator that allows any authenticated user regardless of role.
    This is essentially the same as @login_required but provides consistency
    with other role decorators.
    
    Usage:
        @any_authenticated_user
        def user_view():
            pass
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('auth.login', next=request.url))
        
        return f(*args, **kwargs)
    return decorated_function


def check_user_permissions(required_roles):
    """
    Utility function to check if current user has required roles.
    
    Args:
        required_roles: List of role names or single role name
        
    Returns:
        bool: True if user has any of the required roles
        
    Usage:
        if check_user_permissions(['admin', 'manager']):
            # User has admin or manager role
            pass
    """
    if not current_user.is_authenticated:
        return False
    
    if isinstance(required_roles, str):
        required_roles = [required_roles]
    
    return current_user.has_any_role(required_roles)


def get_user_accessible_features():
    """
    Get list of features accessible to current user based on their roles.
    
    Returns:
        dict: Dictionary mapping feature names to accessibility status
    """
    if not current_user.is_authenticated:
        return {}
    
    user_roles = current_user.get_role_names()
    
    features = {
        'user_management': current_user.is_admin(),
        'ticket_creation': current_user.has_any_role([Role.PRODUCT_OWNER, Role.BUSINESS_ANALYST]),
        'ticket_validation': current_user.has_any_role([
            Role.PRODUCT_OWNER, Role.BUSINESS_ANALYST, Role.SCRUM_MASTER, Role.STAKEHOLDER
        ]),
        'sprint_capacity': current_user.has_role(Role.SCRUM_MASTER),
        'time_machine': True,  # Available to all authenticated users
        'sprint_health': current_user.has_any_role([Role.SCRUM_MASTER, Role.TECH_MANAGER]),
        'nl_query': True,  # Available to all authenticated users
        'spillover_prediction': current_user.has_any_role([Role.SCRUM_MASTER, Role.TECH_MANAGER]),
        'story_estimation': True,  # Available to all authenticated users
        'ticket_summarization': True,  # Available to all authenticated users
        'test_generation': True,  # Available to all authenticated users
        'epic_breakdown': current_user.has_any_role([Role.PRODUCT_OWNER, Role.BUSINESS_ANALYST]),
        'quality_analysis': current_user.has_any_role([Role.SCRUM_MASTER, Role.TECH_MANAGER]),
        'release_notes': current_user.has_any_role([Role.PRODUCT_OWNER, Role.SCRUM_MASTER]),
        'dependency_mapping': True,  # Available to all authenticated users
        'bug_triage': True,  # Available to all authenticated users
        'sla_monitoring': current_user.has_any_role([Role.TECH_MANAGER, Role.STAKEHOLDER]),
        'configuration': True,  # All users can configure their own settings
    }
    
    return features