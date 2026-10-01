-- 0006 — word-of-the-day no-repeat tracking (H4955).
--
-- One row per entry_id shown, ever (within the current cycle). The nightly
-- picker (scripts/word_of_day_generate.py) excludes every entry_id present
-- here from the day's random draw; when the pool is exhausted it truncates
-- this table and starts a fresh cycle (see word_of_day_generate.py
-- pick_entry()). shown_date is diagnostic (last-shown date), not the join key.

CREATE TABLE IF NOT EXISTS word_of_day_shown (
    entry_id   TEXT PRIMARY KEY,
    headword   TEXT NOT NULL,
    shown_date TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_word_of_day_shown_date
    ON word_of_day_shown(shown_date);
