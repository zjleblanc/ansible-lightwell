"""Basic tests for the Lightwell demo Flask application."""

import pytest

from app import create_app


@pytest.fixture
def client():
    app = create_app()
    app.testing = True
    with app.test_client() as test_client:
        yield test_client


def test_dashboard_returns_200(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"Lightwell" in response.data


def test_healthz_returns_ok_status(client):
    response = client.get("/healthz")
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["status"] == "ok"
    assert "packages" in payload
    assert len(payload["packages"]) > 0


def test_api_config_returns_service_metadata(client):
    response = client.get("/api/config")
    assert response.status_code == 200
    payload = response.get_json()
    assert "service" in payload
    assert payload["service"]["name"] == "Lightwell Patch Pipeline Demo"
