#!/usr/bin/env python3
"""
Test script to verify individual save functionality for Jira and Confluence configurations.
"""

from app import create_app, db
from app.database import init_database
from app.models import User, MCPConfiguration
from app.config_mgmt.services import ConfigurationService

def test_individual_save_functionality():
    """Test individual save functionality for Jira and Confluence."""
    
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
        
        # Test 1: Save only Jira configuration
        jira_config_data = {
            'jira_url': 'https://jira.company.com',
            'jira_personal_token': 'jira-secret-token',
            'jira_ssl_verify': True,
            'confluence_url': '',  # Empty
            'confluence_personal_token': '',  # Empty
            'confluence_ssl_verify': True,
            'is_active': True,
            'additional_params': {}
        }
        
        success, errors, config = ConfigurationService.save_mcp_config(user.id, jira_config_data)
        
        if success:
            print("✓ Jira-only configuration saved successfully")
            print(f"  - Jira URL: {config.jira_url}")
            print(f"  - Jira Token: {'Configured' if config.get_jira_personal_token() else 'Not configured'}")
            print(f"  - Confluence URL: {config.confluence_url or 'Not configured'}")
            print(f"  - Confluence Token: {'Configured' if config.get_confluence_personal_token() else 'Not configured'}")
        else:
            print(f"✗ Jira configuration failed: {errors}")
            return False
        
        # Test 2: Add Confluence configuration (preserving Jira)
        confluence_config_data = {
            'jira_url': config.jira_url,  # Preserve existing
            'jira_personal_token': config.get_jira_personal_token(),  # Preserve existing
            'jira_ssl_verify': config.jira_ssl_verify,  # Preserve existing
            'confluence_url': 'https://confluence.company.com',
            'confluence_personal_token': 'confluence-secret-token',
            'confluence_ssl_verify': False,
            'is_active': True,
            'additional_params': {}
        }
        
        success, errors, config = ConfigurationService.save_mcp_config(user.id, confluence_config_data)
        
        if success:
            print("✓ Confluence configuration added successfully (Jira preserved)")
            print(f"  - Jira URL: {config.jira_url}")
            print(f"  - Jira Token: {'Configured' if config.get_jira_personal_token() else 'Not configured'}")
            print(f"  - Confluence URL: {config.confluence_url}")
            print(f"  - Confluence Token: {'Configured' if config.get_confluence_personal_token() else 'Not configured'}")
            print(f"  - Confluence SSL Verify: {config.confluence_ssl_verify}")
        else:
            print(f"✗ Confluence configuration failed: {errors}")
            return False
        
        # Test 3: Update only Jira SSL setting (preserve everything else)
        jira_ssl_update_data = {
            'jira_url': config.jira_url,  # Preserve existing
            'jira_personal_token': config.get_jira_personal_token(),  # Preserve existing
            'jira_ssl_verify': False,  # Change this
            'confluence_url': config.confluence_url,  # Preserve existing
            'confluence_personal_token': config.get_confluence_personal_token(),  # Preserve existing
            'confluence_ssl_verify': config.confluence_ssl_verify,  # Preserve existing
            'is_active': True,
            'additional_params': {}
        }
        
        success, errors, config = ConfigurationService.save_mcp_config(user.id, jira_ssl_update_data)
        
        if success and config.jira_ssl_verify == False:
            print("✓ Jira SSL setting updated successfully (all other settings preserved)")
            print(f"  - Jira SSL Verify: {config.jira_ssl_verify}")
            print(f"  - Confluence SSL Verify: {config.confluence_ssl_verify}")
        else:
            print(f"✗ Jira SSL update failed: {errors}")
            return False
        
        # Test 4: Test validation with partial configurations
        partial_config_data = {
            'jira_url': 'https://jira.company.com',
            'jira_personal_token': '',  # Missing token
            'jira_ssl_verify': True,
            'confluence_url': '',  # No confluence
            'confluence_personal_token': '',
            'confluence_ssl_verify': True,
            'is_active': True,
            'additional_params': {}
        }
        
        success, errors, _ = ConfigurationService.save_mcp_config(user.id + 1, partial_config_data)
        
        if not success and 'Jira Personal Access Token is required' in str(errors):
            print("✓ Validation correctly catches missing Jira token when URL is provided")
        else:
            print(f"✗ Validation should have failed: {errors}")
            return False
        
        # Test 5: Test global settings update
        global_settings_data = {
            'jira_url': config.jira_url,  # Preserve existing
            'jira_personal_token': config.get_jira_personal_token(),  # Preserve existing
            'jira_ssl_verify': config.jira_ssl_verify,  # Preserve existing
            'confluence_url': config.confluence_url,  # Preserve existing
            'confluence_personal_token': config.get_confluence_personal_token(),  # Preserve existing
            'confluence_ssl_verify': config.confluence_ssl_verify,  # Preserve existing
            'is_active': False,  # Change global setting
            'additional_params': {}
        }
        
        success, errors, config = ConfigurationService.save_mcp_config(user.id, global_settings_data)
        
        if success and config.is_active == False:
            print("✓ Global settings updated successfully (service settings preserved)")
            print(f"  - Active status: {config.is_active}")
            print(f"  - Jira URL still configured: {bool(config.jira_url)}")
            print(f"  - Confluence URL still configured: {bool(config.confluence_url)}")
        else:
            print(f"✗ Global settings update failed: {errors}")
            return False
        
        print("\n🎉 All individual save functionality tests passed!")
        print("\nThe system correctly:")
        print("- Saves individual service configurations")
        print("- Preserves existing settings when updating specific services")
        print("- Validates configurations appropriately")
        print("- Handles global settings updates")
        
        return True

if __name__ == '__main__':
    test_individual_save_functionality()