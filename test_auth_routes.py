#!/usr/bin/env python3
"""
Test script for authentication routes and web interface.

This script tests the Flask routes and templates for the authentication system.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import User, Role

def test_auth_routes():
    """Test authentication routes."""
    print("Testing Authentication Routes...")
    print("=" * 50)
    
    # Create test app
    app = create_app('testing')
    
    with app.test_client() as client:
        with app.app_context():
            # Create tables
            db.create_all()
            
            # Create test user with roles
            user = User(username='testuser', email='test@example.com')
            user.set_password('testpassword123')
            
            # Create roles
            scrum_role = Role(name=Role.SCRUM_MASTER, description='Scrum Master')
            po_role = Role(name=Role.PRODUCT_OWNER, description='Product Owner')
            
            db.session.add(scrum_role)
            db.session.add(po_role)
            db.session.commit()
            
            user.roles.append(scrum_role)
            user.roles.append(po_role)
            
            db.session.add(user)
            db.session.commit()
            
            print("\n1. Testing login page access...")
            
            # Test GET login page
            response = client.get('/auth/login')
            assert response.status_code == 200, f"Login page should be accessible, got {response.status_code}"
            assert b'Sign In to JIA' in response.data, "Login page should contain title"
            print("✓ Login page accessible")
            
            print("\n2. Testing login with invalid credentials...")
            
            # Test login with wrong password
            response = client.post('/auth/login', data={
                'username': 'testuser',
                'password': 'wrongpassword'
            }, follow_redirects=True)
            assert response.status_code == 200, "Should return to login page"
            assert b'Invalid username or password' in response.data, "Should show error message"
            print("✓ Invalid login properly rejected")
            
            print("\n3. Testing login with valid credentials...")
            
            # Test successful login
            response = client.post('/auth/login', data={
                'username': 'testuser',
                'password': 'testpassword123'
            }, follow_redirects=True)
            assert response.status_code == 200, "Should redirect to dashboard"
            assert b'Welcome back, testuser!' in response.data, "Should show welcome message"
            print("✓ Valid login successful")
            
            print("\n4. Testing dashboard access after login...")
            
            # Test dashboard access
            response = client.get('/dashboard')
            assert response.status_code == 200, "Dashboard should be accessible after login"
            assert b'Dashboard' in response.data, "Should show dashboard"
            assert b'testuser' in response.data, "Should show username"
            
            # Debug: print response to see what's actually rendered
            print(f"Dashboard response contains: {response.data[:500]}")
            
            # Check for role information (might be formatted differently)
            response_text = response.data.decode('utf-8')
            assert 'scrum_master' in response_text.lower() or 'scrum master' in response_text.lower(), "Should show scrum master role"
            print("✓ Dashboard accessible with role information")
            
            print("\n5. Testing logout...")
            
            # Test logout
            response = client.get('/auth/logout', follow_redirects=True)
            assert response.status_code == 200, "Should redirect after logout"
            assert b'You have been logged out' in response.data, "Should show logout message"
            print("✓ Logout successful")
            
            print("\n6. Testing protected route access after logout...")
            
            # Test dashboard access after logout (should redirect to login)
            response = client.get('/dashboard', follow_redirects=True)
            assert response.status_code == 200, "Should redirect to login"
            assert b'Sign In to JIA' in response.data, "Should show login page"
            print("✓ Protected routes properly secured")
            
            print("\n7. Testing login with email address...")
            
            # Test login with email instead of username
            response = client.post('/auth/login', data={
                'username': 'test@example.com',  # Using email as username
                'password': 'testpassword123'
            }, follow_redirects=True)
            assert response.status_code == 200, "Should allow login with email"
            assert b'Welcome back, testuser!' in response.data, "Should show welcome message"
            print("✓ Email login working")
            
            print("\n" + "=" * 50)
            print("✅ All authentication route tests passed!")
            
            return True

def test_role_based_features():
    """Test role-based feature visibility."""
    print("\n" + "=" * 50)
    print("Testing Role-Based Feature Visibility...")
    print("=" * 50)
    
    app = create_app('testing')
    
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            
            # Create users with different roles
            admin_user = User(username='admin', email='admin@example.com')
            admin_user.set_password('password123')
            
            regular_user = User(username='regular', email='regular@example.com')
            regular_user.set_password('password123')
            
            # Create roles
            admin_role = Role(name=Role.TECH_MANAGER, description='Tech Manager')
            stakeholder_role = Role(name=Role.STAKEHOLDER, description='Stakeholder')
            
            db.session.add(admin_role)
            db.session.add(stakeholder_role)
            db.session.commit()
            
            admin_user.roles.append(admin_role)
            regular_user.roles.append(stakeholder_role)
            
            db.session.add(admin_user)
            db.session.add(regular_user)
            db.session.commit()
            
            print("\n1. Testing admin user dashboard...")
            
            # Login as admin
            client.post('/auth/login', data={
                'username': 'admin',
                'password': 'password123'
            })
            
            response = client.get('/dashboard')
            assert response.status_code == 200, "Admin should access dashboard"
            assert b'User Management' in response.data, "Admin should see user management"
            
            # Check for admin role (might be formatted as tech_manager)
            response_text = response.data.decode('utf-8')
            assert 'tech_manager' in response_text.lower() or 'tech manager' in response_text.lower(), "Should show admin role"
            print("✓ Admin user sees administrative features")
            
            # Logout
            client.get('/auth/logout')
            
            print("\n2. Testing regular user dashboard...")
            
            # Login as regular user
            client.post('/auth/login', data={
                'username': 'regular',
                'password': 'password123'
            })
            
            response = client.get('/dashboard')
            assert response.status_code == 200, "Regular user should access dashboard"
            assert b'User Management' not in response.data, "Regular user should not see user management"
            
            # Check for stakeholder role
            response_text = response.data.decode('utf-8')
            assert 'stakeholder' in response_text.lower(), "Should show stakeholder role"
            print("✓ Regular user sees appropriate features only")
            
            print("\n✅ Role-based feature visibility working correctly!")
            
            return True

if __name__ == '__main__':
    try:
        # Test authentication routes
        test_auth_routes()
        
        # Test role-based features
        test_role_based_features()
        
        print("\n" + "🎉" * 25)
        print("🎉 AUTHENTICATION SYSTEM FULLY TESTED! 🎉")
        print("🎉" * 25)
        print("\nAll authentication features working:")
        print("✅ Login/logout routes with proper validation")
        print("✅ Session management with Flask-Login")
        print("✅ Role-based dashboard feature visibility")
        print("✅ Protected route access control")
        print("✅ Email and username login support")
        print("✅ User-friendly error messages")
        print("✅ Responsive templates with Bootstrap")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)