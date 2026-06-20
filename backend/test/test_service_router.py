import pytest
from fastapi.testclient import TestClient


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
