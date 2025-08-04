"""
Database models for JIA application.

This module contains SQLAlchemy models for users, roles, and configurations.
"""

from datetime import datetime
from typing import List, Optional
import bcrypt
import json
from cryptography.fernet import Fernet
import os

from app import db, login_manager
from flask_login import UserMixin
from sqlalchemy import event
from sqlalchemy.ext.hybrid import hybrid_property


# Association table for many-to-many relationship between users and roles
user_roles = db.Table('user_roles',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('role_id', db.Integer, db.ForeignKey('roles.id'), primary_key=True)
)


class User(UserMixin, db.Model):
    """
    User model for authentication and authorization.
    
    Supports multiple roles per user and secure password storage.
    """
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False, index=True)
    email = db.Column(db.String(100), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    roles = db.relationship('Role', secondary=user_roles, lazy='subquery',
                           backref=db.backref('users', lazy=True))
    mcp_configurations = db.relationship('MCPConfiguration', backref='user', lazy=True,
                                       cascade='all, delete-orphan')
    ai_configurations = db.relationship('AIConfiguration', backref='user', lazy=True,
                                      cascade='all, delete-orphan')
    validation_criteria = db.relationship('ValidationCriteria', backref='user', lazy=True,
                                        cascade='all, delete-orphan')
    
    def set_password(self, password: str) -> None:
        """Hash and set user password."""
        salt = bcrypt.gensalt()
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    def check_password(self, password: str) -> bool:
        """Check if provided password matches stored hash."""
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))
    
    def has_role(self, role_name: str) -> bool:
        """Check if user has a specific role."""
        return any(role.name == role_name for role in self.roles)
    
    def has_any_role(self, role_names: List[str]) -> bool:
        """Check if user has any of the specified roles."""
        user_role_names = {role.name for role in self.roles}
        return bool(user_role_names.intersection(set(role_names)))
    
    def get_role_names(self) -> List[str]:
        """Get list of role names for this user."""
        return [role.name for role in self.roles]
    
    def is_admin(self) -> bool:
        """Check if user has admin privileges (tech_manager role)."""
        return self.has_role('tech_manager')
    
    def validate(self) -> List[str]:
        """Validate user data and return list of errors."""
        errors = []
        
        if not self.username or len(self.username.strip()) < 3:
            errors.append("Username must be at least 3 characters long")
        
        if not self.email or '@' not in self.email:
            errors.append("Valid email address is required")
        
        if not self.password_hash:
            errors.append("Password is required")
        
        return errors
    
    def to_dict(self) -> dict:
        """Convert user to dictionary for API responses."""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'is_active': self.is_active,
            'roles': [role.name for role in self.roles],
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<User {self.username}>'


class Role(db.Model):
    """
    Role model for role-based access control.
    
    Defines available roles in the system with descriptions.
    """
    __tablename__ = 'roles'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False, index=True)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Valid role names as class constants
    SCRUM_MASTER = 'scrum_master'
    PRODUCT_OWNER = 'product_owner'
    BUSINESS_ANALYST = 'business_analyst'
    TECH_MANAGER = 'tech_manager'
    STAKEHOLDER = 'stakeholder'
    
    VALID_ROLES = [SCRUM_MASTER, PRODUCT_OWNER, BUSINESS_ANALYST, TECH_MANAGER, STAKEHOLDER]
    
    def validate(self) -> List[str]:
        """Validate role data and return list of errors."""
        errors = []
        
        if not self.name or self.name.strip() == '':
            errors.append("Role name is required")
        elif self.name not in self.VALID_ROLES:
            errors.append(f"Role name must be one of: {', '.join(self.VALID_ROLES)}")
        
        return errors
    
    def to_dict(self) -> dict:
        """Convert role to dictionary for API responses."""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<Role {self.name}>'


