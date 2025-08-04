#!/usr/bin/env python3
"""
Test script to verify database models functionality.

This script tests the core functionality of all database models
to ensure they work correctly.
"""

import os
import sys
from datetime import datetime

# Add the app directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import User, Role, MCPConfiguration, AIConfiguration, ValidationCriteria, AdminPrompt


def test_models():
    """Test all model functionality."""
    app = create_app()
    
    with app.app_context():
        print("🧪 Testing database models...")
        
        # Test User model
        print("\n1. Testing User model...")
        test_user = User(
            username="testuser",
            email="test@example.com"
        )
        test_user.set_password("testpassword")
        
        # Test password functionality
        assert test_user.check_password("testpassword"), "Password check failed"
        assert not test_user.check_password("wrongpassword"), "Wrong password accepted"
        print("   ✅ Password hashing and verification works")
        
        # Test validation
        errors = test_user.validate()
        assert len(errors) == 0, f"User validation failed: {errors}"
        print("   ✅ User validation works")
        
        # Test role assignment
        role = Role.query.filter_by(name=Role.PRODUCT_OWNER).first()
        test_user.roles.append(role)
        assert test_user.has_role(Role.PRODUCT_OWNER), "Role assignment failed"
        assert test_user.has_any_role([Role.PRODUCT_OWNER, Role.SCRUM_MASTER]), "has_any_role failed"
        print("   ✅ Role assignment and checking works")
        
        # Test to_dict
        user_dict = test_user.to_dict()
        assert 'username' in user_dict, "to_dict missing username"
        assert 'roles' in user_dict, "to_dict missing roles"
        print("   ✅ User to_dict works")
        
        # Test Role model
        print("\n2. Testing Role model...")
        test_role = Role(name=Role.SCRUM_MASTER, description="Test role")
        errors = test_role.validate()
        assert len(errors) == 0, f"Role validation failed: {errors}"
        print("   ✅ Role validation works")
        
        # Test invalid role
        invalid_role = Role(name="invalid_role")
        errors = invalid_role.validate()
        assert len(errors) > 0, "Invalid role should have validation errors"
        print("   ✅ Role validation catches invalid roles")
        
        # Test MCPConfiguration model
        print("\n3. Testing MCPConfiguration model...")
        mcp_config = MCPConfiguration(
            user_id=1,
            server_url="https://jira.example.com",
            additional_params={"param1": "value1"}
        )
        mcp_config.set_personal_access_token("test_token_123")
        
        # Test encryption/decryption
        decrypted_token = mcp_config.get_personal_access_token()
        assert decrypted_token == "test_token_123", "Token encryption/decryption failed"
        print("   ✅ MCP token encryption/decryption works")
        
        # Test additional params
        mcp_config.set_additional_param("test_key", "test_value")
        assert mcp_config.get_additional_param("test_key") == "test_value", "Additional params failed"
        print("   ✅ MCP additional parameters work")
        
        # Test validation
        errors = mcp_config.validate()
        assert len(errors) == 0, f"MCP validation failed: {errors}"
        print("   ✅ MCP validation works")
        
        # Test to_dict
        mcp_dict = mcp_config.to_dict()
        assert 'server_url' in mcp_dict, "MCP to_dict missing server_url"
        assert 'has_token' in mcp_dict, "MCP to_dict missing has_token"
        print("   ✅ MCP to_dict works")
        
        # Test AIConfiguration model
        print("\n4. Testing AIConfiguration model...")
        ai_config = AIConfiguration(
            user_id=1,
            user_id_from_jira="jira_user_123"
        )
        
        # Test custom headers
        headers = {"Authorization": "Bearer token", "Content-Type": "application/json"}
        ai_config.set_custom_headers(headers)
        retrieved_headers = ai_config.get_custom_headers()
        assert retrieved_headers == headers, "Custom headers failed"
        print("   ✅ AI custom headers work")
        
        # Test model configs
        ai_config.set_model_config("temperature", 0.7)
        assert ai_config.get_model_config("temperature") == 0.7, "Model config failed"
        print("   ✅ AI model configs work")
        
        # Test validation
        errors = ai_config.validate()
        assert len(errors) == 0, f"AI validation failed: {errors}"
        print("   ✅ AI validation works")
        
        # Test ValidationCriteria model
        print("\n5. Testing ValidationCriteria model...")
        criteria = ValidationCriteria(
            user_id=1,
            criteria_type=ValidationCriteria.DEFINITION_OF_READY,
            criteria_text="Requirement 1\nRequirement 2\nRequirement 3"
        )
        
        # Test criteria list
        criteria_list = criteria.get_criteria_list()
        assert len(criteria_list) == 3, "Criteria list parsing failed"
        assert "Requirement 1" in criteria_list, "Criteria list missing item"
        print("   ✅ Validation criteria parsing works")
        
        # Test validation
        errors = criteria.validate()
        assert len(errors) == 0, f"Criteria validation failed: {errors}"
        print("   ✅ Validation criteria validation works")
        
        # Test AdminPrompt model
        print("\n6. Testing AdminPrompt model...")
        prompt = AdminPrompt(
            feature_name="test_feature",
            prompt_template="Test prompt with {variable}",
            output_format="json"
        )
        
        # Test validation
        errors = prompt.validate()
        assert len(errors) == 0, f"Prompt validation failed: {errors}"
        print("   ✅ Admin prompt validation works")
        
        # Test to_dict
        prompt_dict = prompt.to_dict()
        assert 'feature_name' in prompt_dict, "Prompt to_dict missing feature_name"
        print("   ✅ Admin prompt to_dict works")
        
        print("\n🎉 All model tests passed successfully!")
        
        # Show final database stats
        from app.database import get_database_stats
        stats = get_database_stats()
        print(f"\n📊 Final database stats: {stats}")


if __name__ == '__main__':
    test_models()