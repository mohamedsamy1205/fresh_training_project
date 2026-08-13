from fastapi.testclient import TestClient
from app.main import app



client = TestClient(app)

def test_get_user():
    response = client.get("/users/1")

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == 1
    assert data["name"] == "Mohamed"
    assert data["email"] == "test@example.com"