"""Basic tests for JIA application structure."""

def test_app_creation(app):
    """Test that the app is created successfully."""
    assert app is not None
    assert app.config['TESTING'] is True

def test_index_route_exists(client):
    """Test that the index route exists."""
    response = client.get('/')
    assert response.status_code == 200
    assert b'Welcome to JIA' in response.data

def test_login_route_exists(client):
    """Test that the login route exists."""
    response = client.get('/auth/login')
    assert response.status_code == 200
    assert b'Sign In to JIA' in response.data

def test_app_has_blueprints(app):
    """Test that blueprints are registered."""
    blueprint_names = [bp.name for bp in app.blueprints.values()]
    assert 'main' in blueprint_names
    assert 'auth' in blueprint_names