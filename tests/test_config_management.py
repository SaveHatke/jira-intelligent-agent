"""
Tests for configuration management functionality.

This module tests the configuration services, routes, and utilities.
"""

import pytest
import json
from unittest.mock import patch, MagicMock
from flask import url_for

from app import create_app, db
from app.models import User, Role, MCPConfiguration, AIConfiguration
from app.config_mgmt.services import (
    ConfigurationService, MCPTestService, AIConfigValidationService,
    ConfigurationUtilities
)


class TestConfigurationService:
    """Test configuration service functionality."""
    
    def test_get_user_mcp_config(self, app, test_user):
        """Test getting user MCP configuration."""
        with app.app_context():
            # Initially no config
            config = ConfigurationService.get_user_mcp_config(test_user.id)
            assert config is None
            
            # Create config
            mcp_config = MCPConfiguration(
                user_id=test_user.id,
                server_url='https://test.jira.com',
                is_active=True
            )
            mcp_config.set_personal_access_token('test-token')
            db.session.add(mcp_config)
            db.session.commit()
            
            # Should find config
            config = ConfigurationService.get_user_mcp_config(test_user.id)
            assert config is not None
            assert config.server_url == 'https://test.jira.com'
            assert config.get_personal_access_token() == 'test-token'
    
    def test_save_mcp_config(self, app, test_user):
        """Test saving MCP configuration."""
        with app.app_context():
            config_data = {
                'server_url': 'https://test.jira.com',
                'personal_access_token': 'test-token-123',
                'additional_params': {'timeout': 30},
                'is_active': True
            }
            
            success, errors, config = ConfigurationService.save_mcp_config(
                test_user.id, config_data
            )
            
            assert success is True
            assert len(errors) == 0
            assert config is not None
            assert config.server_url == 'https://test.jira.com'
            assert config.get_personal_access_token() == 'test-token-123'
            assert config.additional_params == {'timeout': 30}
    
    def test_save_mcp_config_validation_errors(self, app, test_user):
        """Test MCP config validation errors."""
        with app.app_context():
            config_data = {
                'server_url': '',  # Invalid - empty
                'personal_access_token': '',  # Invalid - empty
                'additional_params': {},
                'is_active': True
            }
            
            success, errors, config = ConfigurationService.save_mcp_config(
                test_user.id, config_data
            )
            
            assert success is False
            assert len(errors) > 0
            assert 'Server URL is required' in errors
            assert 'Personal Access Token is required' in errors
    
    def test_save_ai_config(self, app, test_user):
        """Test saving AI configuration."""
        with app.app_context():
            config_data = {
                'custom_headers': {'Authorization': 'Bearer test-key'},
                'user_id_from_jira': 'test-user',
                'model_configs': {'model': 'gpt-4', 'temperature': 0.7}
            }
            
            success, errors, config = ConfigurationService.save_ai_config(
                test_user.id, config_data
            )
            
            assert success is True
            assert len(errors) == 0
            assert config is not None
            assert config.get_custom_headers() == {'Authorization': 'Bearer test-key'}
            assert config.user_id_from_jira == 'test-user'
            assert config.model_configs == {'model': 'gpt-4', 'temperature': 0.7}


class TestMCPTestService:
    """Test MCP connection testing service."""
    
    @pytest.mark.asyncio
    async def test_test_connection_success(self, app, test_user):
        """Test successful MCP connection."""
        with app.app_context():
            config = MCPConfiguration(
                user_id=test_user.id,
                server_url='https://test.jira.com',
                is_active=True
            )
            config.set_personal_access_token('test-token')
            db.session.add(config)
            db.session.commit()
            
            success, message, user_info = await MCPTestService.test_connection(config, 'jira')
            
            assert success is True
            assert 'successful' in message.lower()
            assert 'user_name' in user_info
            assert 'user_id' in user_info
    
    @pytest.mark.asyncio
    async def test_test_connection_missing_credentials(self, app, test_user):
        """Test connection with missing credentials."""
        with app.app_context():
            config = MCPConfiguration(
                user_id=test_user.id,
                server_url='',  # Missing URL
                is_active=True
            )
            db.session.add(config)
            db.session.commit()
            
            success, message, user_info = await MCPTestService.test_connection(config, 'jira')
            
            assert success is False
            assert 'Missing' in message
            assert user_info == {}


class TestAIConfigValidationService:
    """Test AI configuration validation service."""
    
    @pytest.mark.asyncio
    async def test_validate_ai_config_success(self, app, test_user):
        """Test successful AI config validation."""
        with app.app_context():
            config = AIConfiguration(
                user_id=test_user.id,
                user_id_from_jira='test-user'
            )
            config.set_custom_headers({'Authorization': 'Bearer test-key'})
            db.session.add(config)
            db.session.commit()
            
            success, message, validation_info = await AIConfigValidationService.validate_ai_config(config)
            
            assert success is True
            assert 'validated successfully' in message.lower()
            assert 'headers_valid' in validation_info
            assert validation_info['headers_valid'] is True


