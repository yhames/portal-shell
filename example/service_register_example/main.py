import logging
import os
import random
import time

import requests
import yaml


DEFAULT_REGISTRATION_PATH = "portal-registry.yml"
DEFAULT_REGISTRY_URL = "http://localhost:8000"
DEFAULT_INTERVAL_SECONDS = 10
DEFAULT_REQUEST_TIMEOUT_SECONDS = 5
JITTER_RATIO = 0.2

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("service_register")


def load_registration(path):
    with open(path, "r", encoding="utf-8") as registration_file:
        return yaml.safe_load(registration_file)


def registry_is_alive(registry_url, timeout):
    try:
        response = requests.get(f"{registry_url}/health", timeout=timeout)
        response.raise_for_status()
        return response.json()["instance_id"]
    except (requests.RequestException, KeyError, ValueError):
        return None


def register_service(registry_url, registration, timeout):
    response = requests.post(
        f"{registry_url}/register",
        json=registration,
        timeout=timeout,
    )
    response.raise_for_status()


def sleep_with_jitter(interval):
    time.sleep(interval * random.uniform(1 - JITTER_RATIO, 1 + JITTER_RATIO))


def main():
    registration_path = os.getenv("SPEC_PATH", DEFAULT_REGISTRATION_PATH)
    registry_url = os.getenv("REGISTRY_URL", DEFAULT_REGISTRY_URL).rstrip("/")
    interval_seconds = int(os.getenv("INTERVAL_SECONDS", DEFAULT_INTERVAL_SECONDS))
    request_timeout = int(
        os.getenv("REQUEST_TIMEOUT_SECONDS", DEFAULT_REQUEST_TIMEOUT_SECONDS)
    )

    registration = load_registration(registration_path)
    service_id = registration["id"]
    last_registry_instance_id = None

    while True:
        registry_instance_id = registry_is_alive(registry_url, request_timeout)

        # 1. service registry is not reachable
        if registry_instance_id is None:
            logger.error(f"Registry is not reachable: {registry_url}")
            sleep_with_jitter(interval_seconds)
            continue

        # 2. service registry is alive but no change in instance_id
        if registry_instance_id == last_registry_instance_id:
            sleep_with_jitter(interval_seconds)
            continue

        # 3. service registry is alive and service needs to be registered
        try:
            register_service(registry_url, registration, request_timeout)
            last_registry_instance_id = registry_instance_id
            logger.info(f"Registered service: {service_id}")
        except requests.RequestException as exc:
            logger.error(f"Failed to register service: {exc}")

        sleep_with_jitter(interval_seconds)


if __name__ == "__main__":
    main()
