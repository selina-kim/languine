"""
Integration tests for create-deck endpoint.

These tests rely on repo conftest fixtures (db_schema/db_setup/app/client/auth_headers).
See src/tests/conftest.py. :contentReference[oaicite:1]{index=1}
"""

import json
from uuid import uuid4
import pytest

pytestmark = pytest.mark.integration


def test_create_deck_success_201(client, auth_headers):
    deck_name = f"Integration Deck {uuid4()}"
    payload = {
        "deck_name": deck_name,
        "word_lang": "French",
        "trans_lang": "English",
        "description": "integration test",
        "is_public": False,
        "link": None,
    }

    resp = client.post("/decks/new", data=json.dumps(payload), content_type="application/json", headers=auth_headers)
    assert resp.status_code == 201

    body = json.loads(resp.data)
    assert body["deck"]["deck_name"] == deck_name
    assert "d_id" in body["deck"]


def test_create_deck_duplicate_of_seeded_deck_returns_409(client, auth_headers):
    # conftest seeds Decks with name "Test Deck" for user 'test-user-id' :contentReference[oaicite:2]{index=2}
    payload = {"deck_name": "Test Deck", "word_lang": "Spanish", "trans_lang": "English"}

    resp = client.post("/decks/new", data=json.dumps(payload), content_type="application/json", headers=auth_headers)
    assert resp.status_code == 409


def test_create_deck_blank_name_returns_400(client, auth_headers):
    payload = {"deck_name": "   ", "word_lang": "French", "trans_lang": "English"}

    resp = client.post("/decks/new", data=json.dumps(payload), content_type="application/json", headers=auth_headers)
    assert resp.status_code == 400


def test_create_deck_missing_fields_returns_400(client, auth_headers):
    payload = {"deck_name": f"Missing Fields {uuid4()}"}

    resp = client.post("/decks/new", data=json.dumps(payload), content_type="application/json", headers=auth_headers)
    assert resp.status_code == 400