from fastapi.testclient import TestClient
from unittest.mock import patch
from api.main import app  

client = TestClient(app)  # Use the actual app

# Mock Cognito authentication
@patch("main.verify_cognito_token", return_value={"username": "testuser"})
def test_root(mock_auth):
    headers = {"Authorization": "Bearer faketoken123"}  # Mock token
    response = client.get("/", headers=headers)  # Make request

    assert response.status_code == 200
    assert response.json() == {"message": "Hello"}  # Must match actual API

    # Ensure authentication was called
    mock_auth.assert_called_once()
