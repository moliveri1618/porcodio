from fastapi.testclient import TestClient
from api.main import app
from api.dependecies import verify_cognito_token

client = TestClient(app)
app.dependency_overrides[verify_cognito_token] = lambda: {"sub": "test-user", "username": "testuser"}

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello"}