class TestConfigurationUtilities:
    """Test configuration utility functions."""
    
    def test_validate_json_string_valid(self):
        """Test valid JSON string validation."""
        json_str = '{"key": "value", "number": 123}'
        is_valid, error_msg, parsed_data = ConfigurationUtilities.validate_json_string(json_str)
        
        assert is_valid is True
        assert error_msg == ''
        assert parsed_data == {"key": "value", "number": 123}
    
    def test_validate_json_string_invalid(self):
        """Test invalid JSON string validation."""
        json_str = '{"key": "value", "invalid": }'
        is_valid, error_msg, parsed_data = ConfigurationUtilities.validate_json_string(json_str)
        
        assert is_valid is False
        assert 'Invalid JSON' in error_msg
        assert parsed_data is None
    
    def test_validate_json_string_empty(self):
        """Test empty JSON string validation."""
        json_str = ''
        is_valid, error_msg, parsed_data = ConfigurationUtilities.validate_json_string(json_str)
        
        assert is_valid is True
        assert error_msg == ''
        assert parsed_data == {}
    
    def test_sanitize_url(self):
        """Test URL sanitization."""
        # Test adding https
        url = ConfigurationUtilities.sanitize_url('example.com')
        assert url == 'https://example.com'
        
        # Test removing trailing slash
        url = ConfigurationUtilities.sanitize_url('https://example.com/')
        assert url == 'https://example.com'
        
        # Test preserving existing protocol
        url = ConfigurationUtilities.sanitize_url('http://example.com')
        assert url == 'http://example.com'
    
    def test_mask_sensitive_data(self):
        """Test sensitive data masking."""
        data = {
            'personal_access_token': 'secret123456',
            'api_key': 'key789',
            'normal_field': 'visible_value'
        }
        
        masked = ConfigurationUtilities.mask_sensitive_data(data)
        
        assert masked['personal_access_token'] == 'secr************'
        assert masked['api_key'] == '****'
        assert masked['normal_field'] == 'visible_value'
    
    def test_get_default_configs(self):
        """Test default configuration getters."""
        mcp_defaults = ConfigurationUtilities.get_default_mcp_params()
        assert 'timeout' in mcp_defaults
        assert 'max_retries' in mcp_defaults
        
        ai_defaults = ConfigurationUtilities.get_default_ai_model_configs()
        assert 'model' in ai_defaults
        assert 'temperature' in ai_defaults


class TestConfigurationRoutes:
    """Test configuration management routes."""
    
    def test_config_index_requires_login(self, client):
        """Test that config index requires authentication."""
        response = client.get('/config/')
        assert response.status_code == 302  # Redirect to login
    
    def test_config_index_authenticated(self, client, auth_user):
        """Test config index with authenticated user."""
        response = client.get('/config/')
        assert response.status_code == 200
        assert b'Configuration Management' in response.data
    
    def test_mcp_config_page(self, client, auth_user):
        """Test MCP configuration page."""
        response = client.get('/config/mcp')
        assert response.status_code == 200
        assert b'MCP Configuration' in response.data
        assert b'Server URL' in response.data
        assert b'Personal Access Token' in response.data
    
    def test_ai_config_page(self, client, auth_user):
        """Test AI configuration page."""
        response = client.get('/config/ai')
        assert response.status_code == 200
        assert b'AI Configuration' in response.data
        assert b'Custom Headers' in response.data
        assert b'Model Configurations' in response.data
    
    def test_save_mcp_config_post(self, client, auth_user):
        """Test saving MCP configuration via POST."""
        data = {
            'server_url': 'https://test.jira.com',
            'personal_access_token': 'test-token',
            'additional_params': '{"timeout": 30}',
            'is_active': 'on'
        }
        
        response = client.post('/config/mcp', data=data, follow_redirects=True)
        assert response.status_code == 200
        assert b'saved successfully' in response.data
    
    def test_save_ai_config_post(self, client, auth_user):
        """Test saving AI configuration via POST."""
        data = {
            'custom_headers': '{"Authorization": "Bearer test-key"}',
            'user_id_from_jira': 'test-user',
            'model_configs': '{"model": "gpt-4", "temperature": 0.7}'
        }
        
        response = client.post('/config/ai', data=data, follow_redirects=True)
        assert response.status_code == 200
        assert b'saved successfully' in response.data
    
    def test_config_status_api(self, client, auth_user):
        """Test configuration status API endpoint."""
        response = client.get('/config/status')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'mcp_configured' in data
        assert 'ai_configured' in data
        assert 'configuration_complete' in data
    
    def test_export_config_api(self, client, auth_user):
        """Test configuration export API endpoint."""
        response = client.get('/config/export')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'user_id' in data
        assert 'username' in data
        assert 'export_timestamp' in data
        assert 'mcp_configuration' in data
        assert 'ai_configuration' in data


# Fixtures for testing
@pytest.fixture
def test_user(app):
    """Create a test user."""
    with app.app_context():
        user = User(username='testuser', email='test@example.com')
        user.set_password('testpass')
        db.session.add(user)
        db.session.commit()
        return user


@pytest.fixture
def auth_user(client, test_user):
    """Authenticate a test user."""
    with client.session_transaction() as sess:
        sess['_user_id'] = str(test_user.id)
        sess['_fresh'] = True
    return test_user