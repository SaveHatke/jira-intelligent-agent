#!/usr/bin/env python3
"""
Test script to verify the updated MCP configuration functionality with separate Jira/Confluence settings.
"""

from app import create_app, db
from app.database import init_database
from app.models import User, MCPConfiguration
from app.config_mgmt.services import ConfigurationService

def test_updated_mcp_configuration():
    """Test the updated MCP configuration with separate Jira/Confluence settings."""
    
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
        
        # Test separate Jira and Confluence configuration
        config_data = {
            'jira_url': 'https://test-jira.company.com',
            'jira_personal_token': 'jira-token-123',
            'jira_ssl_verify': True,
            'confluence_url': 'https://test-confluence.company.com',
            'confluence_personal_token': 'confluence-token-456',
            'confluence_ssl_verify': False,
            'additional_params': {'timeout': 30, 'max_retries': 3},
            'is_active': True
        }
        
        success, errors, mcp_config = ConfigurationService.save_mcp_config(user.id, config_data)
        
        if success:
            print("✓ MCP configuration with separate Jira/Confluence settings saved successfully")
            print(f"  - Jira URL: {mcp_config.jira_url}")
            print(f"  - Jira Token configured: {bool(mcp_config.get_jira_personal_token())}")
            print(f"  - Jira SSL Verify: {mcp_config.jira_ssl_verify}")
            print(f"  - Confluence URL: {mcp_config.confluence_url}")
            print(f"  - Confluence Token configured: {bool(mcp_config.get_confluence_personal_token())}")
            print(f"  - Confluence SSL Verify: {mcp_config.confluence_ssl_verify}")
        else:
            print(f"✗ MCP configuration failed: {errors}")
            return False
        
        # Test configuration retrieval
        retrieved_config = ConfigurationService.get_user_mcp_config(user.id)
        
        if retrieved_config:
            print("✓ Configuration retrieval working")
            
            # Test token decryption
            jira_token = retrieved_config.get_jira_personal_token()
            confluence_token = retrieved_config.get_confluence_personal_token()
            
            if jira_token == 'jira-token-123' and confluence_token == 'confluence-token-456':
                print("✓ Token encryption/decryption working correctly")
            else:
                print(f"✗ Token encryption/decryption failed: Jira={jira_token}, Confluence={confluence_token}")
                return False
        else:
            print("✗ Configuration retrieval failed")
            return False
        
        # Test validation with missing data
        invalid_config_data = {
            'jira_url': 'https://test-jira.company.com',
            # Missing jira_personal_token
            'confluence_url': '',  # Empty confluence URL
            'confluence_personal_token': 'confluence-token',  # Token without URL
            'is_active': True
        }
        
        success, errors, _ = ConfigurationService.save_mcp_config(user.id + 1, invalid_config_data)
        
        if not success and len(errors) > 0:
            print("✓ Validation working correctly for invalid configurations")
            print(f"  - Validation errors: {errors}")
        else:
            print("✗ Validation should have failed for invalid configuration")
            return False
        
        # Test to_dict method
        config_dict = retrieved_config.to_dict(include_token=True)
        expected_fields = ['jira_url', 'jira_personal_token', 'confluence_url', 'confluence_personal_token']
        
        if all(field in config_dict for field in expected_fields):
            print("✓ to_dict method includes new Jira/Confluence fields")
        else:
            print(f"✗ to_dict method missing fields: {config_dict.keys()}")
            return False
        
        print("\n🎉 All updated MCP configuration functionality tests passed!")
        print("\nMCP Server Configuration Preview:")
        print(f"""{{
  "mcpServers": {{
    "mcp-atlassian": {{
      "command": "docker",
      "args": ["run", "--rm", "-i", "-e", "JIRA_URL", "-e", "JIRA_PERSONAL_TOKEN", "-e", "JIRA_SSL_VERIFY", "-e", "CONFLUENCE_URL", "-e", "CONFLUENCE_PERSONAL_TOKEN", "-e", "CONFLUENCE_SSL_VERIFY", "ghcr.io/sooperset/mcp-atlassian:latest"],
      "env": {{
        "JIRA_URL": "{mcp_config.jira_url}",
        "JIRA_PERSONAL_TOKEN": "***",
        "JIRA_SSL_VERIFY": "{str(mcp_config.jira_ssl_verify).lower()}",
        "CONFLUENCE_URL": "{mcp_config.confluence_url}",
        "CONFLUENCE_PERSONAL_TOKEN": "***",
        "CONFLUENCE_SSL_VERIFY": "{str(mcp_config.confluence_ssl_verify).lower()}"
      }}
    }}
  }}
}}""")
        
        return True

if __name__ == '__main__':
    test_updated_mcp_configuration()