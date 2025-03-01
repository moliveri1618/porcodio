from fastapi.testclient import TestClient
from api.main import app
from api.dependecies import verify_cognito_token

# Create a mock function that returns user data
def mock_verify_cognito_token():
    return {"sub": "test-user", "username": "testuser"}

# Override the dependency before creating the TestClient
app.dependency_overrides[verify_cognito_token] = mock_verify_cognito_token

# Create the test client after overriding dependencies
client = TestClient(app)

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello"}

# Don't forget to clean up after your tests
def teardown_module(module):
    app.dependency_overrides = {}