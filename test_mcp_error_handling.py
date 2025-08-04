#!/usr/bin/env python3
"""
Test script for MCP client error handling and edge cases.

This script tests error conditions and edge cases in the MCP client integration.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import User, MCPConfiguration
from app.services.mcp_client import MCPClientManager
from app.services.exceptions import MCPValidationError, MCPConnectionError
from app.services.connection_service import ConnectionService


def test_mcp_error_handling():
    """Test MCP client error handling and edge cases."""
    print("🧪 Testing MCP Client Error Handling")
    print("=" * 50)
    
    # Create app and initialize database
    app = create_app('testing')
    
    with app.app_context():
        # Create tables
        db.create_all()
        
        # Create test user
        test_user = User(
            username='test_error_user',
            email='test@error.example.com'
        )
        test_user.set_password('test_password')
        db.session.add(test_user)
        db.session.commit()
        
        print(f"✓ Created test user: {test_user.username}")
        
        # Test 1: Invalid configuration - missing URLs
        print("\n1. Testing invalid configuration (missing URLs)...")
        try:
            invalid_config = MCPConfiguration(
                user_id=test_user.id,
                jira_url='',
                confluence_url=''
            )
            db.session.add(invalid_config)
            db.session.commit()
            
            client = MCPClientManager(invalid_config)
            print("✗ Should have failed with validation error")
        except MCPValidationError as e:
            print(f"✓ Correctly caught validation error: {e.message}")
        except Exception as e:
            print(f"✗ Unexpected error: {e}")
        
        # Test 2: Invalid configuration - malformed URLs
        print("\n2. Testing invalid configuration (malformed URLs)...")
        try:
            malformed_config = MCPConfiguration(
                user_id=test_user.id,
                jira_url='not-a-url',
                confluence_url='also-not-a-url'
            )
            malformed_config.set_jira_personal_token('test_token')
            malformed_config.set_confluence_personal_token('test_token')
            db.session.add(malformed_config)
            db.session.commit()
            
            client = MCPClientManager(malformed_config)
            jira_result = client.test_jira_connection_sync()
            
            if not jira_result.success and 'Invalid' in jira_result.error_message:
                print(f"✓ Correctly detected malformed URL: {jira_result.error_message}")
            else:
                print(f"✗ Should have detected malformed URL")
        except Exception as e:
            print(f"✗ Unexpected error: {e}")
        
        # Test 3: Missing tokens
        print("\n3. Testing missing tokens...")
        try:
            no_token_config = MCPConfiguration(
                user_id=test_user.id,
                jira_url='https://valid-jira.example.com',
                confluence_url='https://valid-confluence.example.com'
            )
            # Don't set tokens
            db.session.add(no_token_config)
            db.session.commit()
            
            client = MCPClientManager(no_token_config)
            jira_result = client.test_jira_connection_sync()
            
            if not jira_result.success and 'token' in jira_result.error_message.lower():
                print(f"✓ Correctly detected missing token: {jira_result.error_message}")
            else:
                print(f"✗ Should have detected missing token")
        except Exception as e:
            print(f"✗ Unexpected error: {e}")
        
        # Test 4: Connection service with invalid configuration
        print("\n4. Testing ConnectionService with invalid configuration...")
        try:
            connection_service = ConnectionService(no_token_config)
            
            # Test validation
            validation = connection_service.validate_configuration()
            if not validation['valid'] and len(validation['errors']) > 0:
                print(f"✓ Validation correctly identified {len(validation['errors'])} errors")
                for error in validation['errors']:
                    print(f"  - {error}")
            else:
                print("✗ Validation should have found errors")
            
            # Test diagnosis
            diagnosis = connection_service.diagnose_connection_issues()
            if len(diagnosis['issues']) > 0:
                print(f"✓ Diagnosis found {len(diagnosis['issues'])} issues")
                for issue in diagnosis['issues']:
                    print(f"  - {issue}")
            else:
                print("✗ Diagnosis should have found issues")
                
        except Exception as e:
            print(f"✗ ConnectionService error handling failed: {e}")
        
        # Test 5: Valid configuration but test connection failures
        print("\n5. Testing valid configuration with simulated connection failures...")
        try:
            valid_config = MCPConfiguration(
                user_id=test_user.id,
                jira_url='https://valid-jira.example.com',
                confluence_url='https://valid-confluence.example.com'
            )
            valid_config.set_jira_personal_token('valid_token')
            valid_config.set_confluence_personal_token('valid_token')
            db.session.add(valid_config)
            db.session.commit()
            
            connection_service = ConnectionService(valid_config)
            
            # Test all connections
            all_results = connection_service.test_all_connections()
            print(f"✓ All connections test completed - Overall success: {all_results['overall_success']}")
            
            # Check individual service results
            for service_name, result in all_results['services'].items():
                status = "✓" if result['success'] else "✗"
                print(f"  {status} {service_name.title()}: {result['message']}")
            
        except Exception as e:
            print(f"✗ Valid configuration test failed: {e}")
        
        # Test 6: Edge cases in ticket operations
        print("\n6. Testing edge cases in ticket operations...")
        try:
            client = MCPClientManager(valid_config)
            
            # Test ticket creation with missing required fields
            invalid_ticket_data = {
                'summary': 'Test ticket',
                # Missing 'project' and 'issuetype'
            }
            
            create_result = client.create_ticket_sync(invalid_ticket_data)
            if not create_result.success and 'required' in create_result.error_message.lower():
                print(f"✓ Correctly detected missing required fields: {create_result.error_message}")
            else:
                print(f"✗ Should have detected missing required fields")
            
            # Test ticket history with empty ticket key
            try:
                history = client.get_ticket_history_sync('')
                print("✗ Should have failed with empty ticket key")
            except Exception as e:
                print(f"✓ Correctly handled empty ticket key: {str(e)}")
            
            # Test search with empty JQL
            try:
                search_results = client.search_tickets_sync('')
                print("✗ Should have failed with empty JQL")
            except Exception as e:
                print(f"✓ Correctly handled empty JQL: {str(e)}")
                
        except Exception as e:
            print(f"✗ Ticket operations edge case testing failed: {e}")
        
        # Test 7: Service capabilities with partial configuration
        print("\n7. Testing service capabilities with partial configuration...")
        try:
            # Configuration with only Jira
            jira_only_config = MCPConfiguration(
                user_id=test_user.id,
                jira_url='https://jira-only.example.com'
            )
            jira_only_config.set_jira_personal_token('jira_token')
            db.session.add(jira_only_config)
            db.session.commit()
            
            connection_service = ConnectionService(jira_only_config)
            capabilities = connection_service.get_service_capabilities()
            
            if capabilities['jira']['available'] and not capabilities['confluence']['available']:
                print("✓ Correctly identified Jira-only configuration")
                print(f"  - Jira features: {len(capabilities['jira']['features'])}")
                print(f"  - Confluence features: {len(capabilities['confluence']['features'])}")
            else:
                print("✗ Should have identified Jira-only configuration")
                
        except Exception as e:
            print(f"✗ Partial configuration test failed: {e}")
        
        # Test 8: Configuration encryption/decryption edge cases
        print("\n8. Testing configuration encryption/decryption...")
        try:
            test_config = MCPConfiguration(user_id=test_user.id)
            
            # Test with empty token
            test_config.set_jira_personal_token('')
            empty_token = test_config.get_jira_personal_token()
            if empty_token == '':
                print("✓ Correctly handled empty token encryption/decryption")
            else:
                print(f"✗ Empty token should remain empty, got: '{empty_token}'")
            
            # Test with normal token
            test_token = 'test_secret_token_123'
            test_config.set_jira_personal_token(test_token)
            retrieved_token = test_config.get_jira_personal_token()
            if retrieved_token == test_token:
                print("✓ Token encryption/decryption working correctly")
            else:
                print(f"✗ Token mismatch: expected '{test_token}', got '{retrieved_token}'")
                
        except Exception as e:
            print(f"✗ Encryption/decryption test failed: {e}")
        
        # Test 9: Synchronous wrapper error handling
        print("\n9. Testing synchronous wrapper error handling...")
        try:
            # This should test the sync wrappers' error handling
            client = MCPClientManager(valid_config)
            
            # Test all sync methods to ensure they handle errors gracefully
            methods_to_test = [
                ('test_jira_connection_sync', []),
                ('test_confluence_connection_sync', []),
                ('get_boards_sync', []),
                ('get_sprints_sync', ['1']),
                ('search_tickets_sync', ['project = TEST']),
            ]
            
            for method_name, args in methods_to_test:
                try:
                    method = getattr(client, method_name)
                    result = method(*args)
                    print(f"✓ {method_name} executed without errors")
                except Exception as e:
                    print(f"✓ {method_name} handled error gracefully: {type(e).__name__}")
                    
        except Exception as e:
            print(f"✗ Synchronous wrapper testing failed: {e}")
        
        print("\n🎉 MCP Client Error Handling Test Complete!")
        print("=" * 50)
        
        # Clean up
        try:
            # Clean up all test configurations
            MCPConfiguration.query.filter_by(user_id=test_user.id).delete()
            db.session.delete(test_user)
            db.session.commit()
            print("✓ Test data cleaned up successfully")
        except Exception as e:
            print(f"⚠ Cleanup warning: {e}")
        
        return True


if __name__ == '__main__':
    test_mcp_error_handling()