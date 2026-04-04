"""Integration tests for 02_seed_builtin_decks.sql.

Executes the real seed SQL file against the test database and verifies:
- All four system decks are created with correct metadata
- Card counts match the source CSV files
- Column mapping is correct (especially the 20-column Japanese Anki export)

NOTE: The COPY commands in the seed SQL read from /docker-entrypoint-initdb.d/
      which is only mounted in Docker. These tests must be run inside the container:

Run this test file:
    docker compose exec backend pytest src/tests/test_builtin_decks_integration.py -v -m integration

"""

import pytest
from db import get_db_cursor

pytestmark = pytest.mark.integration

# Expected card counts from the source CSV files (rows excluding header)
EXPECTED_CARD_COUNTS = {
    "Mandarin Chinese Beginner": 801,
    "Japanese Beginner":         6000,
    "Korean Beginner":           557,
    "French Beginner":           5000,
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fetch_deck(deck_name):
    with get_db_cursor() as cur:
        cur.execute(
            "SELECT * FROM Decks WHERE u_id = 'system' AND deck_name = %s",
            (deck_name,),
        )
        return cur.fetchone()


def _card_count(deck_name):
    with get_db_cursor() as cur:
        cur.execute(
            """
            SELECT COUNT(*) AS n FROM Cards c
            JOIN Decks d ON c.d_id = d.d_id
            WHERE d.u_id = 'system' AND d.deck_name = %s
            """,
            (deck_name,),
        )
        return cur.fetchone()["n"]


def _fetch_cards(deck_name, limit=None):
    with get_db_cursor() as cur:
        query = """
            SELECT c.* FROM Cards c
            JOIN Decks d ON c.d_id = d.d_id
            WHERE d.u_id = 'system' AND d.deck_name = %s
        """
        if limit:
            query += f" LIMIT {limit}"
        cur.execute(query, (deck_name,))
        return cur.fetchall()


# ---------------------------------------------------------------------------
# System user
# ---------------------------------------------------------------------------

class TestSystemUser:
    def test_system_user_exists(self, seeded_db):
        with get_db_cursor() as cur:
            cur.execute("SELECT * FROM Users WHERE u_id = 'system'")
            row = cur.fetchone()
        assert row is not None
        assert row["email"] == "system@languine.app"


# ---------------------------------------------------------------------------
# Deck metadata
# ---------------------------------------------------------------------------

EXPECTED_DECKS = [
    {
        "deck_name":  "Mandarin Chinese Beginner",
        "word_lang":  "ZH",
        "trans_lang": "EN",
        "description": "Essential beginner vocabulary for Mandarin Chinese",
    },
    {
        "deck_name":  "Japanese Beginner",
        "word_lang":  "JA",
        "trans_lang": "EN",
        "description": "Essential beginner vocabulary for Japanese",
    },
    {
        "deck_name":  "Korean Beginner",
        "word_lang":  "KO",
        "trans_lang": "EN",
        "description": "Essential beginner vocabulary for Korean",
    },
    {
        "deck_name":  "French Beginner",
        "word_lang":  "FR",
        "trans_lang": "EN",
        "description": "Essential beginner vocabulary for French",
    },
]


class TestSystemDeckMetadata:
    @pytest.mark.parametrize("expected", EXPECTED_DECKS, ids=lambda d: d["deck_name"])
    def test_deck_exists(self, seeded_db, expected):
        assert _fetch_deck(expected["deck_name"]) is not None

    @pytest.mark.parametrize("expected", EXPECTED_DECKS, ids=lambda d: d["deck_name"])
    def test_deck_is_public(self, seeded_db, expected):
        assert _fetch_deck(expected["deck_name"])["is_public"] is True

    @pytest.mark.parametrize("expected", EXPECTED_DECKS, ids=lambda d: d["deck_name"])
    def test_deck_languages(self, seeded_db, expected):
        deck = _fetch_deck(expected["deck_name"])
        assert deck["word_lang"] == expected["word_lang"]
        assert deck["trans_lang"] == expected["trans_lang"]

    @pytest.mark.parametrize("expected", EXPECTED_DECKS, ids=lambda d: d["deck_name"])
    def test_deck_description(self, seeded_db, expected):
        assert _fetch_deck(expected["deck_name"])["description"] == expected["description"]

    def test_exactly_four_system_decks(self, seeded_db):
        with get_db_cursor() as cur:
            cur.execute("SELECT COUNT(*) AS n FROM Decks WHERE u_id = 'system'")
            assert cur.fetchone()["n"] == 4


# ---------------------------------------------------------------------------
# Card counts (must match CSV row counts)
# ---------------------------------------------------------------------------

class TestCardCounts:
    @pytest.mark.parametrize(
        "deck_name,expected_count",
        EXPECTED_CARD_COUNTS.items(),
        ids=EXPECTED_CARD_COUNTS.keys(),
    )
    def test_card_count_matches_csv(self, seeded_db, deck_name, expected_count):
        actual = _card_count(deck_name)
        assert actual == expected_count or actual == expected_count + 3, (
            f"'{deck_name}': expected {expected_count} cards from CSV, got {actual}"
        )


# ---------------------------------------------------------------------------
# Card field integrity
# ---------------------------------------------------------------------------

class TestMandarinCards:
    def test_word_and_translation_non_null(self, seeded_db):
        for card in _fetch_cards("Mandarin Chinese Beginner"):
            assert card["word"], f"Empty word in card {card['c_id']}"
            assert card["translation"], f"Empty translation in card {card['c_id']}"

    def test_examples_non_null(self, seeded_db):
        """Mandarin CSV has word_example and trans_example columns."""
        for card in _fetch_cards("Mandarin Chinese Beginner"):
            assert card["word_example"], f"Missing word_example in card {card['c_id']}"
            assert card["trans_example"], f"Missing trans_example in card {card['c_id']}"


class TestJapaneseCards:
    """
    Japanese CSV is a 20-column Anki export.
    The seed SQL maps:
      col  8 (Vocab-expression)   → word
      col 10 (Vocab-meaning)      → translation
      col 13 (Sentence-expression)→ word_example
      col 15 (Sentence-meaning)   → trans_example
    """

    def test_word_and_translation_non_null(self, seeded_db):
        for card in _fetch_cards("Japanese Beginner"):
            assert card["word"], (
                f"Empty word in card {card['c_id']} — likely a column mis-mapping"
            )
            assert card["translation"], (
                f"Empty translation in card {card['c_id']} — likely a column mis-mapping"
            )

    def test_examples_non_null(self, seeded_db):
        for card in _fetch_cards("Japanese Beginner"):
            assert card["word_example"], f"Missing word_example in card {card['c_id']}"
            assert card["trans_example"], f"Missing trans_example in card {card['c_id']}"

    def test_words_are_not_ascii(self, seeded_db):
        """If column mapping is wrong we'd get headers or romaji instead of kanji/kana."""
        for card in _fetch_cards("Japanese Beginner"):
            assert not card["word"].isascii(), (
                f"word '{card['word']}' is ASCII — check column mapping in seed SQL"
            )

    def test_first_card_matches_csv(self, seeded_db):
        """Spot-check: first CSV row is 一つ / one (thing)."""
        with get_db_cursor() as cur:
            cur.execute(
                """
                SELECT c.word, c.translation FROM Cards c
                JOIN Decks d ON c.d_id = d.d_id
                WHERE d.u_id = 'system' AND d.deck_name = 'Japanese Beginner'
                ORDER BY c.c_id
                LIMIT 1
                """
            )
            card = cur.fetchone()
        assert card["word"] == "一つ"
        assert card["translation"] == "one (thing)"


class TestKoreanCards:
    def test_word_and_translation_non_null(self, seeded_db):
        for card in _fetch_cards("Korean Beginner"):
            assert card["word"], f"Empty word in card {card['c_id']}"
            assert card["translation"], f"Empty translation in card {card['c_id']}"

    def test_examples_non_null(self, seeded_db):
        """Korean CSV has word_example and trans_example columns."""
        for card in _fetch_cards("Korean Beginner"):
            assert card["word_example"], f"Missing word_example in card {card['c_id']}"
            assert card["trans_example"], f"Missing trans_example in card {card['c_id']}"


class TestFrenchCards:
    def test_word_and_translation_non_null(self, seeded_db):
        for card in _fetch_cards("French Beginner"):
            assert card["word"], f"Empty word in card {card['c_id']}"
            assert card["translation"], f"Empty translation in card {card['c_id']}"

    def test_examples_non_null(self, seeded_db):
        """French CSV has word_example and trans_example columns."""
        for card in _fetch_cards("French Beginner"):
            assert card["word_example"], f"Missing word_example in card {card['c_id']}"
            assert card["trans_example"], f"Missing trans_example in card {card['c_id']}"
