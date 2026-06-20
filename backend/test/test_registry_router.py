from copy import deepcopy
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.database.model import ServiceRecord
from app.dto import ServiceResponse
from app.router import registry_router


def test_health_returns_stable_instance_id(client: TestClient) -> None:
    first_response = client.get("/health")
    second_response = client.get("/health")

    assert first_response.status_code == 200
    assert first_response.json()["status"] == "ok"
    assert first_response.json()["instance_id"]
    assert first_response.json()["instance_id"] == second_response.json()["instance_id"]


def test_register_service(
    client: TestClient, registration: dict[str, Any]
) -> None:
    response = client.post("/register", json=registration)

    assert response.status_code == 201
    assert response.json() == {
        "id": 1,
        **registration,
        "status": {
            "health": {
                "state": "unknown",
                "checkedAt": None,
                "lastHealthyAt": None,
                "consecutiveFailures": 0,
                "error": None,
            }
        },
    }


def test_register_duplicate_service_returns_conflict(
    client: TestClient, registration: dict[str, Any]
) -> None:
    assert client.post("/register", json=registration).status_code == 201

    response = client.post("/register", json=registration)

    assert response.status_code == 409
    assert response.json() == {
        "code": "REG-1001",
        "detail": "Service already registered: robotics/mission-management"
    }


def test_register_same_service_name_in_different_namespace(
    client: TestClient, registration: dict[str, Any]
) -> None:
    assert client.post("/register", json=registration).status_code == 201
    other_registration = deepcopy(registration)
    other_registration["metadata"]["namespace"] = "logistics"

    response = client.post("/register", json=other_registration)

    assert response.status_code == 201
    assert response.json()["metadata"] == {
        "namespace": "logistics",
        "name": "mission-management",
        "version": "1.0.0",
    }


def test_register_invalid_service_returns_unprocessable_content(
    client: TestClient,
) -> None:
    response = client.post(
        "/register",
        json={"metadata": {"namespace": "robotics", "name": "invalid"}},
    )

    assert response.status_code == 422


def test_register_rejects_non_http_health_url(
    client: TestClient, registration: dict[str, Any]
) -> None:
    invalid_registration = deepcopy(registration)
    invalid_registration["spec"]["backend"]["healthUrl"] = "ftp://backend/health"

    response = client.post("/register", json=invalid_registration)

    assert response.status_code == 422


def test_unpersisted_service_record_returns_internal_server_error(
    client: TestClient,
    registration: dict[str, Any],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original_mapper = registry_router._to_service_response

    def map_unpersisted_record(service: ServiceRecord) -> ServiceResponse:
        service.id = None
        return original_mapper(service)

    monkeypatch.setattr(
        registry_router,
        "_to_service_response",
        map_unpersisted_record,
    )

    response = client.post("/register", json=registration)

    assert response.status_code == 500
    assert response.json() == {
        "code": "REG-9001",
        "detail": "Service record must be persisted before serialization"
    }


def test_list_and_get_services(
    client: TestClient, registration: dict[str, Any]
) -> None:
    created = client.post("/register", json=registration).json()

    list_response = client.get("/services")
    get_response = client.get("/services/robotics/mission-management")

    assert list_response.status_code == 200
    assert list_response.json() == [created]
    assert get_response.status_code == 200
    assert get_response.json() == created


def test_update_service(
    client: TestClient, registration: dict[str, Any]
) -> None:
    client.post("/register", json=registration)

    response = client.post(
        "/services/robotics/mission-management/update",
        json={
            "metadata": {"version": "1.1.0"},
            "spec": {
                "display": {"name": "Updated Mission Management", "order": 20}
            },
        },
    )

    assert response.status_code == 200
    assert response.json()["metadata"]["name"] == "mission-management"
    assert response.json()["metadata"]["version"] == "1.1.0"
    assert response.json()["spec"]["display"]["name"] == "Updated Mission Management"
    assert response.json()["spec"]["display"]["order"] == 20


def test_delete_service(
    client: TestClient, registration: dict[str, Any]
) -> None:
    client.post("/register", json=registration)

    delete_response = client.post("/services/robotics/mission-management/delete")
    get_response = client.get("/services/robotics/mission-management")

    assert delete_response.status_code == 204
    assert delete_response.content == b""
    assert get_response.status_code == 404


@pytest.mark.parametrize(
    ("method", "path", "json"),
    [
        ("get", "/services/robotics/missing", None),
        (
            "post",
            "/services/robotics/missing/update",
            {"spec": {"display": {"name": "Missing"}}},
        ),
        ("post", "/services/robotics/missing/delete", None),
    ],
)
def test_missing_service_returns_not_found(
    client: TestClient, method: str, path: str, json: dict[str, Any] | None
) -> None:
    response = client.request(method, path, json=json)

    assert response.status_code == 404
    assert response.json() == {
        "code": "REG-2001",
        "detail": "Service not found: robotics/missing",
    }
