import pytest
from app.extensions import db
from app.models.user import User

def test_index_page(client):
    """Test that home page loads successfully."""
    response = client.get('/')
    assert response.status_code == 200
    assert b"Browse the Chapters" in response.data

def test_about_page(client):
    """Test that about page loads successfully."""
    response = client.get('/about')
    assert response.status_code == 200
    assert b"About DivyaGita" in response.data
    assert b"Indrajit Ghosh" in response.data

def test_register_page_get(client):
    """Test register page renders correctly."""
    response = client.get('/auth/register')
    assert response.status_code == 200
    assert b"Become a Contributor" in response.data

def test_register_post_validation(client, app):
    """Test contributor registration adds user in database with inactive status."""
    response = client.post('/auth/register', data={
        'name': 'Test Contributor',
        'username': 'tester',
        'email': 'tester@example.com',
        'password': 'password123',
        'confirm_password': 'password123',
        'contact_number': '+91 9999999999',
        'address': 'IIT Kanpur, India',
        'privacy_agreement': 'y'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b"Account registered successfully" in response.data
    
    with app.app_context():
        user = User.query.filter_by(username='tester').first()
        assert user is not None
        assert user.name == 'Test Contributor'
        assert user.is_active is False
        assert user.is_email_verified is False
