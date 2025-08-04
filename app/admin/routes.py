"""
Admin routes for user management.

Provides CRUD operations for users and role assignment functionality.
"""

from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app.admin import bp
from app.auth.decorators import admin_required
from app.models import User, Role, db
from app.admin.forms import UserForm, EditUserForm
import logging

logger = logging.getLogger(__name__)


@bp.route('/users')
@login_required
@admin_required
def users():
    """Display list of all users with management options."""
    try:
        # Get all users with their roles
        users = User.query.order_by(User.created_at.desc()).all()
        
        # Get all available roles for role assignment
        roles = Role.query.order_by(Role.name).all()
        
        return render_template('admin/users.html',
                             title='User Management',
                             users=users,
                             roles=roles)
    except Exception as e:
        logger.error(f"Error loading users page: {str(e)}")
        flash('Error loading users. Please try again.', 'error')
        return redirect(url_for('main.dashboard'))


@bp.route('/users/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_user():
    """Create a new user."""
    form = UserForm()
    
    # Populate role choices
    form.roles.choices = [(role.id, role.name.replace('_', ' ').title()) 
                         for role in Role.query.order_by(Role.name).all()]
    
    if form.validate_on_submit():
        try:
            # Check if username or email already exists
            existing_user = User.query.filter(
                (User.username == form.username.data) | 
                (User.email == form.email.data)
            ).first()
            
            if existing_user:
                if existing_user.username == form.username.data:
                    flash('Username already exists. Please choose a different username.', 'error')
                else:
                    flash('Email already exists. Please use a different email address.', 'error')
                return render_template('admin/create_user.html', title='Create User', form=form)
            
            # Create new user
            user = User(
                username=form.username.data,
                email=form.email.data,
                is_active=form.is_active.data
            )
            user.set_password(form.password.data)
            
            # Add selected roles
            selected_roles = Role.query.filter(Role.id.in_(form.roles.data)).all()
            user.roles = selected_roles
            
            db.session.add(user)
            db.session.commit()
            
            flash(f'User {user.username} created successfully!', 'success')
            logger.info(f"Admin {current_user.username} created user {user.username}")
            
            return redirect(url_for('admin.users'))
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating user: {str(e)}")
            flash('Error creating user. Please try again.', 'error')
    
    return render_template('admin/create_user.html', title='Create User', form=form)


@bp.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(user_id):
    """Edit an existing user."""
    user = User.query.get_or_404(user_id)
    form = EditUserForm(obj=user)
    
    # Populate role choices
    form.roles.choices = [(role.id, role.name.replace('_', ' ').title()) 
                         for role in Role.query.order_by(Role.name).all()]
    
    # Set current roles as selected
    if request.method == 'GET':
        form.roles.data = [role.id for role in user.roles]
    
    if form.validate_on_submit():
        try:
            # Check if username or email conflicts with other users
            existing_user = User.query.filter(
                ((User.username == form.username.data) | 
                 (User.email == form.email.data)) &
                (User.id != user_id)
            ).first()
            
            if existing_user:
                if existing_user.username == form.username.data:
                    flash('Username already exists. Please choose a different username.', 'error')
                else:
                    flash('Email already exists. Please use a different email address.', 'error')
                return render_template('admin/edit_user.html', title='Edit User', form=form, user=user)
            
            # Update user details
            user.username = form.username.data
            user.email = form.email.data
            user.is_active = form.is_active.data
            
            # Update password if provided
            if form.password.data:
                user.set_password(form.password.data)
            
            # Update roles
            selected_roles = Role.query.filter(Role.id.in_(form.roles.data)).all()
            user.roles = selected_roles
            
            db.session.commit()
            
            flash(f'User {user.username} updated successfully!', 'success')
            logger.info(f"Admin {current_user.username} updated user {user.username}")
            
            return redirect(url_for('admin.users'))
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating user {user_id}: {str(e)}")
            flash('Error updating user. Please try again.', 'error')
    
    return render_template('admin/edit_user.html', title='Edit User', form=form, user=user)


@bp.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    """Delete a user."""
    user = User.query.get_or_404(user_id)
    
    # Prevent admin from deleting themselves
    if user.id == current_user.id:
        flash('You cannot delete your own account.', 'error')
        return redirect(url_for('admin.users'))
    
    try:
        username = user.username
        db.session.delete(user)
        db.session.commit()
        
        flash(f'User {username} deleted successfully!', 'success')
        logger.info(f"Admin {current_user.username} deleted user {username}")
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting user {user_id}: {str(e)}")
        flash('Error deleting user. Please try again.', 'error')
    
    return redirect(url_for('admin.users'))


@bp.route('/users/<int:user_id>/toggle-status', methods=['POST'])
@login_required
@admin_required
def toggle_user_status(user_id):
    """Toggle user active/inactive status."""
    user = User.query.get_or_404(user_id)
    
    # Prevent admin from deactivating themselves
    if user.id == current_user.id:
        return jsonify({'success': False, 'message': 'You cannot deactivate your own account.'})
    
    try:
        user.is_active = not user.is_active
        db.session.commit()
        
        status = 'activated' if user.is_active else 'deactivated'
        logger.info(f"Admin {current_user.username} {status} user {user.username}")
        
        return jsonify({
            'success': True, 
            'message': f'User {user.username} {status} successfully!',
            'is_active': user.is_active
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error toggling user status {user_id}: {str(e)}")
        return jsonify({'success': False, 'message': 'Error updating user status.'})


@bp.route('/users/<int:user_id>/roles', methods=['POST'])
@login_required
@admin_required
def update_user_roles(user_id):
    """Update user roles via AJAX."""
    user = User.query.get_or_404(user_id)
    
    try:
        role_ids = request.json.get('role_ids', [])
        selected_roles = Role.query.filter(Role.id.in_(role_ids)).all()
        
        user.roles = selected_roles
        db.session.commit()
        
        role_names = [role.name.replace('_', ' ').title() for role in selected_roles]
        logger.info(f"Admin {current_user.username} updated roles for user {user.username}: {role_names}")
        
        return jsonify({
            'success': True,
            'message': f'Roles updated for {user.username}',
            'roles': role_names
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating roles for user {user_id}: {str(e)}")
        return jsonify({'success': False, 'message': 'Error updating user roles.'})


@bp.route('/users/<int:user_id>')
@login_required
@admin_required
def view_user(user_id):
    """View detailed user information."""
    user = User.query.get_or_404(user_id)
    
    return render_template('admin/view_user.html',
                         title=f'User: {user.username}',
                         user=user)


@bp.route('/roles')
@login_required
@admin_required
def roles():
    """Display list of all roles."""
    try:
        roles = Role.query.order_by(Role.name).all()
        
        return render_template('admin/roles.html',
                             title='Role Management',
                             roles=roles)
    except Exception as e:
        logger.error(f"Error loading roles page: {str(e)}")
        flash('Error loading roles. Please try again.', 'error')
        return redirect(url_for('main.dashboard'))


@bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    """Admin dashboard with system overview."""
    try:
        # Get system statistics
        total_users = User.query.count()
        active_users = User.query.filter_by(is_active=True).count()
        inactive_users = total_users - active_users
        
        # Get role distribution
        roles = Role.query.all()
        role_stats = []
        for role in roles:
            count = User.query.join(User.roles).filter(Role.id == role.id).count()
            role_stats.append({
                'name': role.name.replace('_', ' ').title(),
                'count': count,
                'description': role.description
            })
        
        # Get recent users (last 10)
        recent_users = User.query.order_by(User.created_at.desc()).limit(10).all()
        
        return render_template('admin/dashboard.html',
                             title='Admin Dashboard',
                             total_users=total_users,
                             active_users=active_users,
                             inactive_users=inactive_users,
                             role_stats=role_stats,
                             recent_users=recent_users)
                             
    except Exception as e:
        logger.error(f"Error loading admin dashboard: {str(e)}")
        flash('Error loading admin dashboard. Please try again.', 'error')
        return redirect(url_for('main.dashboard'))