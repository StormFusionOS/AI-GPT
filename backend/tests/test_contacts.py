"""End-to-end CRUD tests for the contacts API."""
from __future__ import annotations

from fastapi.testclient import TestClient


def test_contacts_crud_flow(client: TestClient) -> None:
    payload = {
        'name': 'Jamie Rivers',
        'email': 'jamie@example.com',
        'phone': '+1-555-1111',
        'company': 'Rivers Co.',
        'notes': 'Prefers SMS updates.',
    }

    create_resp = client.post('/api/contacts/', json=payload)
    assert create_resp.status_code == 201
    created = create_resp.json()
    contact_id = created['id']
    assert created['name'] == payload['name']

    detail_resp = client.get(f'/api/contacts/{contact_id}')
    assert detail_resp.status_code == 200
    assert detail_resp.json()['email'] == payload['email']

    update_resp = client.put(f'/api/contacts/{contact_id}', json={'notes': 'Switch to email'})
    assert update_resp.status_code == 200
    assert update_resp.json()['notes'] == 'Switch to email'

    list_resp = client.get('/api/contacts/')
    assert list_resp.status_code == 200
    ids = [item['id'] for item in list_resp.json()]
    assert contact_id in ids

    delete_resp = client.delete(f'/api/contacts/{contact_id}')
    assert delete_resp.status_code == 204

    missing_resp = client.get(f'/api/contacts/{contact_id}')
    assert missing_resp.status_code == 404
