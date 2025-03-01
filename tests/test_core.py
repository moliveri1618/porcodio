from fastapi.testclient import TestClient
from api.main import app
from api.dependecies import verify_cognito_token

# Create a mock function that returns user data
def mock_verify_cognito_token():
    return {"sub": "test-user", "username": "testuser"}

# Setup function to run before tests
def setup_function():
    # Clear any existing overrides and set new ones
    app.dependency_overrides.clear()
    app.dependency_overrides[verify_cognito_token] = mock_verify_cognito_token

# Teardown function to run after tests
def teardown_function():
    # Clear overrides after tests
    app.dependency_overrides.clear()

def test_root():
    # Setup overrides before each test
    setup_function()
    
    # Create client after overrides are set
    client = TestClient(app)
    
    # Make the request
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello"}
    
    # Clean up
    teardown_function()