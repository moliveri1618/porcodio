from fastapi import FastAPI, Depends
from fastapi.testclient import TestClient

# Create a test-specific app
test_app = FastAPI()

# Define a simple endpoint for testing
@test_app.get("/")
async def test_root():
    return {"message": "Hellosdfsdfdd"}

# Create the test client
client = TestClient(test_app)

# def test_root():
#     response = client.get("/")
#     assert response.status_code == 200
#     assert response.json() == {"message": "Hello"}