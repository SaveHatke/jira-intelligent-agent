"""
Forms for admin user management.

Provides WTForms for creating and editing users with validation.
"""

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SelectMultipleField, TextAreaField
from wtforms.validators import DataRequired, Email, Length, Optional, EqualTo
from wtforms.widgets import CheckboxInput, ListWidget


class MultiCheckboxField(SelectMultipleField):
    """Custom field for multiple checkboxes."""
    widget = ListWidget(prefix_label=False)
    option_widget = CheckboxInput()


class UserForm(FlaskForm):
    """Form for creating a new user."""
    username = StringField('Username', validators=[
        DataRequired(message='Username is required'),
        Length(min=3, max=50, message='Username must be between 3 and 50 characters')
    ])
    
    email = StringField('Email', validators=[
        DataRequired(message='Email is required'),
        Email(message='Please enter a valid email address'),
        Length(max=100, message='Email must be less than 100 characters')
    ])
    
    password = PasswordField('Password', validators=[
        DataRequired(message='Password is required'),
        Length(min=6, message='Password must be at least 6 characters long')
    ])
    
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(message='Please confirm your password'),
        EqualTo('password', message='Passwords must match')
    ])
    
    roles = MultiCheckboxField('Roles', coerce=int, validators=[
        DataRequired(message='At least one role must be selected')
    ])
    
    is_active = BooleanField('Active User', default=True)
    
    def validate(self, extra_validators=None):
        """Custom validation for the form."""
        if not super().validate(extra_validators):
            return False
        
        # Additional validation can be added here
        return True


class EditUserForm(FlaskForm):
    """Form for editing an existing user."""
    username = StringField('Username', validators=[
        DataRequired(message='Username is required'),
        Length(min=3, max=50, message='Username must be between 3 and 50 characters')
    ])
    
    email = StringField('Email', validators=[
        DataRequired(message='Email is required'),
        Email(message='Please enter a valid email address'),
        Length(max=100, message='Email must be less than 100 characters')
    ])
    
    password = PasswordField('New Password', validators=[
        Optional(),
        Length(min=6, message='Password must be at least 6 characters long')
    ])
    
    confirm_password = PasswordField('Confirm New Password', validators=[
        EqualTo('password', message='Passwords must match')
    ])
    
    roles = MultiCheckboxField('Roles', coerce=int, validators=[
        DataRequired(message='At least one role must be selected')
    ])
    
    is_active = BooleanField('Active User')
    
    def validate(self, extra_validators=None):
        """Custom validation for the form."""
        if not super().validate(extra_validators):
            return False
        
        # If password is provided, confirm password is required
        if self.password.data and not self.confirm_password.data:
            self.confirm_password.errors.append('Please confirm your new password')
            return False
        
        return True


class RoleAssignmentForm(FlaskForm):
    """Form for quick role assignment."""
    roles = MultiCheckboxField('Roles', coerce=int)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Role choices will be set in the route