# SamudraManthanam — OxAlpha 30-day retrospective code review (fixed window 26-07..25-08-2026)

_Created: 27-08-2026 · Last updated: 27-08-2026_

**Handoff:** H3552 (OxAlpha) — SamudraManthanam 30-day risk-ranked code review and future independent review gate.
**Executor:** OxAlpha (`x-preview-f-free`), session of 27-08-2026. Plan: [PLAN_SAMUDRAMANTHANAM_OXALPHA_CODE_REVIEW_HARDENING_2026Q3.md](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/PLAN_SAMUDRAMANTHANAM_OXALPHA_CODE_REVIEW_HARDENING_2026Q3.md).
**Method:** two independent passes per slice — **Standards** (quality/security against repo norms) and **Spec** (diff vs handoff/issue contract), resolved in the ruled order PR body → issue → handoff/plan → matching doc → `no spec available`. No finding without severity, file/line, failure mode, and repro or an explicit `no repro constructed`. Read-only reviews; repairs only for proven P0/P1 with regression tests.

## Window and slice selection

Fixed window 26-07-2026..25-08-2026. All ten plan-named candidates (#313, #311, #305, #304, #302, #297, #291, #274, #270, #263) landed 09-08..16-08-2026 — in-window — and every one carries executable code (web app, services, routers, deploy configs, ops scripts). **Retained: 10/10. Excluded: none** (no generated/vendor/data-only-only slice). Diffs taken against each PR's recorded base SHA and its landed squash/rebase commit on main (SHAs below).

## Risk ranking (1 = highest executable/critical-path risk)

| # | Rank | PR | Title | Base | Landed | Focus area |
|---|---|---|---|---|---|---|
| 1 | #313 | feat(ai): deny-by-default paid-AI spend policy | `4ed9515b8` | `ea5d0f2` | money / spend control |
| 2 | #311 | feat(ai): auth + hard monthly quota on /api/ai/* | `aa5c2d9b0` | `a2769a3` | money / spend control |
| 3 | #291 | feat(ops): HSTS + nginx security headers | `22eedd6a6` | `747e026` | security / prod edge |
| 4 | #302 | H2738 follow-up: coerce numeric chapter | `8a351b503` | `4eb1d35` | prod search path |
| 5 | #304 | H2751: pretty search IRIs | `14a266e0a` | `19dd838` | prod URLs / canonicals |
| 6 | #305 | H2752: short search IRI /s/ | `19dd83854` | `10ea7af` | prod URLs |
| 7 | #263 | H2433 Phase 4 web-pipeline hook | `63ebb6d40` | `08d24e8` | build/deploy surface |
| 8 | #297 | H2720 errata.yml + auto rebuild | `d7eb52f7d` | `00c4dfb` | corpus data integrity |
| 9 | #274 | H2390 health check as systemd timer | `e36d460cf` | `813e9fa` | ops / monitoring |
| 10 | #270 | H2390 health+search smoke cron | `595c0e696` | `c846128` | ops / monitoring (superseded by #274) |

## Findings ledger

Severity: P0 prod outage/data loss/security hole · P1 real bug/security weakness with concrete trigger · P2 quality/robustness · P3 style/doc debt.

| ID | Sev | Slice | Location | Failure mode | Proof | Disposition |
|---|---|---|---|---|---|---|
| F1 | **P1** | #297 | `web/corpus_builder/errata_yml.py` `apply_entries` | Extension fix (`read` ⊇ `instead`, e.g. `Ганг`→`Ганга`) re-applies on every run — run 2 yields `Гангаа`, reports `applied`, exit 0 | Repro executed against v0.19.47 (run1 `Ганга` / run2 `Гангаа`) | **Fixed** — [PR #336](https://github.com/gasyoun/SamudraManthanam/pull/336) (read-masked residue test + 2 regression tests; full suite 1028 passed) |
| F2 | **P1** | #304 | `web/static/search.js` `buildPermalink` pretty branch (~lines 231–237) | Permalink built by raw concatenation `'/s/' + q` with no sanitization — a query containing `?`, `#`, `/` produces a corrupted permalink; reload/shared link silently searches a truncated query (server twin `path_segment()` sanitizes; client never does) | Repro reasoned from code + server route behavior (`/search/X? 100` → results for `X` only); no JS test harness in repo to execute a browser-side repro | **Parked, not silently complete:** client-side repair requires refactoring a deployed jQuery IIFE asset and a JS regression harness the repo does not have; blocked by infra, not by the ruled stop conditions — follow-up row minted in GTD. Not fixed in this handoff. |
| F3 | P2 | #304 | `web/app/search_urls.py` `pretty_search_url` | Canonical URLs no longer normalize case (`cs` hardcoded false in pretty routes) — `/s/SVASTI` and `/s/svasti` return identical results with different `rel=canonical` → duplicate-content exposure returns | Code-derivable, both routes live | Report only (P2 = no repair under the plan) |
| F4 | P2 | #304 | `web/app/routers/home.py` `root()` | `/?q=…&src=1` (legacy numeric) and `src=a,b` 301 to an unfiltered pretty path — source filter silently dropped; `/search?q=` handles the same input correctly | Code-derivable | Report only |
| F5 | P2 | #297 | `errata_yml.py` `apply_entries` | `text` and `html` patched independently; if markup splits the typo, `text` is patched, served `html` keeps it, report says `applied` | Logical repro; not executed | Report only |
| F6 | P2 | #297 | `errata_yml.py` `write_jsonl` | Non-atomic in-place rewrite of canonical JSONL — crash mid-write truncates it (git-tracked recovery exists, hence P2) | Code-derivable | Report only |
| F7 | P2 | #297 | `errata_yml.py` `load_errata_yml` | BOM'd `errata.yml` parses to zero entries, applies nothing, exit 0 (`utf-8` not `utf-8-sig`) | Code-derivable | Report only |
| F8 | P2 | #297 | `README.md` + `apply_errata.py` default | Documented rebuild command writes HTML to `web/corpus_builder/jsonl/html/`, not the app data dir — silently stale site | Code-derivable | Report only |
| F9 | P2 | #291 | `scripts/enable_branded_hostname.py` hsts re-apply block | Writes the rewritten nginx vhost then runs `nginx -t` without backup/restore — on test failure a broken config is left on disk (the sibling `enable_security_headers.apply()` restores; this site does not) | Conditional trigger; code-derivable | Report only |
| F10 | P2 | #270/#274 | `scripts/health_monitor.py` `_save_state`/`_load_state` | Non-atomic state write + silent reset on `JSONDecodeError` — kill mid-write erases an in-progress failure streak, delaying CRITICAL by up to 5 ticks | Code-derivable (unfixed on main) | Report only |
| F11 | P2 | #270/#274 | `scripts/health_monitor.py` `check_search` | Missing/non-int `total` in a 200 envelope counts as pass — monitor blind to API shape drift, exactly what it exists to catch | No current repro (API returns int today) | Report only |
| F12 | P2 | #274 | OPS.md fail-inject + unit `User=samudra` | Documented root-shell fail-inject leaves root-owned state files; next timer run dies on `PermissionError` — monitor silently dead while nothing alerts about the monitor | Code-derivable | Report only |
| F13 | P2 | #274 | `deploy/samudra-health-monitor.{service,timer}` | No `OnFailure=` or any notification path — infra-level monitor death never fires (the handoff's own fail condition reached via infra) | Code-derivable | Report only |
| F14 | P2 | #263 | `scripts/run_headless_cb.py` `run_jobs` | Jobs row pointing `--out` into live `Data/` replaces a served HTML file non-atomically (superseded rsync flow was temp+rename) | Conditional (live-servicing unverified); no repro constructed | Report only |
| F15 | P3 | #311 | `routers/ai.py` `_require_quota` | Quota consumed before endpoint body validation (422 burns a call); over-limit calls still increment the counter | Design note | Report only |
| F16 | P3 | #313 | `ai_service.py` / `ai_cache.py` | Cache key excludes `max_tokens` (pre-existing; bound is config-uniform per deployment) | Design note | Report only |
| F17 | P3 | #304 | IRI pipeline | No NFC/NFD normalization — visually identical Cyrillic spellings yield distinct canonical URLs | Code-derivable | Report only |
| F18 | P3 | #304 | `RedirectResponse` sites | Literal `%` survives into `Location` → mojibake/wrong query on arrival; no injection (root-relative always) | Code-derivable | Report only |
| F19 | P3 | #263 | `docs/H2433_WEB_PIPELINE_HOOK.md`, CHANGELOG 0.19.30 | "gitignored if local-only" claim has no matching `.gitignore` entry; changelog/roadmap credit wrong model (Grok 4.5 did the work) | Doc drift | Report only |
| F20 | P3 | #297 | `errata_yml.py` | Hand-rolled YAML: inline `#` not stripped, `|`/`>` folded identically; checksum/_unquote dead (the `import re` half of this was removed in PR #336) | Robustness debt of the documented no-PyYAML choice | Report only |
| F21 | P3 | #270 | OPS.md cron entry | `>>` redirect swallows the claimed cron-mail alert; every line logged twice (superseded by #274's journald) | Doc drift, superseded | Report only |

## Per-slice verdicts

| PR | Standards | Spec | Spec source |
|---|---|---|---|
| #313 | CLEAN (F16 note) | SATISFIED | [H2866 handoff](https://github.com/gasyoun/Uprava/blob/main/handoffs/H2866-Opus_SamudraManthanam_paid-ai-spend-safety_16.08.26.md) |
| #311 | CLEAN (F15 note; CSRF refuted — session cookie `samesite="lax"`, `identity.py:166`) | SATISFIED | [issue #307](https://github.com/gasyoun/SamudraManthanam/issues/307) + H2640 §2.4 |
| #291 | FINDINGS (F9) — gate-before-enable design, backup/rollback/prove in `apply()` are sound | SATISFIED | H2398 handoff |
| #302 | CLEAN | SATISFIED | H2738 follow-up (changelog + issue) |
| #304 | FINDINGS (F2 P1, F3/F4 P2, F17/F18 P3) | SATISFIED against a title-only stub — the handoff's acceptance was never filled | [H2751 stub](https://github.com/gasyoun/Uprava/blob/main/handoffs/archive/H2751-Grok_SamudraManthanam_pretty-search-iris_14.08.26.md) |
| #305 | no new finding (mechanical prefix change; loop/redirect/route-order/JS checked) | SATISFIED | [H2752 handoff](https://github.com/gasyoun/Uprava/blob/main/handoffs/archive/H2752-Grok_SamudraManthanam_short-search-iri-s_14.08.26.md) |
| #297 | FINDINGS (F1 P1 → fixed, F5–F8 P2, F20 P3) | SATISFIED | [H2720 handoff](https://github.com/gasyoun/Uprava/blob/main/handoffs/archive/H2720-Grok_SamudraManthanam_corpus-errata-auto-rebuild_14.08.26.md) |
| #263 | FINDINGS (F14 P2, F19 P3) | PARTIAL (core contract delivered; roadmap tick landed in a later commit) | [H2433 handoff](https://github.com/gasyoun/Uprava/blob/main/handoffs/archive/H2433-Grok_SamudraManthanam_corpus-builder-p4-web-pipeline-hook_08.08.26.md) |
| #274 | FINDINGS (F12/F13 P2, +P3 timer hardening notes) | SATISFIED | H2390 handoff (follow-up documented in its evidence block) |
| #270 | FINDINGS (F10/F11 P2, F21 P3; mechanism superseded same-day by #274) | SATISFIED | H2390 handoff |

## Evidence

- **Adapter bootstrap (Wave 0, merged before this review):** [PR #334](https://github.com/gasyoun/SamudraManthanam/pull/334) + changelog [PR #335](https://github.com/gasyoun/SamudraManthanam/pull/335), release v0.19.47 cut from the resumed [PR #333](https://github.com/gasyoun/SamudraManthanam/pull/333) (original session hard-died; auto-resumed 27-08-2026).
- **Proven-P1 repair:** [PR #336](https://github.com/gasyoun/SamudraManthanam/pull/336) — failing-then-passing regression tests, full web suite 1028 passed / 7 skipped, ruff + black clean.
- **Known-inherited red (not introduced, not repaired here):** `npm build and high-severity audit` fails on main before and after this window (same failure on merged #335); all substantive gates green.
- **Known-inherited red (corpus invariant, pre-window):** the `Full corpus gate` ("Duplicate-suffix categorised invariant") fails with the same 47 `suffix_depth` violations on every run since at least v0.19.41 (13-08-2026) — every tag push v0.19.41..v0.19.47 and every corpus_builder-touching PR, including slices inside this window. PR #336 (pure errata-detection change, no id-generation path) reproduces the identical set; runs: [v0.19.47](https://github.com/gasyoun/SamudraManthanam/actions/runs/) tag push 27-08-2026 = PR #336 run 28-08-2026, both `FAIL 47 violation(s)`. The invariant has been advisory in practice for two weeks — a repair owner should be named outside this handoff (P2-class, data-splitter domain).
- Slices #313/#311/#291/#302 reviewed in the primary OxAlpha session; #305+#304, #297, #274+#270+#263 reviewed in three independent parallel review passes, findings verified against current main before publication.
- **F2 parked fix** carries an explicit stop note (JS test-harness infra gap) — it is NOT treated as complete; follow-up minted in [Uprava GTD](https://github.com/gasyoun/Uprava/blob/main/GTD_NEXT_ACTIONS.md).

_Dr. Mārcis Gasūns_
