#!/usr/bin/env python3
"""
Simple test script to verify configuration management functionality.
"""

from app import create_app, db
from app.database import init_database
from app.models import User, Role, MCPConfiguration, AIConfiguration
from app.config_mgmt.services import ConfigurationService, ConfigurationUtilities

def test_configuration_functionality():
    """Test basic configuration management functionality."""
    
    # Create app and initialize database
    app = create_app('testing')
    
    with app.app_context():
        # Initialize database
        init_database()
        
        # Create a test user
        user = User(username='testuser', email='test@example.com')
        user.set_password('testpass')
        db.session.add(user)
        db.session.commit()
        
        print(f"✓ Created test user: {user.username}")
        
        # Test MCP configuration
        mcp_data = {
            'server_url': 'https://test.jira.com',
            'personal_access_token': 'test-token-123',
            'additional_params': {'timeout': 30, 'max_retries': 3},
            'is_active': True
        }
        
        success, errors, mcp_config = ConfigurationService.save_mcp_config(user.id, mcp_data)
        
        if success:
            print("✓ MCP configuration saved successfully")
            print(f"  - Server URL: {mcp_config.server_url}")
            print(f"  - Token configured: {bool(mcp_config.get_personal_access_token())}")
            print(f"  - Additional params: {mcp_config.additional_params}")
        else:
            print(f"✗ MCP configuration failed: {errors}")
            return False
        
        # Test AI configuration
        ai_data = {
            'custom_headers': {'Authorization': 'Bearer test-key', 'Content-Type': 'application/json'},
            'user_id_from_jira': 'test-user',
            'model_configs': {'model': 'gpt-4', 'temperature': 0.7, 'max_tokens': 2000}
        }
        
        success, errors, ai_config = ConfigurationService.save_ai_config(user.id, ai_data)
        
        if success:
            print("✓ AI configuration saved successfully")
            print(f"  - Custom headers: {len(ai_config.get_custom_headers())} configured")
            print(f"  - Jira User ID: {ai_config.user_id_from_jira}")
            print(f"  - Model configs: {ai_config.model_configs}")
        else:
            print(f"✗ AI configuration failed: {errors}")
            return False
        
        # Test configuration retrieval
        retrieved_mcp = ConfigurationService.get_user_mcp_config(user.id)
        retrieved_ai = ConfigurationService.get_user_ai_config(user.id)
        
        if retrieved_mcp and retrieved_ai:
            print("✓ Configuration retrieval working")
        else:
            print("✗ Configuration retrieval failed")
            return False
        
        # Test utility functions
        test_json = '{"key": "value", "number": 123}'
        is_valid, error_msg, parsed = ConfigurationUtilities.validate_json_string(test_json)
        
        if is_valid and parsed == {"key": "value", "number": 123}:
            print("✓ JSON validation utility working")
        else:
            print(f"✗ JSON validation failed: {error_msg}")
            return False
        
        # Test URL sanitization
        sanitized_url = ConfigurationUtilities.sanitize_url('example.com')
        if sanitized_url == 'https://example.com':
            print("✓ URL sanitization utility working")
        else:
            print(f"✗ URL sanitization failed: {sanitized_url}")
            return False
        
        # Test sensitive data masking
        sensitive_data = {'personal_access_token': 'secret123456', 'normal_field': 'visible'}
        masked = ConfigurationUtilities.mask_sensitive_data(sensitive_data)
        
        if ('secr' in masked['personal_access_token'] and 
            '*' in masked['personal_access_token'] and 
            masked['normal_field'] == 'visible'):
            print("✓ Sensitive data masking working")
        else:
            print(f"✗ Sensitive data masking failed: {masked}")
            return False
        
        print("\n🎉 All configuration management functionality tests passed!")
        return True

if __name__ == '__main__':
    test_configuration_functionality()