from fastapi.testclient import TestClient


def test_health_returns_stable_instance_id(client: TestClient) -> None:
    first_response = client.get("/health")
    second_response = client.get("/health")

    assert first_response.status_code == 200
    assert first_response.json()["status"] == "ok"
    assert first_response.json()["instance_id"]
    assert first_response.json()["instance_id"] == second_response.json()["instance_id"]


def test_register_service(
    client: TestClient, registration: dict[str, object]
) -> None:
    response = client.post("/register", json=registration)

    assert response.status_code == 201
    assert response.json() == {"id": 1, **registration}


def test_register_duplicate_service_returns_conflict(
    client: TestClient, registration: dict[str, object]
) -> None:
    assert client.post("/register", json=registration).status_code == 201

    response = client.post("/register", json=registration)

    assert response.status_code == 409
    assert response.json() == {
        "detail": "Service already registered: mission-management"
    }


def test_register_invalid_service_returns_unprocessable_content(
    client: TestClient,
) -> None:
    response = client.post("/register", json={"service": "mission-management"})

    assert response.status_code == 422
