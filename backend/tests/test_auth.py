"""Authentication API tests covering login flow and header guards."""
from __future__ import annotations

from fastapi.testclient import TestClient


def test_login_and_protected_route(client: TestClient, client_headers: dict[str, str]) -> None:
    response = client.post(
        '/api/client/auth/login',
        json={'email': 'jordan@rivercityclean.com', 'password': 'client-portal-demo'},
    )
    assert response.status_code == 200
    payload = response.json()
    assert 'token' in payload and payload['token']

    protected = client.get('/api/client/dashboard')
    assert protected.status_code == 401

    authorised = client.get('/api/client/dashboard', headers=client_headers | {'Authorization': f"Bearer {payload['token']}"})
    assert authorised.status_code == 200
    body = authorised.json()
    assert body['client_name'] == 'River City Clean Co.'
