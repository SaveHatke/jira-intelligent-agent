#!/usr/bin/env python3
"""
Test script to verify admin functionality is working correctly.
"""

import sys
from app import create_app, db
from app.models import User, Role


def test_admin_functionality():
    """Test the admin functionality."""
    print("Testing Admin Functionality")
    print("=" * 40)
    
    app = create_app()
    
    with app.app_context():
        try:
            # Test 1: Check if admin user exists
            print("1. Checking for admin users...")
            admin_users = User.query.join(User.roles).filter(Role.name == Role.TECH_MANAGER).all()
            if admin_users:
                print(f"   ✓ Found {len(admin_users)} admin user(s):")
                for admin in admin_users:
                    print(f"     - {admin.username} ({admin.email})")
            else:
                print("   ❌ No admin users found")
                return False
            
            # Test 2: Check if all roles exist
            print("\n2. Checking roles...")
            roles = Role.query.all()
            expected_roles = [Role.SCRUM_MASTER, Role.PRODUCT_OWNER, Role.BUSINESS_ANALYST, 
                            Role.TECH_MANAGER, Role.STAKEHOLDER]
            
            role_names = [role.name for role in roles]
            missing_roles = [role for role in expected_roles if role not in role_names]
            
            if not missing_roles:
                print(f"   ✓ All {len(expected_roles)} roles exist:")
                for role in roles:
                    user_count = len(role.users)
                    print(f"     - {role.name}: {user_count} user(s)")
            else:
                print(f"   ❌ Missing roles: {missing_roles}")
                return False
            
            # Test 3: Check admin user permissions
            print("\n3. Testing admin user permissions...")
            admin_user = admin_users[0]
            
            if admin_user.is_admin():
                print(f"   ✓ {admin_user.username} has admin privileges")
            else:
                print(f"   ❌ {admin_user.username} does not have admin privileges")
                return False
            
            if admin_user.has_role(Role.TECH_MANAGER):
                print(f"   ✓ {admin_user.username} has tech_manager role")
            else:
                print(f"   ❌ {admin_user.username} does not have tech_manager role")
                return False
            
            # Test 4: Test user creation functionality
            print("\n4. Testing user creation...")
            test_user = User(
                username='test_user_temp',
                email='test@example.com',
                is_active=True
            )
            test_user.set_password('testpass123')
            
            # Add a role
            stakeholder_role = Role.query.filter_by(name=Role.STAKEHOLDER).first()
            if stakeholder_role:
                test_user.roles.append(stakeholder_role)
            
            try:
                db.session.add(test_user)
                db.session.commit()
                print("   ✓ Test user created successfully")
                
                # Clean up
                db.session.delete(test_user)
                db.session.commit()
                print("   ✓ Test user cleaned up")
            except Exception as e:
                db.session.rollback()
                print(f"   ❌ Error creating test user: {str(e)}")
                return False
            
            # Test 5: Check database integrity
            print("\n5. Checking database integrity...")
            total_users = User.query.count()
            total_roles = Role.query.count()
            
            print(f"   ✓ Database contains {total_users} users and {total_roles} roles")
            
            print("\n" + "=" * 40)
            print("✅ All admin functionality tests passed!")
            print("✅ Task 4 implementation is working correctly!")
            return True
            
        except Exception as e:
            print(f"\n❌ Error during testing: {str(e)}")
            return False


if __name__ == '__main__':
    success = test_admin_functionality()
    sys.exit(0 if success else 1)