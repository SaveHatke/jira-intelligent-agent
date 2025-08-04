#!/usr/bin/env python3
"""
Initial admin user creation script for JIA application.

This script creates the first admin user and initializes the role system.
Run this script after setting up the database to create your first admin user.
"""

import os
import sys
import getpass
from app import create_app, db
from app.models import User, Role


def create_roles():
    """Create default roles if they don't exist."""
    roles_data = [
        {
            'name': Role.SCRUM_MASTER,
            'description': 'Can manage sprint capacity, view sprint health dashboard, predict spillovers, and perform quality analysis.'
        },
        {
            'name': Role.PRODUCT_OWNER,
            'description': 'Can create tickets, validate against DoR/DoD, break down epics, and generate release notes.'
        },
        {
            'name': Role.BUSINESS_ANALYST,
            'description': 'Can create tickets, validate requirements, and break down epics. Specializes in requirements analysis.'
        },
        {
            'name': Role.TECH_MANAGER,
            'description': 'Has administrative privileges including user management. Can access all features including SLA monitoring.'
        },
        {
            'name': Role.STAKEHOLDER,
            'description': 'Can validate tickets, monitor SLAs, and access reporting features. Provides oversight capabilities.'
        }
    ]
    
    created_roles = []
    for role_data in roles_data:
        existing_role = Role.query.filter_by(name=role_data['name']).first()
        if not existing_role:
            role = Role(name=role_data['name'], description=role_data['description'])
            db.session.add(role)
            created_roles.append(role_data['name'])
            print(f"✓ Created role: {role_data['name']}")
        else:
            print(f"- Role already exists: {role_data['name']}")
    
    if created_roles:
        db.session.commit()
        print(f"\n✓ Successfully created {len(created_roles)} new roles")
    else:
        print("\n- All roles already exist")
    
    return Role.query.all()


def create_admin_user():
    """Create the initial admin user."""
    print("\n" + "="*50)
    print("JIA Admin User Creation")
    print("="*50)
    
    # Check if any admin users already exist
    existing_admin = User.query.join(User.roles).filter(Role.name == Role.TECH_MANAGER).first()
    if existing_admin:
        print(f"\n⚠️  Admin user already exists: {existing_admin.username}")
        response = input("Do you want to create another admin user? (y/N): ").strip().lower()
        if response not in ['y', 'yes']:
            print("Exiting...")
            return None
    
    print("\nPlease provide details for the new admin user:")
    
    # Get username
    while True:
        username = input("Username: ").strip()
        if not username:
            print("❌ Username cannot be empty")
            continue
        if len(username) < 3:
            print("❌ Username must be at least 3 characters long")
            continue
        
        # Check if username already exists
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            print(f"❌ Username '{username}' already exists")
            continue
        
        break
    
    # Get email
    while True:
        email = input("Email: ").strip()
        if not email:
            print("❌ Email cannot be empty")
            continue
        if '@' not in email:
            print("❌ Please enter a valid email address")
            continue
        
        # Check if email already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            print(f"❌ Email '{email}' already exists")
            continue
        
        break
    
    # Get password
    while True:
        password = getpass.getpass("Password: ")
        if not password:
            print("❌ Password cannot be empty")
            continue
        if len(password) < 6:
            print("❌ Password must be at least 6 characters long")
            continue
        
        confirm_password = getpass.getpass("Confirm password: ")
        if password != confirm_password:
            print("❌ Passwords do not match")
            continue
        
        break
    
    # Create the admin user
    try:
        admin_user = User(
            username=username,
            email=email,
            is_active=True
        )
        admin_user.set_password(password)
        
        # Assign tech_manager role (admin role)
        tech_manager_role = Role.query.filter_by(name=Role.TECH_MANAGER).first()
        if tech_manager_role:
            admin_user.roles.append(tech_manager_role)
        else:
            print("❌ Tech Manager role not found. Please run database migrations first.")
            return None
        
        db.session.add(admin_user)
        db.session.commit()
        
        print(f"\n✅ Successfully created admin user: {username}")
        print(f"   Email: {email}")
        print(f"   Role: Tech Manager (Administrator)")
        print(f"\nYou can now log in to JIA with these credentials.")
        
        return admin_user
        
    except Exception as e:
        db.session.rollback()
        print(f"\n❌ Error creating admin user: {str(e)}")
        return None


def main():
    """Main function to set up initial admin user."""
    print("JIA Initial Setup - Admin User Creation")
    print("="*50)
    
    # Create Flask app
    app = create_app()
    
    with app.app_context():
        try:
            # Test database connection
            with db.engine.connect() as conn:
                conn.execute(db.text('SELECT 1'))
            print("✓ Database connection successful")
        except Exception as e:
            print(f"❌ Database connection failed: {str(e)}")
            print("\nPlease ensure:")
            print("1. Database is running")
            print("2. Database migrations have been run (flask db upgrade)")
            print("3. Environment variables are set correctly")
            sys.exit(1)
        
        # Create roles first
        print("\n1. Setting up roles...")
        roles = create_roles()
        
        # Create admin user
        print("\n2. Creating admin user...")
        admin_user = create_admin_user()
        
        if admin_user:
            print("\n" + "="*50)
            print("✅ JIA setup completed successfully!")
            print("="*50)
            print("\nNext steps:")
            print("1. Start the Flask application: python jia.py")
            print("2. Navigate to http://localhost:5000")
            print("3. Log in with your admin credentials")
            print("4. Create additional users through the admin interface")
        else:
            print("\n❌ Setup failed. Please check the errors above and try again.")
            sys.exit(1)


if __name__ == '__main__':
    main()