import pytest
from main import create_app
from models import db, User


@pytest.fixture
def app():
    """Create and configure a test application instance."""
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Create a test client for the app."""
    return app.test_client()


@pytest.fixture
def auth_headers(client):
    """Create authenticated user and return auth headers."""
    # Register a test user
    user_data = {
        'email': 'test@example.com',
        'password': 'TestPassword123',
        'first_name': 'Test',
        'last_name': 'User'
    }
    response = client.post('/api/auth/register', json=user_data)
    assert response.status_code == 201

    data = response.get_json()
    token = data['access_token']

    return {'Authorization': f'Bearer {token}'}


def test_health_check(client):
    """Test the health check endpoint."""
    response = client.get('/health')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'healthy'


def test_root_endpoint(client):
    """Test the root endpoint."""
    response = client.get('/')
    assert response.status_code == 200
    data = response.get_json()
    assert 'message' in data
    assert 'endpoints' in data


def test_user_registration(client):
    """Test user registration."""
    user_data = {
        'email': 'newuser@example.com',
        'password': 'SecurePassword123',
        'first_name': 'New',
        'last_name': 'User'
    }
    response = client.post('/api/auth/register', json=user_data)
    assert response.status_code == 201
    data = response.get_json()
    assert 'access_token' in data
    assert data['user']['email'] == user_data['email']


def test_user_login(client):
    """Test user login."""
    # First register a user
    user_data = {
        'email': 'login@example.com',
        'password': 'LoginPassword123',
        'first_name': 'Login',
        'last_name': 'Test'
    }
    client.post('/api/auth/register', json=user_data)

    # Now try to login
    login_data = {
        'email': 'login@example.com',
        'password': 'LoginPassword123'
    }
    response = client.post('/api/auth/login', json=login_data)
    assert response.status_code == 200
    data = response.get_json()
    assert 'access_token' in data


def test_create_mood_entry(client, auth_headers):
    """Test creating a mood entry."""
    mood_data = {
        'mood_score': 7,
        'emotions': ['happy', 'calm'],
        'notes': 'Feeling good today',
        'activities': ['exercise', 'meditation'],
        'triggers': []
    }
    response = client.post('/api/mood/entries', json=mood_data, headers=auth_headers)
    assert response.status_code == 201
    data = response.get_json()
    assert data['entry']['mood_score'] == 7


def test_get_mood_entries(client, auth_headers):
    """Test retrieving mood entries."""
    # Create a mood entry first
    mood_data = {
        'mood_score': 8,
        'emotions': ['content'],
        'notes': 'Test entry'
    }
    client.post('/api/mood/entries', json=mood_data, headers=auth_headers)

    # Now retrieve entries
    response = client.get('/api/mood/entries', headers=auth_headers)
    assert response.status_code == 200
    data = response.get_json()
    assert data['count'] > 0


def test_schedule_therapy_session(client, auth_headers):
    """Test scheduling a therapy session."""
    session_data = {
        'session_type': 'virtual',
        'scheduled_at': '2026-04-01T14:00:00Z',
        'duration_minutes': 60,
        'notes': 'First session'
    }
    response = client.post('/api/therapy/sessions', json=session_data, headers=auth_headers)
    assert response.status_code == 201
    data = response.get_json()
    assert data['session']['session_type'] == 'virtual'


def test_ai_mood_analysis(client, auth_headers):
    """Test AI mood analysis."""
    # Create some mood entries first
    for score in [6, 7, 8, 7, 6]:
        mood_data = {'mood_score': score, 'emotions': ['neutral']}
        client.post('/api/mood/entries', json=mood_data, headers=auth_headers)

    # Get mood analysis
    response = client.get('/api/ai/analyze-mood', headers=auth_headers)
    assert response.status_code == 200
    data = response.get_json()
    assert 'analysis' in data
    assert data['analysis']['average_mood'] is not None


def test_ai_recommendations(client, auth_headers):
    """Test AI recommendations."""
    # Create a mood entry
    mood_data = {'mood_score': 5, 'emotions': ['anxious']}
    client.post('/api/mood/entries', json=mood_data, headers=auth_headers)

    # Get recommendations
    response = client.get('/api/ai/recommendations', headers=auth_headers)
    assert response.status_code == 200
    data = response.get_json()
    assert 'recommendations' in data
    assert len(data['recommendations']) > 0


def test_create_self_care_plan(client, auth_headers):
    """Test creating a self-care plan."""
    # Create some mood entries first
    for score in [6, 7, 5]:
        mood_data = {'mood_score': score, 'emotions': ['neutral']}
        client.post('/api/mood/entries', json=mood_data, headers=auth_headers)

    # Create self-care plan
    response = client.post('/api/ai/self-care-plan', headers=auth_headers)
    assert response.status_code == 201
    data = response.get_json()
    assert 'plan' in data
    assert len(data['plan']['recommendations']) > 0