class MCPConfiguration(db.Model):
    """
    MCP (Model Context Protocol) configuration for individual users.
    
    Stores encrypted connection details for Jira/Confluence access.
    """
    __tablename__ = 'mcp_configurations'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Jira configuration
    jira_url = db.Column(db.String(255))
    jira_personal_token = db.Column(db.Text)  # encrypted
    jira_ssl_verify = db.Column(db.Boolean, default=True)
    
    # Confluence configuration
    confluence_url = db.Column(db.String(255))
    confluence_personal_token = db.Column(db.Text)  # encrypted
    confluence_ssl_verify = db.Column(db.Boolean, default=True)
    
    # Legacy fields for backward compatibility
    server_url = db.Column(db.String(255))
    personal_access_token = db.Column(db.Text)  # encrypted
    additional_params = db.Column(db.JSON)
    
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    last_tested = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if 'additional_params' not in kwargs:
            self.additional_params = {}
    
    @property
    def encryption_key(self) -> bytes:
        """Get encryption key from environment or generate one."""
        key = os.getenv('ENCRYPTION_KEY')
        if not key:
            # In production, this should be set in environment
            key = Fernet.generate_key()
            os.environ['ENCRYPTION_KEY'] = key.decode()
        if isinstance(key, str):
            key = key.encode()
        return key
    
    def set_personal_access_token(self, token: str) -> None:
        """Encrypt and store personal access token (legacy method)."""
        if not token:
            self.personal_access_token = ''
            return
        
        fernet = Fernet(self.encryption_key)
        encrypted_token = fernet.encrypt(token.encode('utf-8'))
        self.personal_access_token = encrypted_token.decode('utf-8')
    
    def get_personal_access_token(self) -> str:
        """Decrypt and return personal access token (legacy method)."""
        if not self.personal_access_token:
            return ''
        
        try:
            fernet = Fernet(self.encryption_key)
            decrypted_token = fernet.decrypt(self.personal_access_token.encode('utf-8'))
            return decrypted_token.decode('utf-8')
        except Exception:
            return ''
    
    def set_jira_personal_token(self, token: str) -> None:
        """Encrypt and store Jira personal access token."""
        if not token:
            self.jira_personal_token = ''
            return
        
        fernet = Fernet(self.encryption_key)
        encrypted_token = fernet.encrypt(token.encode('utf-8'))
        self.jira_personal_token = encrypted_token.decode('utf-8')
    
    def get_jira_personal_token(self) -> str:
        """Decrypt and return Jira personal access token."""
        if not self.jira_personal_token:
            return ''
        
        try:
            fernet = Fernet(self.encryption_key)
            decrypted_token = fernet.decrypt(self.jira_personal_token.encode('utf-8'))
            return decrypted_token.decode('utf-8')
        except Exception:
            return ''
    
    def set_confluence_personal_token(self, token: str) -> None:
        """Encrypt and store Confluence personal access token."""
        if not token:
            self.confluence_personal_token = ''
            return
        
        fernet = Fernet(self.encryption_key)
        encrypted_token = fernet.encrypt(token.encode('utf-8'))
        self.confluence_personal_token = encrypted_token.decode('utf-8')
    
    def get_confluence_personal_token(self) -> str:
        """Decrypt and return Confluence personal access token."""
        if not self.confluence_personal_token:
            return ''
        
        try:
            fernet = Fernet(self.encryption_key)
            decrypted_token = fernet.decrypt(self.confluence_personal_token.encode('utf-8'))
            return decrypted_token.decode('utf-8')
        except Exception:
            return ''
    
    def set_additional_param(self, key: str, value: any) -> None:
        """Set an additional parameter."""
        if self.additional_params is None:
            self.additional_params = {}
        self.additional_params[key] = value
    
    def get_additional_param(self, key: str, default=None) -> any:
        """Get an additional parameter."""
        if self.additional_params is None:
            return default
        return self.additional_params.get(key, default)
    
    def validate(self) -> List[str]:
        """Validate MCP configuration and return list of errors."""
        errors = []
        
        # Check if at least one service (Jira or Confluence) is configured
        jira_configured = bool(self.jira_url and self.jira_personal_token)
        confluence_configured = bool(self.confluence_url and self.confluence_personal_token)
        legacy_configured = bool(self.server_url and self.personal_access_token)
        
        if not (jira_configured or confluence_configured or legacy_configured):
            errors.append("At least one service (Jira or Confluence) must be configured")
        
        # Validate Jira configuration if provided
        if self.jira_url:
            if not self.jira_url.startswith(('http://', 'https://')):
                errors.append("Jira URL must start with http:// or https://")
            if not self.jira_personal_token:
                errors.append("Jira Personal Access Token is required when Jira URL is provided")
        
        # Validate Confluence configuration if provided
        if self.confluence_url:
            if not self.confluence_url.startswith(('http://', 'https://')):
                errors.append("Confluence URL must start with http:// or https://")
            if not self.confluence_personal_token:
                errors.append("Confluence Personal Access Token is required when Confluence URL is provided")
        
        # Legacy validation for backward compatibility
        if self.server_url:
            if not self.server_url.startswith(('http://', 'https://')):
                errors.append("Server URL must start with http:// or https://")
        
        return errors
    
    def to_dict(self, include_token: bool = False) -> dict:
        """Convert configuration to dictionary for API responses."""
        data = {
            'id': self.id,
            'user_id': self.user_id,
            'jira_url': self.jira_url,
            'jira_ssl_verify': self.jira_ssl_verify,
            'confluence_url': self.confluence_url,
            'confluence_ssl_verify': self.confluence_ssl_verify,
            'server_url': self.server_url,  # Legacy field
            'additional_params': self.additional_params or {},
            'is_active': self.is_active,
            'last_tested': self.last_tested.isoformat() if self.last_tested else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
        if include_token:
            data['jira_personal_token'] = self.get_jira_personal_token()
            data['confluence_personal_token'] = self.get_confluence_personal_token()
            data['personal_access_token'] = self.get_personal_access_token()  # Legacy
        else:
            data['has_jira_token'] = bool(self.jira_personal_token)
            data['has_confluence_token'] = bool(self.confluence_personal_token)
            data['has_token'] = bool(self.personal_access_token)  # Legacy
        
        return data
    
    def __repr__(self):
        return f'<MCPConfiguration {self.id} for user {self.user_id}>'


class AIConfiguration(db.Model):
    """
    AI service configuration for individual users.
    
    Stores AI API settings and custom headers.
    """
    __tablename__ = 'ai_configurations'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    custom_headers = db.Column(db.Text)  # JSON string of custom headers
    user_id_from_jira = db.Column(db.String(100))
    model_configs = db.Column(db.JSON)
    is_validated = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if 'model_configs' not in kwargs:
            self.model_configs = {}
    
    def set_custom_headers(self, headers: dict) -> None:
        """Set custom headers as JSON string."""
        if headers:
            self.custom_headers = json.dumps(headers)
        else:
            self.custom_headers = None
    
    def get_custom_headers(self) -> dict:
        """Get custom headers as dictionary."""
        if not self.custom_headers:
            return {}
        
        try:
            return json.loads(self.custom_headers)
        except (json.JSONDecodeError, TypeError):
            return {}
    
    def set_model_config(self, key: str, value: any) -> None:
        """Set a model configuration parameter."""
        if self.model_configs is None:
            self.model_configs = {}
        self.model_configs[key] = value
    
    def get_model_config(self, key: str, default=None) -> any:
        """Get a model configuration parameter."""
        if self.model_configs is None:
            return default
        return self.model_configs.get(key, default)
    
    def validate(self) -> List[str]:
        """Validate AI configuration and return list of errors."""
        errors = []
        
        # Validate custom headers if provided
        if self.custom_headers:
            try:
                headers = json.loads(self.custom_headers)
                if not isinstance(headers, dict):
                    errors.append("Custom headers must be a valid JSON object")
            except json.JSONDecodeError:
                errors.append("Custom headers must be valid JSON")
        
        # Validate user_id_from_jira if provided
        if self.user_id_from_jira and len(self.user_id_from_jira.strip()) == 0:
            errors.append("Jira User ID cannot be empty if provided")
        
        return errors
    
    def to_dict(self) -> dict:
        """Convert configuration to dictionary for API responses."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'custom_headers': self.get_custom_headers(),
            'user_id_from_jira': self.user_id_from_jira,
            'model_configs': self.model_configs or {},
            'is_validated': self.is_validated,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<AIConfiguration {self.id} for user {self.user_id}>'


class ValidationCriteria(db.Model):
    """
    Validation criteria for ticket validation features.
    
    Stores DoR, DoD, and custom validation criteria per user.
    """
    __tablename__ = 'validation_criteria'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    criteria_type = db.Column(db.String(20), nullable=False)  # 'dor', 'dod', 'custom'
    criteria_text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Valid criteria types
    DEFINITION_OF_READY = 'dor'
    DEFINITION_OF_DONE = 'dod'
    CUSTOM = 'custom'
    
    VALID_TYPES = [DEFINITION_OF_READY, DEFINITION_OF_DONE, CUSTOM]
    
    def validate(self) -> List[str]:
        """Validate criteria and return list of errors."""
        errors = []
        
        if not self.criteria_type or self.criteria_type not in self.VALID_TYPES:
            errors.append(f"Criteria type must be one of: {', '.join(self.VALID_TYPES)}")
        
        if not self.criteria_text or self.criteria_text.strip() == '':
            errors.append("Criteria text is required")
        
        return errors
    
    def get_criteria_list(self) -> List[str]:
        """Get criteria as list of individual points."""
        if not self.criteria_text:
            return []
        
        # Split by lines and filter out empty lines
        criteria = [line.strip() for line in self.criteria_text.split('\n')]
        return [c for c in criteria if c]
    
    def to_dict(self) -> dict:
        """Convert criteria to dictionary for API responses."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'criteria_type': self.criteria_type,
            'criteria_text': self.criteria_text,
            'criteria_list': self.get_criteria_list(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<ValidationCriteria {self.criteria_type} for user {self.user_id}>'


class AdminPrompt(db.Model):
    """
    Admin-configurable prompts for AI features.
    
    Stores prompt templates and output formats for different features.
    """
    __tablename__ = 'admin_prompts'
    
    id = db.Column(db.Integer, primary_key=True)
    feature_name = db.Column(db.String(100), nullable=False, index=True)
    prompt_template = db.Column(db.Text, nullable=False)
    output_format = db.Column(db.String(50))
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def validate(self) -> List[str]:
        """Validate prompt and return list of errors."""
        errors = []
        
        if not self.feature_name or self.feature_name.strip() == '':
            errors.append("Feature name is required")
        
        if not self.prompt_template or self.prompt_template.strip() == '':
            errors.append("Prompt template is required")
        
        return errors
    
    def to_dict(self) -> dict:
        """Convert prompt to dictionary for API responses."""
        return {
            'id': self.id,
            'feature_name': self.feature_name,
            'prompt_template': self.prompt_template,
            'output_format': self.output_format,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<AdminPrompt {self.feature_name}>'


@login_manager.user_loader
def load_user(user_id):
    """Load user for Flask-Login."""
    return User.query.get(int(user_id))