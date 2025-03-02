from fastapi.testclient import TestClient
from unittest.mock import patch
from api.main import app  # Import the actual FastAPI app
from api.dependecies import verify_cognito_token  # Ensure correct import

client = TestClient(app)  # Use the real app

# ✅ Overriding the dependency
app.dependency_overrides[verify_cognito_token] = lambda: {"username": "testuser"}

def test_root():
    headers = {"Authorization": "Bearer faketoken123"}  # Mock token
    response = client.get("/", headers=headers)  # Make request

    assert response.status_code == 200
    assert response.json() == {"message": "Hello"}  # Must match actual API
