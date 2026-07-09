import os
import pytest
from app import create_app
from app.extensions import db
from app.models.user import Role, User

@pytest.fixture
def app():
    """Create and configure a new app instance for each test."""
    app = create_app('testing')
    
    with app.app_context():
        db.create_all()
        # Seed basic roles
        admin_role = Role(name='Administrator', description='System Admin')
        user_role = Role(name='Standard User', description='Standard Contributor')
        db.session.add(admin_role)
        db.session.add(user_role)
        db.session.commit()
        
        yield app
        
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()

@pytest.fixture
def runner(app):
    """A test runner for the app's CLI commands."""
    return app.test_cli_runner()
