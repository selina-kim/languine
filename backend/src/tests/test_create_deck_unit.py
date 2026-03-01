"""
Pure unit tests for create-deck (no conftest fixtures, no real DB).
"""

import json
import contextlib
from typing import Any, Dict, Optional

import pytest
import psycopg2
from flask import Flask

from flask_jwt_extended import JWTManager, create_access_token

import services.deck_service as deck_service_module
from services.deck_service import (
    DeckService,
    DuplicateDeckNameError,
    UserNotFoundError,
    DatabaseError,
)

# Import the blueprint module that defines the /decks/new route
# IMPORTANT: adjust this import if your route file path differs
from routes.decks import decks_bp


# -----------------------------
# Helpers for service unit tests
# -----------------------------
class _FakeIntegrityError(psycopg2.IntegrityError):
    def __init__(self, msg: str, pgcode: str):
        super().__init__(msg)
        self._pgcode = pgcode

    @property
    def pgcode(self):
        return self._pgcode


class _FakeCursor:
    def __init__(
        self,
        *,
        raise_on_execute: Optional[Exception] = None,
        fetchone_value: Optional[Dict[str, Any]] = None,
    ):
        self._raise_on_execute = raise_on_execute
        self._fetchone_value = fetchone_value or {
            "d_id": 123,
            "deck_name": "Unit Deck",
            "word_lang": "French",
            "trans_lang": "English",
            "description": "",
            "is_public": False,
            "link": None,
            "creation_date": "2026-02-27T00:00:00Z",
        }

    def execute(self, *_args, **_kwargs):
        if self._raise_on_execute:
            raise self._raise_on_execute

    def fetchone(self):
        return self._fetchone_value


def _fake_get_db_cursor_factory(fake_cursor: _FakeCursor):
    @contextlib.contextmanager
    def _cm(*_args, **_kwargs):
        yield fake_cursor

    return _cm


# -----------------------------
# DeckService.create_deck() tests
# -----------------------------
def test_service_create_deck_success_monkeypatched_cursor(monkeypatch):
    fake_cursor = _FakeCursor()
    monkeypatch.setattr(deck_service_module, "get_db_cursor", _fake_get_db_cursor_factory(fake_cursor))

    result = DeckService.create_deck(
        "test-user-id",
        {"deck_name": "Unit Deck", "word_lang": "French", "trans_lang": "English"},
    )

    assert isinstance(result, dict)
    assert result["deck_name"] == "Unit Deck"
    assert "d_id" in result


def test_service_create_deck_maps_unique_violation_to_duplicate(monkeypatch):
    err = _FakeIntegrityError("unique_violation", "23505")
    fake_cursor = _FakeCursor(raise_on_execute=err)
    monkeypatch.setattr(deck_service_module, "get_db_cursor", _fake_get_db_cursor_factory(fake_cursor))

    with pytest.raises(DuplicateDeckNameError):
        DeckService.create_deck(
            "test-user-id",
            {"deck_name": "Dup", "word_lang": "French", "trans_lang": "English"},
        )


def test_service_create_deck_maps_fk_violation_to_user_not_found(monkeypatch):
    err = _FakeIntegrityError("foreign_key_violation", "23503")
    fake_cursor = _FakeCursor(raise_on_execute=err)
    monkeypatch.setattr(deck_service_module, "get_db_cursor", _fake_get_db_cursor_factory(fake_cursor))

    with pytest.raises(UserNotFoundError):
        DeckService.create_deck(
            "missing-user",
            {"deck_name": "Deck", "word_lang": "French", "trans_lang": "English"},
        )


def test_service_create_deck_maps_other_psycopg2_error_to_database_error(monkeypatch):
    err = psycopg2.ProgrammingError("some db error")
    fake_cursor = _FakeCursor(raise_on_execute=err)
    monkeypatch.setattr(deck_service_module, "get_db_cursor", _fake_get_db_cursor_factory(fake_cursor))

    with pytest.raises(DatabaseError):
        DeckService.create_deck(
            "test-user-id",
            {"deck_name": "Deck", "word_lang": "French", "trans_lang": "English"},
        )


