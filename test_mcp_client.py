#!/usr/bin/env python3
"""
Test script for MCP client integration.

This script tests the MCPClientManager and related services to ensure
they work correctly with the JIA application.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import User, MCPConfiguration
from app.services.mcp_client import MCPClientManager
from app.services.jira_service import JiraService
from app.services.confluence_service import ConfluenceService
from app.services.connection_service import ConnectionService


def test_mcp_client_integration():
    """Test the MCP client integration functionality."""
    print("🧪 Testing MCP Client Integration")
    print("=" * 50)
    
    # Create app and initialize database
    app = create_app('testing')
    
    with app.app_context():
        # Create tables
        db.create_all()
        
        # Create test user
        test_user = User(
            username='test_mcp_user',
            email='test@mcp.example.com'
        )
        test_user.set_password('test_password')
        db.session.add(test_user)
        db.session.commit()
        
        # Create MCP configuration
        mcp_config = MCPConfiguration(
            user_id=test_user.id,
            jira_url='https://test-jira.example.com',
            jira_ssl_verify=True,
            confluence_url='https://test-confluence.example.com',
            confluence_ssl_verify=True
        )
        mcp_config.set_jira_personal_token('test_jira_token_123')
        mcp_config.set_confluence_personal_token('test_confluence_token_456')
        
        db.session.add(mcp_config)
        db.session.commit()
        
        print(f"✓ Created test user: {test_user.username}")
        print(f"✓ Created MCP configuration for user {test_user.id}")
        
        # Test 1: MCPClientManager initialization
        print("\n1. Testing MCPClientManager initialization...")
        try:
            client = MCPClientManager(mcp_config)
            print("✓ MCPClientManager initialized successfully")
        except Exception as e:
            print(f"✗ MCPClientManager initialization failed: {e}")
            return False
        
        # Test 2: Jira connection test
        print("\n2. Testing Jira connection...")
        try:
            jira_result = client.test_jira_connection_sync()
            if jira_result.success:
                print(f"✓ Jira connection test successful")
                print(f"  - User: {jira_result.user_name}")
                print(f"  - User ID: {jira_result.user_id}")
                print(f"  - Email: {jira_result.email}")
            else:
                print(f"✗ Jira connection test failed: {jira_result.error_message}")
        except Exception as e:
            print(f"✗ Jira connection test error: {e}")
        
        # Test 3: Confluence connection test
        print("\n3. Testing Confluence connection...")
        try:
            confluence_result = client.test_confluence_connection_sync()
            if confluence_result.success:
                print(f"✓ Confluence connection test successful")
                print(f"  - User: {confluence_result.user_name}")
                print(f"  - User ID: {confluence_result.user_id}")
                print(f"  - Email: {confluence_result.email}")
            else:
                print(f"✗ Confluence connection test failed: {confluence_result.error_message}")
        except Exception as e:
            print(f"✗ Confluence connection test error: {e}")
        
        # Test 4: Jira boards retrieval
        print("\n4. Testing Jira boards retrieval...")
        try:
            boards = client.get_boards_sync()
            print(f"✓ Retrieved {len(boards)} Jira boards")
            for board in boards:
                print(f"  - {board.name} ({board.type}) - {board.project_key}")
        except Exception as e:
            print(f"✗ Jira boards retrieval failed: {e}")
        
        # Test 5: Jira sprints retrieval
        print("\n5. Testing Jira sprints retrieval...")
        try:
            sprints = client.get_sprints_sync('1')  # Using board ID 1
            print(f"✓ Retrieved {len(sprints)} sprints for board 1")
            for sprint in sprints:
                print(f"  - {sprint.name} ({sprint.state})")
        except Exception as e:
            print(f"✗ Jira sprints retrieval failed: {e}")
        
        # Test 6: JiraService integration
        print("\n6. Testing JiraService integration...")
        try:
            jira_service = JiraService(mcp_config)
            connection_result = jira_service.test_connection()
            if connection_result['success']:
                print("✓ JiraService connection test successful")
                
                # Test boards retrieval through service
                boards = jira_service.get_boards()
                print(f"✓ JiraService retrieved {len(boards)} boards")
                
                # Test sprints retrieval through service
                sprints = jira_service.get_sprints('1')
                print(f"✓ JiraService retrieved sprints: {len(sprints['active'])} active, {len(sprints['future'])} future, {len(sprints['closed'])} closed")
                
            else:
                print(f"✗ JiraService connection test failed: {connection_result['message']}")
        except Exception as e:
            print(f"✗ JiraService integration failed: {e}")
        
        # Test 7: ConfluenceService integration
        print("\n7. Testing ConfluenceService integration...")
        try:
            confluence_service = ConfluenceService(mcp_config)
            connection_result = confluence_service.test_connection()
            if connection_result['success']:
                print("✓ ConfluenceService connection test successful")
                
                # Test spaces retrieval through service
                spaces = confluence_service.get_spaces()
                print(f"✓ ConfluenceService retrieved {len(spaces)} spaces")
                
                # Test pages retrieval through service
                pages = confluence_service.get_pages('DEV')
                print(f"✓ ConfluenceService retrieved {pages['total']} pages from DEV space")
                
            else:
                print(f"✗ ConfluenceService connection test failed: {connection_result['message']}")
        except Exception as e:
            print(f"✗ ConfluenceService integration failed: {e}")
        
        # Test 8: ConnectionService integration
        print("\n8. Testing ConnectionService integration...")
        try:
            connection_service = ConnectionService(mcp_config)
            
            # Test all connections
            all_results = connection_service.test_all_connections()
            print(f"✓ ConnectionService tested all connections - Overall success: {all_results['overall_success']}")
            
            # Test configuration validation
            validation = connection_service.validate_configuration()
            print(f"✓ Configuration validation - Valid: {validation['valid']}, Errors: {len(validation['errors'])}, Warnings: {len(validation['warnings'])}")
            
            # Test connection status
            status = connection_service.get_connection_status()
            print(f"✓ Connection status - Jira configured: {status['jira']['configured']}, Confluence configured: {status['confluence']['configured']}")
            
            # Test service capabilities
            capabilities = connection_service.get_service_capabilities()
            print(f"✓ Service capabilities - Jira features: {len(capabilities['jira']['features'])}, Confluence features: {len(capabilities['confluence']['features'])}")
            
        except Exception as e:
            print(f"✗ ConnectionService integration failed: {e}")
        
        # Test 9: Ticket operations
        print("\n9. Testing ticket operations...")
        try:
            # Test ticket creation
            ticket_data = {
                'summary': 'Test ticket from MCP client',
                'description': 'This is a test ticket created through the MCP client integration',
                'project': 'DEV',
                'issuetype': 'Story'
            }
            
            create_result = client.create_ticket_sync(ticket_data)
            if create_result.success:
                print(f"✓ Ticket creation successful: {create_result.ticket_key}")
                
                # Test ticket history retrieval
                history = client.get_ticket_history_sync(create_result.ticket_key)
                print(f"✓ Ticket history retrieved: {len(history.changelog)} changelog entries, {len(history.comments)} comments")
                
            else:
                print(f"✗ Ticket creation failed: {create_result.error_message}")
        except Exception as e:
            print(f"✗ Ticket operations failed: {e}")
        
        # Test 10: Ticket search
        print("\n10. Testing ticket search...")
        try:
            search_results = client.search_tickets_sync('project = DEV')
            print(f"✓ Ticket search successful: found {len(search_results)} tickets")
            for ticket in search_results[:3]:  # Show first 3 tickets
                print(f"  - {ticket.key}: {ticket.summary} ({ticket.status})")
        except Exception as e:
            print(f"✗ Ticket search failed: {e}")
        
        print("\n🎉 MCP Client Integration Test Complete!")
        print("=" * 50)
        
        # Clean up
        db.session.delete(mcp_config)
        db.session.delete(test_user)
        db.session.commit()
        
        return True


if __name__ == '__main__':
    test_mcp_client_integration()