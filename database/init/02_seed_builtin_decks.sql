-- Built-in reference decks seeded at database initialization.
-- Requires the following CSV files alongside this script in database/init/:
--   chinese_vocab_beginner.csv  (columns: translation, word, trans_example, word_example)
--   japanese_vocab_beginner.csv (20-column Anki export; uses Vocab-expression, Vocab-meaning,
--                        Sentence-expression, Sentence-meaning at cols 8, 10, 13, 15)
--   korean_vocab_beginner.csv   (columns: translation, word, trans_example, word_example)
--   french_vocab_beginner.csv (columns: translation, word)
-- All CSV files include a header row.

INSERT INTO Users (u_id, email, display_name, timezone)
VALUES ('system', 'system@languine.app', 'Languine', 'UTC')
ON CONFLICT (u_id) DO NOTHING;

INSERT INTO Decks (u_id, deck_name, word_lang, trans_lang, description, is_public)
VALUES
    ('system', 'Mandarin Chinese Beginner', 'Chinese (Mandarin)', 'English', 'Essential beginner vocabulary for Mandarin Chinese', true),
    ('system', 'Japanese Beginner',         'Japanese',           'English', 'Essential beginner vocabulary for Japanese',         true),
    ('system', 'Korean Beginner',           'Korean',             'English', 'Essential beginner vocabulary for Korean',           true),
    ('system', 'French Beginner',           'French',             'English', 'Essential beginner vocabulary for French',           true)

ON CONFLICT (u_id, deck_name) DO NOTHING;

-- Add decks to test user for development and testing (temporary)
INSERT INTO Decks (u_id, deck_name, word_lang, trans_lang, description, is_public)
VALUES
    ('112255507948077384809', 'Mandarin Chinese Beginner', 'Chinese (Mandarin)', 'English', 'Essential beginner vocabulary for Mandarin Chinese', true),
    ('112255507948077384809', 'Japanese Beginner',         'Japanese',           'English', 'Essential beginner vocabulary for Japanese',         true),
    ('112255507948077384809', 'Korean Beginner',           'Korean',             'English', 'Essential beginner vocabulary for Korean',           true),
    ('112255507948077384809', 'French Beginner',           'French',             'English', 'Essential beginner vocabulary for French',           true)

ON CONFLICT (u_id, deck_name) DO NOTHING;


-- ── Mandarin Chinese ──────────────────────────────────────────────────────────
CREATE TEMP TABLE tmp_cards (word text, translation text, word_example text, trans_example text);

COPY tmp_cards FROM '/docker-entrypoint-initdb.d/chinese_vocab_beginner.csv'
    WITH (FORMAT csv, HEADER);

INSERT INTO Cards (d_id, word, translation, word_example, trans_example)
SELECT deck.d_id, t.word, t.translation, t.word_example, t.trans_example
FROM tmp_cards t
CROSS JOIN (
    SELECT d_id FROM Decks WHERE u_id = 'system' AND deck_name = 'Mandarin Chinese Beginner'
) AS deck;

-- Add cards to test user for development and testing (temporary)
INSERT INTO Cards (d_id, word, translation, word_example, trans_example)
SELECT deck.d_id, t.word, t.translation, t.word_example, t.trans_example
FROM tmp_cards t
CROSS JOIN (
    SELECT d_id FROM Decks WHERE u_id = '112255507948077384809' AND deck_name = 'Mandarin Chinese Beginner'
) AS deck;

DROP TABLE tmp_cards;

-- ── Japanese ──────────────────────────────────────────────────────────────────
-- CSV columns (1-indexed):
--   8  Vocab-expression  → word
--  10  Vocab-meaning     → translation
--  13  Sentence-expression → word_example
--  15  Sentence-meaning  → trans_example
CREATE TEMP TABLE tmp_jp (
    c01 text, c02 text, c03 text, c04 text, c05 text,
    c06 text, c07 text,
    word         text,   -- col  8: Vocab-expression
    c09          text,
    translation  text,   -- col 10: Vocab-meaning
    c11 text, c12 text,
    word_example  text,  -- col 13: Sentence-expression
    c14          text,
    trans_example text,  -- col 15: Sentence-meaning
    c16 text, c17 text, c18 text, c19 text, c20 text
);

COPY tmp_jp FROM '/docker-entrypoint-initdb.d/japanese_vocab_beginner.csv'
    WITH (FORMAT csv, HEADER);

INSERT INTO Cards (d_id, word, translation, word_example, trans_example)
SELECT deck.d_id, t.word, t.translation, t.word_example, t.trans_example
FROM tmp_jp t
CROSS JOIN (
    SELECT d_id FROM Decks WHERE u_id = 'system' AND deck_name = 'Japanese Beginner'
) AS deck;

-- Add cards to test user for development and testing (temporary)
INSERT INTO Cards (d_id, word, translation, word_example, trans_example)
SELECT deck.d_id, t.word, t.translation, t.word_example, t.trans_example
FROM tmp_jp t
CROSS JOIN (
    SELECT d_id FROM Decks WHERE u_id = '112255507948077384809' AND deck_name = 'Japanese Beginner'
) AS deck;

DROP TABLE tmp_jp;

-- ── Korean ────────────────────────────────────────────────────────────────────
CREATE TEMP TABLE tmp_cards (word text, translation text, word_example text, trans_example text);

COPY tmp_cards FROM '/docker-entrypoint-initdb.d/korean_vocab_beginner.csv'
    WITH (FORMAT csv, HEADER);

INSERT INTO Cards (d_id, word, translation, word_example, trans_example)
SELECT deck.d_id, t.word, t.translation, t.word_example, t.trans_example
FROM tmp_cards t
CROSS JOIN (
    SELECT d_id FROM Decks WHERE u_id = '112255507948077384809' AND deck_name = 'Korean Beginner'
) AS deck;

-- Add cards to test user for development and testing (temporary)
INSERT INTO Cards (d_id, word, translation, word_example, trans_example)
SELECT deck.d_id, t.word, t.translation, t.word_example, t.trans_example
FROM tmp_cards t
CROSS JOIN (
    SELECT d_id FROM Decks WHERE u_id = 'system' AND deck_name = 'Korean Beginner'
) AS deck;

DROP TABLE tmp_cards;

-- ── French ────────────────────────────────────────────────────────────────────
CREATE TEMP TABLE tmp_cards (
    c01 text,
    word text, 
    translation text,
    c04 text, 
    word_example text,    
    trans_example text);

COPY tmp_cards FROM '/docker-entrypoint-initdb.d/french_vocab_beginner.csv'
    WITH (FORMAT csv, HEADER);

INSERT INTO Cards (d_id, word, translation, word_example, trans_example)
SELECT deck.d_id, t.word, t.translation, t.word_example, t.trans_example
FROM tmp_cards t
CROSS JOIN (
    SELECT d_id FROM Decks WHERE u_id = 'system' AND deck_name = 'French Beginner'
) AS deck;

-- Add cards to test user for development and testing (temporary)
INSERT INTO Cards (d_id, word, translation, word_example, trans_example)
SELECT deck.d_id, t.word, t.translation, t.word_example, t.trans_example
FROM tmp_cards t
CROSS JOIN (
    SELECT d_id FROM Decks WHERE u_id = '112255507948077384809' AND deck_name = 'French Beginner'
) AS deck;

DROP TABLE tmp_cards;