# -----------------------------
# Route tests WITHOUT repo conftest
# -----------------------------
@pytest.fixture
def mini_app():
    app = Flask(__name__)
    app.config["TESTING"] = True
    app.config["JWT_SECRET_KEY"] = "unit-test-secret-key-32-bytes-min!!"
    JWTManager(app)
    app.register_blueprint(decks_bp)
    return app


@pytest.fixture
def mini_client(mini_app):
    return mini_app.test_client()


@pytest.fixture
def mini_auth_headers(mini_app):
    with mini_app.app_context():
        token = create_access_token(identity="test-user-id")
    return {"Authorization": f"Bearer {token}"}


def test_route_create_deck_success_with_mocked_service(mini_client, mini_auth_headers, monkeypatch):
    def _fake_create_deck(_user_id, data):
        return {
            "d_id": 999,
            "deck_name": data["deck_name"],
            "word_lang": data["word_lang"],
            "trans_lang": data["trans_lang"],
            "description": data.get("description", ""),
            "is_public": bool(data.get("is_public", False)),
            "link": data.get("link"),
        }

    monkeypatch.setattr(DeckService, "create_deck", staticmethod(_fake_create_deck))

    payload = {
        "deck_name": "Route Unit Deck",
        "word_lang": "French",
        "trans_lang": "English",
        "description": "unit test",
    }

    resp = mini_client.post("/decks/new", data=json.dumps(payload), content_type="application/json", headers=mini_auth_headers)
    assert resp.status_code == 201

    body = json.loads(resp.data)
    assert body["deck"]["deck_name"] == "Route Unit Deck"
    assert body["deck"]["d_id"] == 999


def test_route_create_deck_blank_name_returns_400(mini_client, mini_auth_headers):
    payload = {"deck_name": "   ", "word_lang": "French", "trans_lang": "English"}
    resp = mini_client.post("/decks/new", data=json.dumps(payload), content_type="application/json", headers=mini_auth_headers)
    assert resp.status_code == 400

    body = json.loads(resp.data)
    assert "deck_name" in body["error"]


def test_route_create_deck_duplicate_returns_409(mini_client, mini_auth_headers, monkeypatch):
    def _raise_dup(_user_id, _data):
        raise DuplicateDeckNameError("A deck with this name already exists for you")

    monkeypatch.setattr(DeckService, "create_deck", staticmethod(_raise_dup))

    payload = {"deck_name": "Dup", "word_lang": "French", "trans_lang": "English"}
    resp = mini_client.post("/decks/new", data=json.dumps(payload), content_type="application/json", headers=mini_auth_headers)
    assert resp.status_code == 409


def test_route_create_deck_user_not_found_returns_401(mini_client, mini_auth_headers, monkeypatch):
    def _raise_nf(_user_id, _data):
        raise UserNotFoundError("User not registered")

    monkeypatch.setattr(DeckService, "create_deck", staticmethod(_raise_nf))

    payload = {"deck_name": "Deck", "word_lang": "French", "trans_lang": "English"}
    resp = mini_client.post("/decks/new", data=json.dumps(payload), content_type="application/json", headers=mini_auth_headers)
    assert resp.status_code == 401


def test_route_create_deck_database_error_returns_500(mini_client, mini_auth_headers, monkeypatch):
    def _raise_db(_user_id, _data):
        raise DatabaseError("Database error")

    monkeypatch.setattr(DeckService, "create_deck", staticmethod(_raise_db))

    payload = {"deck_name": "Deck", "word_lang": "French", "trans_lang": "English"}
    resp = mini_client.post("/decks/new", data=json.dumps(payload), content_type="application/json", headers=mini_auth_headers)
    assert resp.status_code == 500