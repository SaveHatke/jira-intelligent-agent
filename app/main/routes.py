"""Main application routes."""

from flask import render_template, redirect, url_for
from flask_login import login_required, current_user
from app.main import bp
from app.auth.decorators import get_user_accessible_features

@bp.route('/')
@bp.route('/index')
def index():
    """Home page route."""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    try:
        return render_template('index.html', title='Welcome to JIA')
    except:
        return 'Welcome to JIA - Templates will be available after full setup'

@bp.route('/dashboard')
@login_required
def dashboard():
    """Main dashboard route with role-based feature access."""
    # Get features accessible to current user
    accessible_features = get_user_accessible_features()
    
    # Get user role information
    user_roles = current_user.get_role_names()
    
    try:
        return render_template('dashboard.html', 
                             title='Dashboard',
                             accessible_features=accessible_features,
                             user_roles=user_roles)
    except:
        return f'Dashboard - Welcome {current_user.username}! Your roles: {", ".join(user_roles)}'