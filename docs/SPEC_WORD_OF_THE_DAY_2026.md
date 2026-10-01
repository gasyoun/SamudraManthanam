# Word of the Day — design spec

_Created: 16-09-2026 · Last updated: 16-09-2026_

Design decisions ruled by MG via interactive grill (Claude Code, 16-09-2026). This spec is the durable record for the future build handoff — no implementation has started yet.

## Scope

A daily-rotating Sanskrit word feature for [samskrtam.ru](https://samskrtam.ru), shown on the [SamudraManthanam](https://github.com/gasyoun/SamudraManthanam) web platform and cross-posted to social channels.

## Decisions (MG rulings, 16-09-2026)

1. **Data source: Kochergina LES1990.** Pull entries from the digitized Kochergina Sanskrit-Russian dictionary data in [SanskritLexicography/RussianTranslation](https://github.com/gasyoun/SanskritLexicography/tree/master/RussianTranslation) — already has RU glosses, no new translation work needed. **Open item for the build handoff:** locate/confirm the exact machine-readable LES1990 entry file (a research step, not assumed here — the directory holds many pipeline artifacts and no single obvious `les1990.json`/`.db` was found during this scoping pass).
2. **Surface: both.** A web widget/page in the SamudraManthanam FastAPI app (`web/app`) AND a daily auto-post to the site's existing Telegram/VK channels, reusing the content-calendar automation pattern already used for other scheduled posts (see [samskrte.ru canonical customer links](https://github.com/gasyoun/Uprava/blob/main/docs/CANONICAL_CUSTOMER_LINKS_2026.md) for the existing automation precedent, if applicable to this site).
3. **Selection: random, no-repeat.** Pick randomly from the eligible LES1990 entry pool each day; track already-shown words in a small state table (date, headword, entry id) so nothing repeats until the pool is exhausted, then reset.
4. **Content: dictionary fields + one corpus example.** Each entry shows headword, IAST transliteration, Devanagari, Russian gloss, part of speech, plus one real usage sentence pulled from SamudraManthanam's parallel-corpus search (Sanskrit + Russian translation pair).
5. **Automation: static nightly regeneration.** A scheduled job (cron) picks and writes the day's entry once per day into a static file/small table; the web widget reads that static output (no per-request compute), and the same output feeds the social-post script — one generation step, two consumers.

## Not yet decided / left to the build handoff

- Exact LES1990 source file/format and how to filter to entries with usable RU glosses.
- Where the no-repeat tracking table lives (SQLite table in the existing `web/` app DB is the natural default, given the app already uses SQLite FTS5).
- Which corpus-search API/function in SamudraManthanam to call for the example-sentence lookup, and the fallback behavior when a chosen word has no corpus attestation (skip and re-roll, or ship without an example that day).
- Telegram/VK posting mechanics — which existing script/credentials this site already uses for scheduled social posts, if any exist yet for samskrtam.ru specifically (distinct from the samskrte.ru tutoring-business automation referenced in Uprava's canonical links doc).
- Exact cron trigger (system cron vs. a hosting-provider scheduled task) and where in `deploy/` it should be wired.

## Acceptance criteria (for the eventual build handoff)

- A visitor to samskrtam.ru sees a word-of-the-day widget that changes once every 24h and never repeats a word until the full LES1990-derived pool has cycled once.
- Each shown word includes headword, IAST, Devanagari, RU gloss, POS, and either a corpus example sentence or an explicit graceful fallback.
- The same day's word is posted to the configured social channel(s) without manual intervention.
- No per-request runtime cost added to page load — the day's word is precomputed.

_Гасунс_
