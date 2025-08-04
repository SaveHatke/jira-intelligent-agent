"""Authentication routes."""

from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user, login_required
from app.auth import bp
from app.models import User
from app import db

@bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login route."""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        remember_me = bool(request.form.get('remember_me'))
        
        # Validate input
        if not username or not password:
            flash('Username and password are required.', 'error')
            return render_template('auth/login.html', title='Sign In')
        
        # Find user by username or email
        user = User.query.filter(
            (User.username == username) | (User.email == username)
        ).first()
        
        # Check credentials
        if user is None or not user.check_password(password):
            flash('Invalid username or password.', 'error')
            return render_template('auth/login.html', title='Sign In')
        
        # Check if user is active
        if not user.is_active:
            flash('Your account has been deactivated. Please contact an administrator.', 'error')
            return render_template('auth/login.html', title='Sign In')
        
        # Log user in
        login_user(user, remember=remember_me)
        flash(f'Welcome back, {user.username}!', 'success')
        
        # Redirect to next page or dashboard
        next_page = request.args.get('next')
        if not next_page or not next_page.startswith('/'):
            next_page = url_for('main.dashboard')
        
        return redirect(next_page)
    
    return render_template('auth/login.html', title='Sign In')

@bp.route('/logout')
@login_required
def logout():
    """User logout route."""
    username = current_user.username
    logout_user()
    flash(f'You have been logged out, {username}.', 'info')
    return redirect(url_for('main.index'))