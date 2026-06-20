import pytest
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


def test_list_and_get_services(
    client: TestClient, registration: dict[str, object]
) -> None:
    created = client.post("/register", json=registration).json()

    list_response = client.get("/services")
    get_response = client.get("/services/mission-management")

    assert list_response.status_code == 200
    assert list_response.json() == [created]
    assert get_response.status_code == 200
    assert get_response.json() == created


def test_update_service(
    client: TestClient, registration: dict[str, object]
) -> None:
    client.post("/register", json=registration)

    response = client.post(
        "/services/mission-management/update",
        json={"name": "Updated Mission Management", "order": 20},
    )

    assert response.status_code == 200
    assert response.json()["service"] == "mission-management"
    assert response.json()["name"] == "Updated Mission Management"
    assert response.json()["order"] == 20


def test_delete_service(
    client: TestClient, registration: dict[str, object]
) -> None:
    client.post("/register", json=registration)

    delete_response = client.post("/services/mission-management/delete")
    get_response = client.get("/services/mission-management")

    assert delete_response.status_code == 204
    assert delete_response.content == b""
    assert get_response.status_code == 404


@pytest.mark.parametrize(
    ("method", "path", "json"),
    [
        ("get", "/services/missing", None),
        ("post", "/services/missing/update", {"name": "Missing"}),
        ("post", "/services/missing/delete", None),
    ],
)
def test_missing_service_returns_not_found(
    client: TestClient, method: str, path: str, json: dict[str, str] | None
) -> None:
    response = client.request(method, path, json=json)

    assert response.status_code == 404
    assert response.json() == {"detail": "Service not found: missing"}
