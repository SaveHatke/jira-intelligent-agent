#!/usr/bin/env python3
"""
Test script to verify database model relationships.

This script tests the relationships between models to ensure
foreign keys and associations work correctly.
"""

import os
import sys

# Add the app directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import (
    User, Role, MCPConfiguration, AIConfiguration, 
    ValidationCriteria, AdminPrompt
)


def test_relationships():
    """Test all model relationships."""
    app = create_app()
    
    with app.app_context():
        print("🔗 Testing database model relationships...")
        
        # Create test user
        test_user = User(
            username="relationtest",
            email="relation@example.com"
        )
        test_user.set_password("testpass")
        db.session.add(test_user)
        db.session.commit()
        
        print(f"   Created test user: {test_user.username} (ID: {test_user.id})")
        
        # Test User-Role relationship (many-to-many)
        print("\n1. Testing User-Role relationship...")
        product_owner_role = Role.query.filter_by(name=Role.PRODUCT_OWNER).first()
        scrum_master_role = Role.query.filter_by(name=Role.SCRUM_MASTER).first()
        
        # Add roles to user
        test_user.roles.append(product_owner_role)
        test_user.roles.append(scrum_master_role)
        db.session.commit()
        
        # Test forward relationship
        assert len(test_user.roles) == 2, "User should have 2 roles"
        role_names = [role.name for role in test_user.roles]
        assert Role.PRODUCT_OWNER in role_names, "User missing product_owner role"
        assert Role.SCRUM_MASTER in role_names, "User missing scrum_master role"
        print("   ✅ User -> Roles relationship works")
        
        # Test reverse relationship
        assert test_user in product_owner_role.users, "Role missing user in reverse relationship"
        print("   ✅ Role -> Users relationship works")
        
        # Test User-MCPConfiguration relationship (one-to-many)
        print("\n2. Testing User-MCPConfiguration relationship...")
        mcp_config = MCPConfiguration(
            user_id=test_user.id,
            server_url="https://test-jira.example.com"
        )
        mcp_config.set_personal_access_token("test_token")
        db.session.add(mcp_config)
        db.session.commit()
        
        # Test forward relationship
        assert len(test_user.mcp_configurations) == 1, "User should have 1 MCP config"
        assert test_user.mcp_configurations[0].server_url == "https://test-jira.example.com"
        print("   ✅ User -> MCPConfigurations relationship works")
        
        # Test reverse relationship
        assert mcp_config.user == test_user, "MCP config missing user in reverse relationship"
        print("   ✅ MCPConfiguration -> User relationship works")
        
        # Test User-AIConfiguration relationship (one-to-many)
        print("\n3. Testing User-AIConfiguration relationship...")
        ai_config = AIConfiguration(
            user_id=test_user.id,
            user_id_from_jira="test_jira_user"
        )
        db.session.add(ai_config)
        db.session.commit()
        
        # Test forward relationship
        assert len(test_user.ai_configurations) == 1, "User should have 1 AI config"
        assert test_user.ai_configurations[0].user_id_from_jira == "test_jira_user"
        print("   ✅ User -> AIConfigurations relationship works")
        
        # Test reverse relationship
        assert ai_config.user == test_user, "AI config missing user in reverse relationship"
        print("   ✅ AIConfiguration -> User relationship works")
        
        # Test User-ValidationCriteria relationship (one-to-many)
        print("\n4. Testing User-ValidationCriteria relationship...")
        criteria = ValidationCriteria(
            user_id=test_user.id,
            criteria_type=ValidationCriteria.DEFINITION_OF_READY,
            criteria_text="Test criteria 1\nTest criteria 2"
        )
        db.session.add(criteria)
        db.session.commit()
        
        # Test forward relationship
        assert len(test_user.validation_criteria) == 1, "User should have 1 validation criteria"
        assert test_user.validation_criteria[0].criteria_type == ValidationCriteria.DEFINITION_OF_READY
        print("   ✅ User -> ValidationCriteria relationship works")
        
        # Test reverse relationship
        assert criteria.user == test_user, "Criteria missing user in reverse relationship"
        print("   ✅ ValidationCriteria -> User relationship works")
        
        # Test cascade delete
        print("\n5. Testing cascade delete...")
        user_id = test_user.id
        
        # Count related records before delete
        mcp_count_before = MCPConfiguration.query.filter_by(user_id=user_id).count()
        ai_count_before = AIConfiguration.query.filter_by(user_id=user_id).count()
        criteria_count_before = ValidationCriteria.query.filter_by(user_id=user_id).count()
        
        assert mcp_count_before == 1, "Should have 1 MCP config before delete"
        assert ai_count_before == 1, "Should have 1 AI config before delete"
        assert criteria_count_before == 1, "Should have 1 criteria before delete"
        
        # Delete user
        db.session.delete(test_user)
        db.session.commit()
        
        # Count related records after delete
        mcp_count_after = MCPConfiguration.query.filter_by(user_id=user_id).count()
        ai_count_after = AIConfiguration.query.filter_by(user_id=user_id).count()
        criteria_count_after = ValidationCriteria.query.filter_by(user_id=user_id).count()
        
        assert mcp_count_after == 0, "MCP configs should be deleted with user"
        assert ai_count_after == 0, "AI configs should be deleted with user"
        assert criteria_count_after == 0, "Criteria should be deleted with user"
        print("   ✅ Cascade delete works correctly")
        
        # Test that roles are not deleted (many-to-many relationship)
        product_owner_still_exists = Role.query.filter_by(name=Role.PRODUCT_OWNER).first()
        assert product_owner_still_exists is not None, "Roles should not be deleted with user"
        print("   ✅ Roles preserved after user deletion (correct many-to-many behavior)")
        
        print("\n🎉 All relationship tests passed successfully!")


if __name__ == '__main__':
    test_relationships()