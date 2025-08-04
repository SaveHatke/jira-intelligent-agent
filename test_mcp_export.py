#!/usr/bin/env python3
"""
Test script to verify MCP server configuration export functionality.
"""

import json
from app import create_app, db
from app.database import init_database
from app.models import User, MCPConfiguration
from app.config_mgmt.services import ConfigurationService, ConfigurationUtilities

def test_mcp_export_functionality():
    """Test MCP server configuration export."""
    
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
        
        # Create MCP configuration
        config_data = {
            'jira_url': 'https://jira.company.com',
            'jira_personal_token': 'jira-secret-token',
            'jira_ssl_verify': True,
            'confluence_url': 'https://confluence.company.com',
            'confluence_personal_token': 'confluence-secret-token',
            'confluence_ssl_verify': False,
            'is_active': True
        }
        
        success, errors, mcp_config = ConfigurationService.save_mcp_config(user.id, config_data)
        
        if not success:
            print(f"✗ Failed to create MCP configuration: {errors}")
            return False
        
        print("✓ MCP configuration created successfully")
        
        # Test MCP server configuration generation
        server_config = ConfigurationUtilities.generate_mcp_server_config(mcp_config)
        
        print("✓ MCP server configuration generated")
        print("\nGenerated MCP Server Configuration:")
        print(json.dumps(server_config, indent=2))
        
        # Verify the structure
        expected_structure = {
            'mcpServers': {
                'mcp-atlassian': {
                    'command': 'docker',
                    'args': list,
                    'env': dict
                }
            }
        }
        
        # Check structure
        if 'mcpServers' in server_config:
            print("✓ Root 'mcpServers' key present")
        else:
            print("✗ Missing 'mcpServers' key")
            return False
        
        if 'mcp-atlassian' in server_config['mcpServers']:
            print("✓ 'mcp-atlassian' server configuration present")
        else:
            print("✗ Missing 'mcp-atlassian' server configuration")
            return False
        
        atlassian_config = server_config['mcpServers']['mcp-atlassian']
        
        # Check command and args
        if atlassian_config.get('command') == 'docker':
            print("✓ Docker command configured correctly")
        else:
            print("✗ Docker command not configured correctly")
            return False
        
        if isinstance(atlassian_config.get('args'), list) and 'ghcr.io/sooperset/mcp-atlassian:latest' in atlassian_config['args']:
            print("✓ Docker args configured correctly")
        else:
            print("✗ Docker args not configured correctly")
            return False
        
        # Check environment variables
        env_vars = atlassian_config.get('env', {})
        expected_env_vars = [
            'JIRA_URL', 'JIRA_PERSONAL_TOKEN', 'JIRA_SSL_VERIFY',
            'CONFLUENCE_URL', 'CONFLUENCE_PERSONAL_TOKEN', 'CONFLUENCE_SSL_VERIFY'
        ]
        
        for env_var in expected_env_vars:
            if env_var in env_vars:
                print(f"✓ Environment variable '{env_var}' present")
            else:
                print(f"✗ Missing environment variable '{env_var}'")
                return False
        
        # Check specific values
        if env_vars['JIRA_URL'] == 'https://jira.company.com':
            print("✓ Jira URL correctly set")
        else:
            print(f"✗ Jira URL incorrect: {env_vars['JIRA_URL']}")
            return False
        
        if env_vars['JIRA_PERSONAL_TOKEN'] == 'jira-secret-token':
            print("✓ Jira token correctly set")
        else:
            print("✗ Jira token not correctly set")
            return False
        
        if env_vars['JIRA_SSL_VERIFY'] == 'true':
            print("✓ Jira SSL verify correctly set")
        else:
            print(f"✗ Jira SSL verify incorrect: {env_vars['JIRA_SSL_VERIFY']}")
            return False
        
        if env_vars['CONFLUENCE_SSL_VERIFY'] == 'false':
            print("✓ Confluence SSL verify correctly set")
        else:
            print(f"✗ Confluence SSL verify incorrect: {env_vars['CONFLUENCE_SSL_VERIFY']}")
            return False
        
        print("\n🎉 All MCP server configuration export tests passed!")
        print("\nThis configuration can be directly used in your MCP client settings.")
        
        return True

if __name__ == '__main__':
    test_mcp_export_functionality()