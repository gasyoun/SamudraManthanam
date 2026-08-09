# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]
### Fixed
- **Wave P4 health monitor: cron → systemd timer correction (H2390 follow-up, Sonnet 5 `claude-sonnet-5`).** The 0.19.33 entry below described a root-crontab line; that would have been silently wiped the next time Systema's [`scripts/server_guards_apply.sh`](https://github.com/gasyoun/Systema-Sanscriticum/blob/main/scripts/server_guards_apply.sh) re-renders root's crontab (it fully overwrites it from a template on every run, keyed only off `AUTO_DEPLOY_SCHEDULE`). Replaced with [`deploy/samudra-health-monitor.service`](https://github.com/gasyoun/SamudraManthanam/blob/main/deploy/samudra-health-monitor.service) + [`deploy/samudra-health-monitor.timer`](https://github.com/gasyoun/SamudraManthanam/blob/main/deploy/samudra-health-monitor.timer) (`OnUnitActiveSec=15min`), a unit outside that managed file. `OPS.md` and the script docstring updated accordingly.

## [0.19.34] - 2026-08-09
### Added
- **P8 performance baseline against the public prod URL (H2395, Sonnet 5 `claude-sonnet-4-5`).** Ran [`web/scripts/performance_baseline.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/scripts/performance_baseline.py) against `https://samudra.193.232.229.92.sslip.io` (230 sources, corpus `2026.08`) instead of localhost, refreshing [`docs/PERFORMANCE_BASELINES.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/PERFORMANCE_BASELINES.md). Two measurements over budget, recorded as exceptions per VERIFICATION: `plain_search_p95[atman]` (700ms vs 500ms, 1.4×) and `reader_lookup_p95` (635ms vs 500ms, 1.3×, now against `/01_atharvaveda`); `catastrophic_regex` improved to within budget (1671ms vs 2000ms).
- **Wave P6: offline packs built and served on prod (H2392, Sonnet 5 `claude-sonnet-5`).** Ran [`scripts/build_offline_pack.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/scripts/build_offline_pack.py) against the live `/opt/samudra/db/corpus.db`: `base.db` 469,192 rows, 283.9 MB raw → 109.5 MB wire (limit 130 MB); `dict.db` 254,037 rows, 86.8 MB raw → 36.8 MB wire (limit 90 MB). Found and fixed a real prod blocker: `/opt/samudra/repo/web/offline-packs/` was `root:samudra` mode `755` (no group-write), so the `samudra` service user's temp-file write failed with `unable to open database file` even though `corpus.db` itself was readable — fixed with `chown samudra:samudra` + `chmod 775`. Verified `/api/corpus-version` and both `/api/offline-packs/{base,dict}.db` return 200 with correct `content-encoding: gzip` / `x-db-bytes` headers. Recipe added to [`OPS.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/OPS.md) § Offline packs; roadmap Wave P6 ticked. Doc: [`docs/H2392_OFFLINE_PACKS_PROD_STATUS.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/H2392_OFFLINE_PACKS_PROD_STATUS.md).

## [0.19.33] - 2026-08-09
### Added
- **Wave P4 health + search smoke monitor and alert path (H2390, Sonnet 5 `claude-sonnet-5`).** New [`scripts/health_monitor.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/scripts/health_monitor.py): stdlib-only (no extra deps), single-shot worker that hits `/api/health` and a `/api/search` probe on every invocation, appends `PASS`/`FAIL` lines to `/opt/samudra/logs/health_monitor.log`, tracks consecutive failures in a JSON state file, and writes a `CRITICAL:` alert to `health_monitor_journal.log` after 5 consecutive failures (circuit-breaker); auto-logs `RECOVERY` when the counter resets. Run every 15 minutes via a systemd timer (see `[Unreleased]` above — corrected from an initial cron design same-day). [`OPS.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/OPS.md) updated with monitor section, log-files table, alert path, manual fail-inject smoke commands, and env overrides.

## [0.19.32] - 2026-08-09
### Added
- **P7 zero-orphan gate run against real prod state+corpus (H2393, Sonnet 5 `claude-sonnet-4-5`).** Ran [`web/scripts/zero_orphan_report.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/scripts/zero_orphan_report.py) on `root@193.232.229.92` against the live `/opt/samudra/db/state.db` + `/opt/samudra/db/corpus.db` (before `v2026.07.15`/611,569 lines → candidate `2026.08`/671,250 lines), with `--rollback-rehearsal`. Result: `ZERO-ORPHAN: PASS`, rollback rehearsal SAFE — but `references_checked: 0` since prod's `corrections` table currently holds no rows, so this proves the pipeline runs clean end-to-end on real non-fixture data, not non-vacuous orphan survival yet. Report: [`reports/zero_orphan_prod_2026-08-09.json`](https://github.com/gasyoun/SamudraManthanam/blob/main/reports/zero_orphan_prod_2026-08-09.json). Status doc: [`docs/H2393_ZERO_ORPHAN_PROD_GATE_STATUS.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/H2393_ZERO_ORPHAN_PROD_GATE_STATUS.md).

## [0.19.32] - 2026-08-09
### Added
- **Daily DB backups with 7-day retention (H2389, Sonnet 5 `claude-sonnet-5`).** New [`scripts/db_backup.sh`](https://github.com/gasyoun/SamudraManthanam/blob/main/scripts/db_backup.sh) uses `sqlite3 .backup` (WAL-safe) to back up `corpus.db` + `state.db` to `/opt/samudra/db/backups/` with `YYYYMMDD_HHMMSS` suffix; `find -mtime +7` prunes stale backups and `-shm`/`-wal` sidecars. Installed on prod as `/usr/local/sbin/samudra-db-backup.sh`; wired via `/etc/cron.d/samudra-db-backup` (03:07 UTC daily). Restore dry-run PASS. OPS.md § DB backups added. Wave P3 exit.

## [0.19.31] - 2026-08-09
### Added
- **Corpus_builder Phase 4 CI job — golden tests on Linux (H2434, Sonnet 4.6 `claude-sonnet-4-6`, override of Grok lock).** New [`.github/workflows/corpus-builder-golden.yml`](https://github.com/gasyoun/SamudraManthanam/blob/main/.github/workflows/corpus-builder-golden.yml): `lazbuild` builds `cb_headless.lpi` on `ubuntu-latest` (reusing the H2431 toolchain steps), then runs [`Corpus_builder/tests/golden/run_golden_case01.py --verify`](https://github.com/gasyoun/SamudraManthanam/blob/main/Corpus_builder/tests/golden/run_golden_case01.py) against the case01 baseline (H2427); fails closed if `expected/` is missing/empty or the build/binary is absent. Fixed a latent bug in the golden script's `EXE_CANDIDATES` list, which only listed Windows paths and would have made `--verify` unable to find the Linux binary. Triggers on push/PR touching `Corpus_builder/**`. Roadmap Phase 4 CI-job checkbox ticked.

## [0.19.30] - 2026-08-09
### Added
- **Corpus_builder Phase 4 web-pipeline hook (H2433, Sonnet 5 `claude-sonnet-4-5`).** Wired headless `cb_headless` (H2432) into a scripted pre-ingest step. New [`scripts/run_headless_cb.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/scripts/run_headless_cb.py) runs JSONL-configured `cb_headless --build/--out/--check` jobs before DB ingest; called from [`reindex.sh`](https://github.com/gasyoun/SamudraManthanam/blob/main/reindex.sh) and [`build-web-db.ps1`](https://github.com/gasyoun/SamudraManthanam/blob/main/build-web-db.ps1). No jobs file / `SKIP_HEADLESS_CB=1` → no-op, so prod's prebuilt-HTML rsync flow is unaffected. Jobs example: [`Corpus_builder/pipeline/headless_jobs.example.jsonl`](https://github.com/gasyoun/SamudraManthanam/blob/main/Corpus_builder/pipeline/headless_jobs.example.jsonl). Hermetic tests: [`web/tests/test_run_headless_cb.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/tests/test_run_headless_cb.py) (13 passed). Doc: [`docs/H2433_WEB_PIPELINE_HOOK.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/H2433_WEB_PIPELINE_HOOK.md).

## [0.19.29] - 2026-08-08
### Fixed
- **Linux lazbuild unit filenames (H2431 follow-up, Grok 4.5 `grok-4.5`).** FPC on Linux searches for lowercase unit files; rename builder `dcu/TextU.pas`→`textu.pas`, `CalcSimU`→`calcsimu`, `ArtMath`→`artmath`, `uEncoding`→`uencoding`, `uSort`→`usort`, `TextUVCL`→`textuvcl`. CI: [run 31258164782](https://github.com/gasyoun/SamudraManthanam/actions/runs/31258164782) green.

## [0.19.29] - 2026-08-08
### Added
- **H2450 remainder reparse (Grok 4.5 grok-4.5).** New racket-free footnote mode: free-form [N] text notes linked by first inline use. Auto chain: structured → prose (≥10) → free (≥3). Colophon skip so MBH notes collect after «ТАК ЗАКАНЧИВАЕТСЯ». Shared note block attached to MBH 16–18. Results: kama prose 489; MBH free 154+55+127 comments; yoni 13; kadambara/bhagavati residue documented. Driver h2450_remainder_reparse.py; doc docs/H2450_REMAINDER_REPARSE.md; summary jsonl/h2450_remainder_reparse_summary.json.

## [0.19.28] - 2026-08-08
### Added
- **Wave P5 branded hostname path (H2391, Grok 4.5 `grok-4.5`) — agent half only.** DNS-gated [`scripts/enable_branded_hostname.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/scripts/enable_branded_hostname.py) (exit 2 on NXDOMAIN / wrong A; `--apply` injects `server_name`, certbot, dual smoke). Operator docs: [`DEPLOYMENT.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/DEPLOYMENT.md) § Branded hostname, [`OPS.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/OPS.md) § Branded hostname, status [`docs/H2391_BRANDED_HOSTNAME_TLS_STATUS.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/H2391_BRANDED_HOSTNAME_TLS_STATUS.md). **Not done until human A-record + HTTPS 200** (measured 08-08-2026: `samudra.samskrte.ru` NXDOMAIN; sslip remains public).

## [0.19.27] - 2026-08-08
### Changed
- **Corpus_builder Phase 1 unified encoding layer (H2428, Grok 4.5 `grok-4.5`).** New [`dcu/uEncoding.pas`](https://github.com/gasyoun/SamudraManthanam/blob/main/Corpus_builder/PSRCBuilder/dcu/uEncoding.pas) (`ToUTF8`/`FromUTF8`/`EncUTF8Length`/`EncUTF8Copy`); engine + forms + TextU free of raw `AnsiToUTF8`/`UTF8ToAnsi` (census 21+27 → 0 active). `lazbuild cb.lpi` + `cb_headless.lpi` green. Golden case01 rebaselined for UTF-8 I/O (H2427 CP-1251 `Err.txt` → UTF-8). Roadmap Phase 1 encoding unit ticked. Doc: [`docs/H2428_LAZUTF8_ENCODING_LAYER.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/H2428_LAZUTF8_ENCODING_LAYER.md).
- **Corpus_builder Phase 2 shared utils via OtherUnitFiles (H2430, Grok 4.5 `grok-4.5`).** `cb.lpi` / `cb_headless.lpi` set `OtherUnitFiles=dcu;..\..\Units`; single [`Units/uTypes.pas`](https://github.com/gasyoun/SamudraManthanam/blob/main/Units/uTypes.pas) (promoted `TWideStringArr`; obsolete `dcu/uTypes` removed). Builder `TextU` dual-kept in `dcu/` (name collision with Index `textu`, H2429). Phase-2 common-dir + SHARED_CODE registration checkboxes ticked. Doc: [`docs/H2430_OTHERUNITFILES_SHARED_UTILS.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/H2430_OTHERUNITFILES_SHARED_UTILS.md). `lazbuild` green: cb (7318 lines), cb_headless, Index.

### Fixed
- **`cb_headless.lpr` program terminator** was `end;` (FPC Fatal 2003); corrected to `end.` so headless `lazbuild` links again (noticed while proving H2430).

## [0.19.27] - 2026-08-08
### Added
- **Prose commentary apparatus for Ignatiev remainder works (H2450, Grok 4.5 grok-4.5).** Third footnote front-end --footnote-mode prose on [ignatiev_book_to_canonical.py](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/ignatiev_book_to_canonical.py): print-style N. notes after KOMMENTARIJ, multi-line, link note#=verse#, wrap false-start reject. auto upgrades when bracket empty and prose density >=3. Pilot Kama-samuha: 685 verses / 489 comments / 17 unlinked; verse RT 100%, comment-text RT 100%. HTML comment ids comment_ch_v_fn. Driver h2450_prose_commentary_pilot.py; docs/H2450_PROSE_COMMENTARY_APPARATUS.md; jsonl/h2450_kama_samuha_prose_pilot.json.

## [0.19.26] - 2026-08-08
### Added
- **H2394 P9 UX acceptance on prod (Grok 4.5 `grok-4.5`).** Bilingual Sa+Ru + deep-link probes against `https://samudra.193.232.229.92.sslip.io/` — **11/11 PASS** (vishnu-smriti, yajnavalkyasmriti, ṛgveda). Checklist + probe script + JSON: [`docs/acceptance/H2394_UX_ACCEPTANCE_BILINGUAL_DEEPLINK_CHECKLIST.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/acceptance/H2394_UX_ACCEPTANCE_BILINGUAL_DEEPLINK_CHECKLIST.md). Wave P P9 ticked.
- **Production deploy runbook (H2388, Grok 4.5 `grok-4.5`).** New
  [OPS.md](https://github.com/gasyoun/SamudraManthanam/blob/main/OPS.md):
  copy-paste pull `--ff-only` / pip / `systemctl restart samudra` / smoke /
  code rollback, grounded in live LXC layout (`/opt/samudra` on
  `193.232.229.92`). [DEPLOYMENT.md](https://github.com/gasyoun/SamudraManthanam/blob/main/DEPLOYMENT.md)
  points day-2 ops there; layout/`state.db` path aligned with prod; corpus vs
  code rollback separated. Wave P2 exit.

### Fixed
- **Corpus_builder Linux `lazbuild` gates (H2431, Grok 4.5 `grok-4.5`).** Phase 3 residual after H2417 (Win-only): `fMainForm` drops `Windows`/`ShellApi` — 12× `ShellExecute` → LCL `OpenDocument`, `MessageBeep` → `Beep`, WinAPI `CopyFile` → `FileUtil.CopyFile`; `uMhHTML` `GlobalMemoryStatus` only under `{$IFDEF MSWINDOWS}`; `cb.lpi`/`cb_headless.lpi` host-default target + portable `dcu/` / `../../Units` paths. Win64 regression green (`docs/H2431_WIN64_REGRESSION.log`). CI: `.github/workflows/corpus-builder-lazbuild.yml` builds both projects on `ubuntu-latest`. Doc: [`docs/H2431_LINUX_LAZBUILD.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/H2431_LINUX_LAZBUILD.md).

## [0.19.25] - 2026-08-08
### Added
- **Corpus_builder Phase 4 headless CLI flags (H2432, Grok 4.5 `grok-4.5`).** [`cb_headless.lpr`](https://github.com/gasyoun/SamudraManthanam/blob/main/Corpus_builder/PSRCBuilder/cb_headless.lpr) accepts `cb_headless --build <config.ini|dir> [--out <file.html>] [--check]`; wires progress/error sinks to stdout; Confirm auto-yes (no MessageDlg hang); exit **1** on `HasErrors`, **2** on usage/missing config. Engine: public `OutFileOverride` on `TMhHTMLBuilder` for `--out`. Legacy `cb_headless <dir> [check]` kept for H2427 golden. Roadmap Phase 4 CLI unit ticked. README ┬з Headless CLI. Doc: [`docs/H2432_CLI_HEADLESS_BUILD.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/H2432_CLI_HEADLESS_BUILD.md).

## [0.19.24] - 2026-08-08
### Added
- **Corpus_builder Phase 2 dcu vs Units canonical diff (H2429, Grok 4.5 `grok-4.5`).** Written comparison of builder `TextU`/`uTypes` vs `Units/` twins: sizes, API deltas, consumer-safe **split** ruling (builder TextU for `cb`; Index `textu` is not a twin; `uTypes` master = builder). Phase-2 first roadmap checkbox ticked. Report: [`docs/H2429_DCU_UNITS_CANONICAL_DIFF.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/H2429_DCU_UNITS_CANONICAL_DIFF.md).
- **Corpus_builder Phase 0 golden + Phase 3 re-verify (H2427, Grok 4.5 grok-4.5).** case01 fixtures under tests/golden/case01/; headless cb_headless (console) drives TMhHTMLBuilder + CheckAll; run_golden_case01.py --verify byte-exact PASS ├Ч2. CheckPages base-count fix; portable check JSON input basename; RusPage init. Doc: [docs/H2427_GOLDEN_CAPTURE_P3_VERIFY.md](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/H2427_GOLDEN_CAPTURE_P3_VERIFY.md).

### Fixed
- **Bс╣Ыhann─лla-tantra JSONL duplicate comment IDs** (48 identical double rows) blocked full-pin web publish; dropped dups (2533тЖТ2485 records). Rebuild corpus-manifest pin: **230** sources / **723тАп229** records. `*.jsonl text eol=lf` in `.gitattributes` so Windows pin builds match Linux publish.
- **Search stats show server elapsed time** permanently in the result strip (not only a 1.2 s flash on the progress bar).
- **AI ╨а╨░╨╖╨▒╨╛╤А `[object Object]`** on long context lines: client truncates each line to 2000 chars (server cap) and formats FastAPI validation `detail` arrays as readable messages (H2426).

### Changed
- **Compact source overview** replaces the multi-screen SVG bar chart (159├Ч24 px for ┬л╨╛╨│╨╛╨╜╤М┬╗). Top-15 text list + residue + optional scroll for the rest.

### Added
- **`web/scripts/source_overview.py`** тАФ CLI text report of hits by source (top-N + residue, optional `--out` / `--json`).
- **H2415 residual: Ignatiev preface + glossary/bibliography layers (H2449, Grok 4.5 `grok-4.5`).** 17 registered companion sources (700 records): prefaces, four K─Бma-sam┼лha glossaries, MBH name/term glossaries, literature/sources, about-author тАФ cut by H2415 as non-verse. Parser [`ignatiev_backmatter.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/ignatiev_backmatter.py); driver [`h2449_backmatter_ingest.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/h2449_backmatter_ingest.py); census [`docs/H2449_IGNATIEV_BACKMATTER_LAYERS_CENSUS.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/H2449_IGNATIEV_BACKMATTER_LAYERS_CENSUS.md); summary [`jsonl/wave_h2449_backmatter_summary.json`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/jsonl/wave_h2449_backmatter_summary.json). Layer RT **100%** (1 soft Latin-accent fold on K─Бdambara literatura). Prose commentary remains H2450.
## [0.19.22] - 2026-08-08
### Added
- **H1438 archive remainder ingest (H2415, Grok 4.5 `grok-4.5`).** Seven new ru_only sources registered in `Programdata/data.txt`: K─Бma-sam┼лha (685 v), K─Бdambara-sv─лkaraс╣Зa-k─Бrik─Б (128 v), MBH XVIтАУXVIII Ignatiev (285+110+319 v; distinct from Vasilkov/Neveleva 16тАУ18_*), yoni-p┼лj─Б texts (16 v), Bhagavat─л-m─Бnasa-p┼лj─Б-stotra (69 v). All HTMLтЖТJSONL RT **100%**. Driver [`h2415_remainder_ingest.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/h2415_remainder_ingest.py); census [`docs/H2415_IGNATIEV_ARCHIVE_REMAINDER_CENSUS.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/H2415_IGNATIEV_ARCHIVE_REMAINDER_CENSUS.md); summary [`jsonl/wave_h2415_remainder_summary.json`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/jsonl/wave_h2415_remainder_summary.json). Corpus-manifest pin rebuilt (209 sources / 693тАп990 records).

### Changed
- **Chapter-open trailing footnote ref (H2415).** `╨У╨╗╨░╨▓╨░ ╤З╨╡╤В╨▓╨╡╤А╤В╨░╤П[249]` opens ch.4 (MBH Ignatiev book 18); unit test `test_chapter_open_allows_trailing_footnote_ref`. Doc: [`PDF_INGESTION_PIPELINE.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/PDF_INGESTION_PIPELINE.md) ┬з Wave remainder.

## [0.19.21] - 2026-08-08
### Added
- **Corpus_builder Phase 3 Lazarus/FPC LCL port (H2417, Grok 4.5 `grok-4.5`).** New [`PSRCBuilder/cb.lpr`](https://github.com/gasyoun/SamudraManthanam/blob/main/Corpus_builder/PSRCBuilder/cb.lpr) + [`cb.lpi`](https://github.com/gasyoun/SamudraManthanam/blob/main/Corpus_builder/PSRCBuilder/cb.lpi); forms as `.lfm`; `{$MODE Delphi}` on engine/utility units. FPC portability fixes (WideString digit ranges in `uMhHTML`, CP-1251 set-of-char тЖТ Ord/`IsRussian*` helpers). **`lazbuild` green** on Windows x64 (1603 lines тЖТ `lib/x86_64-win64/cb.exe`). Log: [`docs/H2417_LAZARUS_BUILD_WIN64.log`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/H2417_LAZARUS_BUILD_WIN64.log). Residuals: golden `expected/` capture (Phase 0), Linux `lazbuild`, lazUTF8 encoding layer, Phase 2 unit dedupe.

## [0.19.20] - 2026-08-08
### Changed
- **Wave-A PDF tantras glued-digit re-baseline (H2412тАУH2414, Grok 4.5 `grok-4.5`).** Yoni 221/0тЖТ221/192, Niruttara 674/0тЖТ676/322, Guptas─Бdhana 319/0тЖТ319/368 comments; HTMLтЖТJSONL тЙе99.9%; all re-run stable. Census of all Ignatiev registered works: docx stay bracket. Doc: [`docs/WAVE_A_PDF_GLUED_DIGIT_REBASELINE_H2412_14.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/WAVE_A_PDF_GLUED_DIGIT_REBASELINE_H2412_14.md). Residual archive remainder: H2415.

## [0.19.8] - 2026-08-07
### Changed
- **H2370 optional FPC compile residual (Grok 4.5 `grok-4.5`).** Installed Free Pascal 3.2.2 (user prefix); portable stack `mytypes`тАж`uSort` **compiles and runs** smoke after Dialogs removal. Full `cb.dpr` still needs Delphi 7 `dcc32` (absent). `TextU` has one pre-existing CP-1251 char-set FPC error (not H2370). Logs: [`docs/H2370_FPC_USORT_COMPILE.log`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/H2370_FPC_USORT_COMPILE.log), [`docs/H2370_DEAD_VCL_STATIC_PROOF.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/H2370_DEAD_VCL_STATIC_PROOF.md) ┬з FPC compile proof.
- **Nirv─Бс╣Зa-tantra glued-digit re-baseline (H2385, Grok 4.5 `grok-4.5`).** Re-ingest with H2377 `--footnote-mode glued-digit`: **465 тЖТ 527** RU verses, **0 тЖТ 212** comments, gaps 64тЖТ3, no id_collisions, HTMLтЖТJSONL **100%**. Doc: [`docs/NIRVANA_TANTRA_GLUED_DIGIT_REBASELINE_H2385.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/NIRVANA_TANTRA_GLUED_DIGIT_REBASELINE_H2385.md). H2273 debris-path note updated with supersession pointer.

## [0.19.9] - 2026-08-07
### Changed
- **H2370 optional FPC compile residual (Grok 4.5 `grok-4.5`).** Installed Free Pascal 3.2.2 (user prefix); portable stack `mytypes`тАж`uSort` **compiles and runs** smoke after Dialogs removal. Full `cb.dpr` still needs Delphi 7 `dcc32` (absent). `TextU` has one pre-existing CP-1251 char-set FPC error (not H2370). Logs: [`docs/H2370_FPC_USORT_COMPILE.log`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/H2370_FPC_USORT_COMPILE.log), [`docs/H2370_DEAD_VCL_STATIC_PROOF.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/H2370_DEAD_VCL_STATIC_PROOF.md) ┬з FPC compile proof.
- **Nirv─Бс╣Зa-tantra glued-digit re-baseline (H2385, Grok 4.5 `grok-4.5`).** Re-ingest with H2377 `--footnote-mode glued-digit`: **465 тЖТ 527** RU verses, **0 тЖТ 212** comments, gaps 64тЖТ3, no id_collisions, HTMLтЖТJSONL **100%**. Doc: [`docs/NIRVANA_TANTRA_GLUED_DIGIT_REBASELINE_H2385.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/NIRVANA_TANTRA_GLUED_DIGIT_REBASELINE_H2385.md). H2273 debris-path note updated with supersession pointer.

## [0.19.7] - 2026-08-07
### Added
- **M─Бy─Б-tantra glued-digit front-end + ingest (H2377, Grok 4.5 `grok-4.5`).** New `--footnote-mode glued-digit|bracket|auto` on `ignatiev_book_to_canonical.py`: page-local DBhP-style notes stripped before verse split; inline glued-digit linking; ToC ghost-chapter drop. M─Бy─Б registered: **12 ch / 343 RU verses / 148 comments**, HTMLтЖТJSONL round-trip **100%**, re-run stable. `auto` stays `bracket` (Wave-A count lock). Design: [`docs/MAYA_TANTRA_GLUED_DIGIT_MODE_H2377.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/MAYA_TANTRA_GLUED_DIGIT_MODE_H2377.md). Corpus-manifest pin rebuilt.

## [0.19.5] - 2026-08-07
### Added
- **H1438 Wave D: six Ignatiev fragments / selected works (H2376, Grok 4.5 `grok-4.5`).** All registered in `Programdata/data.txt` with desktop HTML + JSONL + `*.meta.json` carrying **explicit partial provenance**. Dev─л-pur─Бс╣Зa ch.22 (18 v); Liс╣Еga-pur─Бс╣Зa ch.17+29 (124 v); Padma J─Бlandhara tale only (16 ch / 1039 v тАФ NOT whole Padma); Bh─Бgavata partial prose (13 ch / 1176 paragraph units); Bс╣Ыhann─лla selected (18 ch / 1387 v / 1146 notes); ┼Ъ─Бktisaс╣Еgama selected (28 ch / 1494 v). HTMLтЖТJSONL round-trip тЙе99% except Bс╣Ыhann─лla **97.4%** (documented: 36 endnote-adjacent passages re-keyed as `.commN`). Parser/extract hardenings: excerpt `╨Ш╨╖ тАж ╨│╨╗╨░╨▓╤Л`, trailing-period chapter open, digit `╨У╨Ы╨Р╨Т╨Р N`, pypdf PDF fallback, RTF-as-`.doc` + cp1251 reverse, prose paragraph split. Summary: [`jsonl/wave_d_summary.json`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/jsonl/wave_d_summary.json). Doc: [`PDF_INGESTION_PIPELINE.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/PDF_INGESTION_PIPELINE.md) ┬з Wave D. Corpus-manifest pin rebuilt (201 sources). M─Бy─Б-tantra remains **H2377**.

### Changed
- **Corpus_builder dead VCL cleanup (H2370, Grok 4.5 `grok-4.5`).** Dropped unused `Dialogs` from [`uSort.pas`](https://github.com/gasyoun/SamudraManthanam/blob/main/Corpus_builder/PSRCBuilder/dcu/uSort.pas). Split VCL list/clipboard/RichEdit helpers out of [`TextU.pas`](https://github.com/gasyoun/SamudraManthanam/blob/main/Corpus_builder/PSRCBuilder/dcu/TextU.pas) into [`TextUVCL.pas`](https://github.com/gasyoun/SamudraManthanam/blob/main/Corpus_builder/PSRCBuilder/dcu/TextUVCL.pas) so the engine path (`uMhHTML` тЖТ `TextU`) no longer imports `CheckLst`/`StdCtrls`/`ComCtrls`/`ClipBrd`/`Windows`. Roadmap unit ticked; inventory ┬з4тАУ┬з5/┬з7 updated. Static proof (no dcc32/FPC on this host): [`docs/H2370_DEAD_VCL_STATIC_PROOF.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/H2370_DEAD_VCL_STATIC_PROOF.md).
## [0.19.4] - 2026-08-07

### Added
- **H1438 Wave C: K─Бlik─Б-pur─Бс╣Зa + Dev─лm─Бh─Бtmya (H2353, Grok 4.5 `grok-4.5`).** Both works registered in `Programdata/data.txt` with desktop HTML + JSONL. Dev─лm─Бh─Бtmya: 13 ch / 595 RU verses / **497 SA matched** (83.5%) via GRETIL M─Бrkaс╣Зс╕Нeya adhy. 81тАУ93 key-join. K─Бlik─Б-pur─Бс╣Зa: 90 ch / 8137 RU verses, `alignment: none` (no keyed SA witness). HTMLтЖТJSONL round-trip **100%** on both. Parser hardenings: OLE glued unit-ordinal peel (ch.62), colophon/absurd-jump drop, empty-verse filter. Converter: [`gretil_markp_devimahatmya_to_canonical.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/gretil_markp_devimahatmya_to_canonical.py). Doc: [`PDF_INGESTION_PIPELINE.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/PDF_INGESTION_PIPELINE.md) ┬з Wave C. Corpus-manifest pin rebuilt in the same pass (H2351).

## [0.19.3] - 2026-08-07
### Added
- **Committed corpus pin + hard corpus-gate (H2351, Grok 4.5 `grok-4.5`).** Generated and committed [`web/corpus_builder/manifest/corpus-manifest.json`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/manifest/corpus-manifest.json) (`bundle_version` 2026.08, **197** sources / **703,699** records, full SHA-256 verify). [`corpus-gate.yml`](https://github.com/gasyoun/SamudraManthanam/blob/main/.github/workflows/corpus-gate.yml) no longer only warns тАЬNOT a pinned-bundle runтАЭ: missing pin exits 1; present pin is schema-validated always and full-hash + rebuild-diff validated when checkout JSONL is present. Optional `source_file`/`metadata` blocks that would fall outside `corpus_root` (schema-illegal `..` paths) are omitted. Spec: [`docs/CORPUS_BUNDLE_SPEC.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/CORPUS_BUNDLE_SPEC.md).

### Changed
- **Wave-1 journal truth-pass (H2350, Grok 4.5 `grok-4.5`).** `.ai_state.md` Queue/WIP no longer claim H1926 тАЬin flightтАЭ or print an H1927 execute starter тАФ Lanes AтАУD are recorded as shipped (v0.16.0тАУv0.19.1); residuals point only at H2351тАУH2354. Hub GTD execute block for H1924тАУH1927 closed in the same pass.

## [0.19.2] - 2026-08-07

### Added
- **Legacy `.doc` extract front-end hardened for H1438 remainder (H2352, Grok 4.5 `grok-4.5`).** `extract_text()` prefers `antiword` (cp1251, 120 s timeout, path-bearing errors) and falls back to the OLE WordDocument UTF-16 scan via `olefile`; never returns a silent empty string. Hermetic unit tests cover the OLE path with a synthetic minimal OLE fixture; antiword/archive smokes skip when absent (CI policy: antiword optional). Doc: [`PDF_INGESTION_PIPELINE.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/PDF_INGESTION_PIPELINE.md) ┬з Legacy `.doc` extract. Dep: `olefile==0.47`. Full Wave C/D ingest remains **H2353**.

### Changed
- **Single state-migration runner (H2354, Grok 4.5 `grok-4.5`).** Canonical-reference SQL from H1925 Lane B (`canonical_state_migrations` / `canonical_ref_migrations`) is refiled as [`0004_canonical_reference_columns.sql`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/app/migrations/state/0004_canonical_reference_columns.sql) and [`0005_canonical_reference_indices.sql`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/app/migrations/state/0005_canonical_reference_indices.sql). Startup calls the D1 runner once; a one-time bridge imports any pre-absorb B ledger rows into `schema_migrations` under versions `0004`/`0005` with **current** newline-normalised file checksums (old B hashes are not carried). Dual-ledger apply path is gone; `app.canonical_state_migrations` remains as backup/restore + thin path wrappers for the backfill script. Design note: [`web/app/migrations/README.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/app/migrations/README.md).

## [0.19.1] - 2026-08-06
### Changed
- **Nirv─Бс╣Зa-tantra re-ingest after H2273 high-N fix (Grok 4.5 `grok-4.5`).** Regenerated `nirvana-tantra.jsonl` / `.raw.jsonl` / `.report.json` from a `pypdf` text-layer extract of the archive PDF: **492 тЖТ 465** verses; `id_collisions` shrinks to `["9.1"]` (debris `9.4` primary removed); ch.8 recovers addressable 9/11/12тАУ13/14 (no more `6->30` note bag); ch.13 51тЖТ74. Not `pdftotext`-byte-identical тАФ documented in [`docs/NIRVANA_TANTRA_VERSE_COUNT_DROP_H2273.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/NIRVANA_TANTRA_VERSE_COUNT_DROP_H2273.md).

### Added
- **Nirv─Бс╣Зa-tantra 821тЖТ492 verse-count drop justified (H2273, Grok 4.5 `grok-4.5`).** Chapter-by-chapter pre/post table against the printed Ignatiev PDF numbering, тЙе12 sampled absorbed chunks with debris verdicts, and a ruling on residual `id_collisions` `9.1`/`9.4`. Narrow fix: high-N footnote debris no longer becomes `prev_end` and swallows later real verses (ch.8 measured). Doc: [`docs/NIRVANA_TANTRA_VERSE_COUNT_DROP_H2273.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/NIRVANA_TANTRA_VERSE_COUNT_DROP_H2273.md).

### Fixed
- **Bс╣Ыhann─лla-tantra JSONL duplicate comment IDs** (48 identical double rows) blocked full-pin web publish; dropped dups (2533тЖТ2485 records). Rebuild corpus-manifest pin: **230** sources / **723тАп229** records. `*.jsonl text eol=lf` in `.gitattributes` so Windows pin builds match Linux publish.
- **Wave-B Ignatiev dual-run compare (H2076, Sonnet 5 `claude-sonnet-5`).** Independent Sonnet re-run of Grok's Wave-B ingest ([PR #125](https://github.com/gasyoun/SamudraManthanam/pull/125)) confirms 3/5 works byte-identical (N─лlamata, Kul─Бrс╣Зava, Yogin─л) and independently reproduces the тЙе99% round-trip claim for all 5 via `html_to_canonical.py` against the live corpus. Two works (Adbhuta-r─Бm─Бyaс╣Зa, Mah─Бbh─Бgavata-pur─Бс╣Зa) diverge under a different pandoc build on already-flagged out-of-order source verse numbering тАФ root cause is an unpinned pandoc version, not a corpus defect; the merged corpus (which explicitly logs both anomalies) is confirmed correct-or-better and kept as-is. Also fixes a doc slip (Wave-B unit test count "19" тЖТ actual 23). Full memo: [`web/corpus_builder/H2076_SONNET_WAVEB_DUAL_RUN_COMPARE.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/H2076_SONNET_WAVEB_DUAL_RUN_COMPARE.md).

## [0.19.0] - 2026-08-05
### Added
- **Durable corpus identity and the zero-orphan gate (H1925, Wave-1 Lane B, Opus 5 `claude-opus-5`).** Every retained reference moves from the ordinal pair `(source_id, line_num)` тАФ both re-assigned on every ingest, so one inserted line silently re-points every stored reference below it at the wrong verse тАФ to the canonical tuple `(source_slug, canonical_id, corpus_version)`. [`web/app/canonical_refs.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/app/canonical_refs.py) holds one dual-read resolver used by the request path, the backfill and the gate alike: canonical tuple тЖТ explicit mapping pinned to the recorded corpus version тЖТ same-version ordinal тЖТ otherwise **report, never bind**. A legacy ordinal recorded against version X is never bound in version Y without an explicit mapping, because it *would* resolve тАФ that is precisely the danger.
- **The tuple now reaches every durable-reference site.** Search results (all three modes share one SELECT), `/api/search/context`, JSON and CSV export rows, the reader's JSON-LD `Quotation` (`identifier`, no longer dropped by the segment merge), the corrections queue, and the offline packs (which already carried it). The census тАФ including the four sites whose verdict is "carries no corpus reference", asserted by test rather than assumed тАФ is [DURABLE_REFERENCE_INVENTORY.md](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/DURABLE_REFERENCE_INVENTORY.md); the additive public fields are in [SEARCH_CONTRACT.md](https://github.com/gasyoun/SamudraManthanam/blob/main/web/SEARCH_CONTRACT.md) ┬з6. All fields are additive and the legacy ordinals still resolve, so existing clients keep working.
- **Checksum-tracked, reversible state migrations** ([`canonical_state_migrations.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/app/canonical_state_migrations.py)) add the canonical columns plus `legacy_ref_map`. Ordered, idempotent, genuinely transactional (Python's `sqlite3` auto-commits DDL by default, so a half-applied migration was possible until the runner took explicit transaction control), and an edited-after-apply migration fails loudly on its recorded checksum instead of drifting. Backup/restore is exercised, not asserted.
- **Backfill checks its own pin.** [`scripts/backfill_canonical_refs.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/scripts/backfill_canonical_refs.py) may read an unversioned pre-migration ordinal as belonging to the operator-pinned corpus тАФ that is the only way such a row can ever be resolved тАФ but then verifies the pin against the text the correction itself remembers. A mis-pinned corpus surfaces as `text_mismatch` and the row stays unresolved rather than binding to a plausible wrong line.
- **Zero-orphan evidence command** ([`scripts/zero_orphan_report.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/scripts/zero_orphan_report.py)) resolves every retained reference against both the recorded and the candidate corpus and compares identity *and* content fingerprint. `identity_changed` / `orphaned` / `ambiguous` fail the gate; `content_changed` is reported but not fatal, since corrected text is the point of the project. `--rollback-rehearsal` proves the previous corpus still resolves everything.
- 45 hermetic tests, each named for the B1тАУB6 criterion it proves; full suite 750 passed, no regressions. Measured 05-08-2026 against the production corpus (`v2026.07.15`, 611,569 lines, 100% canonical-id and slug coverage, zero duplicate canonical ids) under a simulated rebuild that shifts every ordinal: **5,000/5,000 canonical-addressed references survived with identity intact while all their ordinals moved, and 5,000/5,000 ordinal-only references were refused тАФ zero silently re-bound.** Left open deliberately: the ordinals are still stored as compatibility fields pending a clean gate run over a real production rebuild, and the gate compares two built corpus DBs rather than monitoring a live one.

## [0.18.0] - 2026-08-05
### Added
- **Bounded regex and public-boundary trust тАФ Wave-1 Lane C (H1926, Opus 5 `claude-opus-5[1m]`).** Every bound on user-supplied regex now lives in one module, [`web/app/services/regex_executor.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/app/services/regex_executor.py): a 2 s hard scan deadline, the H1830 per-match timeout, caps on pattern length (512) and count (10), and **one** stable error payload тАФ `{"error", "detail"}` with no engine text, pattern echo or offsets тАФ shared by `POST /api/search`, `/export` and `/stream`. The three used to disagree (POST returned pydantic's 422 quoting the offending pattern; GET returned 400), and a *third* copy of the validation lived in [`models.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/app/models.py). This also closes the gap H1927's Lane D7 baseline reported and deliberately left for this lane: `search_service.MAX_TIME` was 5.0 s against a documented 2 s deadline, so a catastrophic regex measured 3358 ms. Without the timeout-capable `regex` package the mode is now **refused** (503 `regex_unavailable`) rather than served by unbounded `re.search` in the event loop. New contract sections: [SEARCH_CONTRACT.md ┬з3](https://github.com/gasyoun/SamudraManthanam/blob/main/web/SEARCH_CONTRACT.md) (accepted syntax, caps, deadlines, error codes) and a new [IDENTITY_TRUST_CONTRACT.md](https://github.com/gasyoun/SamudraManthanam/blob/main/web/IDENTITY_TRUST_CONTRACT.md).
- **Measured adversarial regex fixture (H1926 C1).** The textbook ReDoS shapes are **defused by the `regex` engine** тАФ `(a+)+$`, `(a*)*b`, `(x+x+)+y`, `(.*a){20}` all complete in under 4 ms at length 40, so freezing them would have produced a fixture that proves nothing while looking rigorous. Independently measured the same day as H1927's identical finding on its smoke probe. [`regex_adversarial_backtracking.json`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/tests/fixtures/regex_adversarial_backtracking.json) instead uses overlapping-alternation shapes (`(a|aa)+$`, `([ab]|[ab][ab])+$`, IAST and Cyrillic variants), each measured to exhaust the per-match budget; the same cases do not finish in 120 s under stdlib `re` at length 24. Paired with a 22-case scholarly compatibility corpus ([`regex_compat_scholarly.json`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/tests/fixtures/regex_compat_scholarly.json)) that pins documented semantics across the engine change. 43 tests in [`test_regex_bounded.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/tests/test_regex_bounded.py).
- **Verified sessions, correction trust tiers and rate limits (H1926 C4/C6/C7).** State migration [`0003_correction_trust_and_sessions.sql`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/app/migrations/state/0003_correction_trust_and_sessions.sql) adds `email_verifications`, `user_sessions`, `correction_audit` and `rate_limits`, plus `trust_tier` / `actor_ip_hash` / `contact_email` / `link_id` / `corpus_version` on `corrections`. Anonymous proposals stay open at 10/hour; a redeemed session raises the cap to 60/hour and is the **only** thing that grants attribution. Delivery of the verification token is out of scope and deliberately not faked тАФ non-production returns it, production logs it for an operator, stated as a limitation in the trust contract. 30 tests in [`test_correction_trust.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/tests/test_correction_trust.py).
### Changed
- **Admin authentication moves from `?key=` to a header (H1926 C3/C5).** `POST /api/admin/vacuum` and `GET /api/corrections/pending` accept `X-Admin-Key` or `Authorization: Bearer`, compared with `hmac.compare_digest`; **any** credential-shaped query parameter is refused with 400 *without being compared*, including the correct one тАФ by the time the application sees it, nginx and uvicorn have already logged it and browsers have it in history. No time-bounded compatibility path: the only callers were this repo's tests and the operator runbook, both updated here. A credential-scrubbing logging filter is attached to the application loggers **and the root handlers** (a logger-level filter never sees records propagated from child loggers). Operator migration in [DEPLOYMENT.md](https://github.com/gasyoun/SamudraManthanam/blob/main/DEPLOYMENT.md).
### Fixed
- **Bс╣Ыhann─лla-tantra JSONL duplicate comment IDs** (48 identical double rows) blocked full-pin web publish; dropped dups (2533тЖТ2485 records). Rebuild corpus-manifest pin: **230** sources / **723тАп229** records. `*.jsonl text eol=lf` in `.gitattributes` so Windows pin builds match Linux publish.
- **Typed email text no longer grants attribution (H1926 C6).** `POST /api/corrections/propose` resolved the `email` field of the request body against the users table and attached the matching account to the correction тАФ so typing a known scholar's address filed corrections under their name, with no verification step in the loop. The address is now stored as `contact_email` only; `user_id` comes from a redeemed session or is null. `POST /api/identity/lead` also stops returning the internal `users.id`. **Pre-existing `user_id` links written by the old lookup are not evidence of verification** and should not be read as attribution.

## [0.17.0] - 2026-08-05
### Added
- **Ordered checksum-tracked state migrations (H1927 Lane D1, Opus 5 `claude-opus-5[1m]`).** [`web/app/migrations/`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/app/migrations/README.md) replaces the inline `CREATE TABLE`/`ALTER TABLE` block that `init_state_db` re-executed on every startup. Each applied file is recorded in `schema_migrations` with a SHA-256 over its **newline-normalised** bytes тАФ normalisation is load-bearing, not cosmetic: this repo is authored on Windows and cloned on Linux CI, so a CRLF checkout would otherwise change every checksum and refuse every deployment. Two refusals are deliberate: an applied migration later edited (`MigrationChecksumError`), and a recorded migration missing from disk (`MigrationMissingError`, i.e. the DB is ahead of the code). `0001` is written entirely `IF NOT EXISTS` so an existing production `state.db` is adopted with no dump/restore, verified by a test that migrates a legacy-shaped DB with its rows intact. SQLite has no conditional `ALTER`, so `0002` uses a per-statement `-- @idempotent-error:` directive rather than a file-level `try/except` that would hide a genuine failure in any other statement.
- **corpus.db rebuild-not-migrate policy (H1927 Lane D2).** [`corpus_policy.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/app/migrations/corpus_policy.py) declares `CORPUS_SCHEMA_VERSION` and probes it at startup. It never raises and never mutates тАФ a stale corpus is served with a loud log rather than taking search down. The one pre-existing in-place shim (the slug backfill) moves to [`corpus_compat.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/app/corpus_compat.py), documented as grandfathered instead of silently tolerated.
- **One shared deployment contract for both production profiles (H1927 Lane D4).** [`deployment_contract_smoke.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/scripts/deployment_contract_smoke.py) takes only a base URL and asserts readiness, corpus-version exposure, plain search, a bounded catastrophic regex, opaque error payloads, service-worker scope, COOP on HTML, CORP on static, the reader deep-link route, sitemaps, and admin refusal of a bogus key. CI now boots the built image against fixture databases and runs it; [`deployment-contract-bare.yml`](https://github.com/gasyoun/SamudraManthanam/blob/main/.github/workflows/deployment-contract-bare.yml) runs the *same* script on a scheduled/pre-release bare profile through the repo's own `deploy/samudra.nginx`. That second profile is the point: nginx serves `/static/` directly and bypasses the `security_headers` middleware, so those headers are hand-duplicated in the vhost тАФ and the container profile cannot see them drift.
- **Categorised duplicate-suffix invariant (H1927 Lane D7).** [`dup_suffix_report.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/scripts/dup_suffix_report.py) + [docs/DUP_SUFFIX_INVARIANT_REPORT.md](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/DUP_SUFFIX_INVARIANT_REPORT.md). Gate 4 asserted a bare count ceiling; H1829 showed what that costs, with `<= 200` concealing 284 of 429 suffixed ids in a single work. A count can only ask *how many*, so a splitting bug that stays under the number is invisible to it. The gate now asserts structure тАФ every suffixed id has its un-suffixed twin, suffixes never run past `b`, segments are `sa`/`ru` pairs or commentaries, and no work exceeds 60% of the population тАФ shapes that debris has and genuine collisions do not. Measured over 675,139 records: 147 suffixed ids across 18 works, all invariants holding. The count survives only as a coarse backstop that prompts re-derivation.
- **Full-corpus gate on corpus-changing PRs and releases (H1927 Lane D5).** [`corpus-gate.yml`](https://github.com/gasyoun/SamudraManthanam/blob/main/.github/workflows/corpus-gate.yml) path-filters converters, ingest, the corpus gates and the schema policy. Ordinary CI runs `-m "not corpus"`, so until now a PR that changed a converter ran none of the checks that could tell whether it had damaged the corpus.
- **Recorded performance baselines (H1927 Lane D7).** [docs/PERFORMANCE_BASELINES.md](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/PERFORMANCE_BASELINES.md), measured by [`performance_baseline.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/scripts/performance_baseline.py) against a live deployment on the real 183-source corpus. Plain search p95 52тАУ119 ms and health p95 33 ms sit well inside budget. **Two exceptions are recorded rather than the budgets deleted:** reader lookup p95 1079 ms against a 500 ms budget (2.2├Ч), and a catastrophic regex completing in 3358 ms against the documented 2 s hard deadline (1.7├Ч) тАФ `search_service.MAX_TIME` is 5.0 s, so the implementation's whole-scan budget was never aligned to the 2 s spec. That file belongs to Lane C2 (H1926), so the finding is reported, not unilaterally patched.
### Changed
- **`web/app/main.py` 611 тЖТ 120 lines (H1927 Lane D2).** Split into `lifespan`, `http_headers`, `static_assets`, `site_context`, `corpus_compat` and the `home`/`pwa`/`seo` routers, leaving a composition root that does nothing but create the app, wire middleware and register routers. Handlers moved byte-for-byte so headers and sitemap XML cannot drift; the route table was diffed before and after and is identical; and `app.main` still re-exports every private helper the test modules import, because an import path is behaviour too.
- **CI test matrix extended to Python 3.10тАУ3.14 (H1927 Lane D3).** The Dockerfile has run `python:3.14-slim` while CI tested only 3.10тАУ3.12, so every release shipped on an interpreter no test had ever executed and nothing would have reported it. The full hermetic suite was measured passing on 3.14.4 *before* choosing to extend the matrix rather than downgrade the image. [`test_runtime_alignment.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/tests/test_runtime_alignment.py) parses the Dockerfile `FROM` against the workflow matrix so the two cannot silently re-diverge, and carries a fixture replaying the pre-fix state to prove the guard goes red there.

### Fixed
- **Bс╣Ыhann─лla-tantra JSONL duplicate comment IDs** (48 identical double rows) blocked full-pin web publish; dropped dups (2533тЖТ2485 records). Rebuild corpus-manifest pin: **230** sources / **723тАп229** records. `*.jsonl text eol=lf` in `.gitattributes` so Windows pin builds match Linux publish.
- **Two checks that would have passed without testing anything (H1927).** The deployment smoke's admin probe pointed at `/api/admin/corrections`, which does not exist тАФ it 404'd and reported PASS; it now hits the real `/api/admin/vacuum`, and a test pins the probe path to a registered route. And every regex bound was being exercised with the textbook `(a+)+$`, which this app's `regex` engine optimises away in ~1 ms; measured 05-08-2026, `(a|a)*$` is an alternation the optimiser cannot collapse and does reach the 0.05 s per-match timeout. Both call sites were switched.

## [0.16.0] - 2026-08-05
### Added
- **Canonical corpus manifest and immutable bundle contract (H1924, Wave-1 Lane A, Opus 5 `claude-opus-5`).** The enumeration of record moves from `Programdata/data.txt` тАФ a bare list of legacy HTML filenames that could say *which* sources exist but never *what they contain* тАФ to a content-addressed manifest. [`web/corpus_builder/corpus_manifest.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/corpus_manifest.py) builds, validates and diffs it against [`schema-v1.json`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/manifest/schema-v1.json) (`jsonschema` is now a real dependency precisely so the published schema is the *only* validator тАФ a hand-written twin would drift from it silently). Each source carries SHA-256, byte count, live record count and first/last canonical id of the JSONL that is actually published. **The manifest deliberately carries no wall clock:** `bundle` is a pure function of its inputs, so two builds from identical inputs are byte-identical and `content_hash` is a usable identity; event time lives in build reports instead, and a test asserts no clock-shaped key ever reappears. `content_hash` covers `bundle` only, so the same content rebuilt at a new git revision keeps one identity.
- **Publication now validates the bytes it publishes.** [`ingest/publish.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/ingest/publish.py) `--manifest` opens and hashes every canonical JSONL the manifest names, and [`ingest/ingest.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/ingest/ingest.py) re-verifies each hash before inserting a row and rejects a manifest whose declared record count disagrees with what it inserted. A one-character edit inside a JSONL string тАФ valid JSON, unchanged record count, so only a hash can catch it тАФ now aborts publish, while the legacy `validate_corpus` tree check still passes it: that gap is asserted in the suite rather than assumed. Ingest writes `input_manifest_hash`/`bundle_version` into `corpus_meta` and `corpus_version` becomes the bundle version, not a build date. The manifest-less path survives behind an explicit warning that it does not hash what it publishes.
- **Every generated view names its input bundle.** New [`build_report.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/build_report.py) ties each derivative to one manifest hash; the web DB (from the manifest it published), the offline packs (inherited via `corpus.db`'s `corpus_meta`, and re-recorded in `pack_meta`) and the desktop HTML plus its `.no_tags` sidecars (from `--manifest`) all now emit one. A generator whose source DB carries no `input_manifest_hash` is **refused** rather than given a placeholder тАФ a derivative of an unregistered corpus must not fabricate a lineage.
- **Checksum-pinned, vendor-neutral artifact resolution.** [`ingest/artifact_resolver.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/ingest/artifact_resolver.py) stages a download, hashes it there, and moves it into place only on a match тАФ nothing extracts or opens an unverified file, and `extract_verified` takes a verified artifact rather than a path so the check cannot be bypassed. `file://`, bare paths and `http(s)://` share one `Transport` interface (no vendor SDK), a cached copy is re-hashed rather than trusted, and every URL in a log line or exception passes through `redact_url` тАФ object stores authenticate with pre-signed query strings, so an un-redacted URL in a build log is a leaked credential.
- **Rollback is now a rehearsed path, not a hope.** `restore_backup()` re-activates a previous bundle from the copy publish records, refusing a backup that fails its own integrity check, and a failed candidate publication is proven to leave the live corpus byte-identical.
- 59 hermetic tests ([`test_corpus_manifest.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/tests/test_corpus_manifest.py), [`test_artifact_resolver.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/tests/test_artifact_resolver.py)), each named for the A1тАУA7 criterion it proves; the HTTP transport is tested against a real loopback server because a mocked socket cannot show a transport that streams to disk without hashing. Full suite 705 passed, no regressions; CI green on Python 3.10/3.11/3.12, ruff, black and the Docker image (the one red job, `npm audit`, is a pre-existing advisory that failed identically on the preceding main commit). Measured on the real JSONL directory: 197 sources / 703,726 records, two builds byte-identical, full-hash validation 3.1 s. That run also caught a real defect тАФ the fallback enumerator would have pulled 22 converter intermediates (`*.raw.jsonl`) into a bundle as sources; they are now excluded **and named on every build**, since a bundle that silently drops or absorbs a file is the failure the manifest exists to prevent. Spec + stated limits: [CORPUS_BUNDLE_SPEC.md](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/CORPUS_BUNDLE_SPEC.md).

## [0.15.3] - 2026-08-04
### Changed
- **Corpus Builder: `TMhHTMLBuilder` cut free of VCL/GUI (H1485, Opus 5 `claude-opus-5[1m]`).** [`uMhHTML.pas`](https://github.com/gasyoun/SamudraManthanam/blob/main/Corpus_builder/PSRCBuilder/uMhHTML.pas)'s implementation `uses` drops to `SysUtils, textu, windows, MyUtils` тАФ `dialogs`, `fMainForm`, `Forms`, `controls` and `ShellApi` are gone, and with them the `uMhHTML тЖТ fMainForm` reverse edge the H2064 inventory measured. Every VCL call site is replaced by a nil-safe sink the host assigns after `Create`: `Form1.StatusBar1` writes (├Ч5, panel index preserved тАФ including the one `Panels[1]` site) тЖТ `Progress(APanel, AText)`, `MessageDlg` тЖТ `Confirm`, `ShowMessage` (├Ч3) тЖТ `ReportError`, which appends to `ErrList` unconditionally тАФ so the standing `CLAUDE.md` rule "`ErrList` is the sole error channel, never `ShowMessage` in builder logic" now holds by construction rather than by convention. `ShellExecute` of `Err.txt` moves to the caller via new `HasErrors` / `ErrFileFullPath`; [`fMainForm.pas`](https://github.com/gasyoun/SamudraManthanam/blob/main/Corpus_builder/PSRCBuilder/fMainForm.pas) implements the three sinks and wires them at all three construction sites, preserving the ordering relative to `RenameErrFile`. Two intentional host-side deltas: progress now refreshes *and* pumps messages at every site (the engine used to do one or the other), and a load error no longer halts a multi-book batch on a modal тАФ it lands in `Memo1`, `ErrList` and `Err.txt`. **Not compiled:** no Delphi 7 machine in the session, so `dcc32` never ran; the source-level verification and the human residual are written up in [Corpus_builder/DEPENDENCY_INVENTORY.md](https://github.com/gasyoun/SamudraManthanam/blob/main/Corpus_builder/DEPENDENCY_INVENTORY.md) ┬з3a. Ticks [Corpus_builder/ROADMAP.md](https://github.com/gasyoun/SamudraManthanam/blob/main/Corpus_builder/ROADMAP.md) Phase 1 ┬л╨Ю╤В╨┤╨╡╨╗╨╕╤В╤М ╨┤╨▓╨╕╨╢╨╛╨║ ╨╛╤В ╤Д╨╛╤А╨╝╤Л┬╗; the dead-VCL-import cleanup in `uSort`/`TextU` is explicitly still open.

## [0.15.1] - 2026-08-04
### Added
- **Annotates-remap provenance for the H1828 orphan fix (H2219, Opus 5 `claude-opus-5[1m]`, dual-run compare of the Grok 4.5 override).** H1828 removed every gate-5 dead anchor by re-pointing an endnote at the *nearest emitted verse* and rewriting the record id with it тАФ destroying the target the endnote actually named, with no flag separating a genuine anchor from a heuristic one. Measured on shipped data, both readings occur: `6.5.559 тЖТ 6.005.059` is an OCR-digit repair the remap gets right, while `12.8.111 тЖТ 12.008.092` moves a note 19 verses with nothing behind it; gate 5 reported zero orphans for both. Commentary records now carry `annotates_resolution` (`exact`/`nearest`) plus `annotates_requested` when the anchor moved, and the conversion report gains `annotates_remapped` / `annotates_remap_max_delta` / a per-remap list. New corpus gate 5b asserts a moved anchor never loses its requested target; the gate-5 `chinachara-tantra` exemption is narrowed from a blanket work-level skip to a count-bounded budget (1), so a *second* orphan there fails again. The shipped JSONL predates the fields and needs regeneration from the off-git source PDFs.
- **Regex match-timeout observability (H2219, follow-on to H1830).** `search_regex` now reports `match_timeouts` / `match_errors` / `regex_timeout_engine` in `search_metadata` and marks the result `truncated` when rows were abandoned mid-match тАФ previously a swallowed catastrophic-backtracking timeout silently under-reported matches while the metadata still read clean. Import falls back to stdlib `re` only with a loud `logging.warning`, so a deployment missing the `regex` package can no longer serve an unprotected `mode=regex` in silence.
- **Corpus Builder Phase 1 dependency inventory (H2064, Grok 4.5 `grok-4.5`).** Full `uses` graph from `PSRCBuilder/cb.dpr`: every local unit is reachable (no dead modules); VCL/WinAPI vs RTL classification; concrete proof that `uMhHTML` / `TMhHTMLBuilder` is **not** GUI-free today (`Form1.StatusBar1`, `ShowMessage`, `MessageDlg`, `ShellExecute`, `Application.ProcessMessages`). Portable core named (`myutils`/`uTypes`/`ArtMath`/`CalcSimU`/`StatProcs`/`uSort`). Builder `TextU.pas` ~3├Ч larger than main-app `Units/TextU.pas` тАФ Phase 2 must re-diff, not assume subset. Artifact: [Corpus_builder/DEPENDENCY_INVENTORY.md](https://github.com/gasyoun/SamudraManthanam/blob/main/Corpus_builder/DEPENDENCY_INVENTORY.md). Tick: [Corpus_builder/ROADMAP.md](https://github.com/gasyoun/SamudraManthanam/blob/main/Corpus_builder/ROADMAP.md) Phase 1 inventory. Feeds H1485 (engineтЖФGUI decouple).
- **Ignatiev Wave B ingest: 5 docx/doc tantras + upapur─Бс╣Зas (H1438, Grok 4.5
  override dual-run).** N─лlamata-pur─Бс╣Зa (1 ch / 410 v, partial ┼Ыl. 1тАУ411),
  Adbhuta-r─Бm─Бyaс╣Зa (6 selected ch / 308 v), Kul─Бrс╣Зava-tantra (17 ch / 2049 v +
  1113 endnotes), Yogin─л-tantra (19 ch / 1285 v + 340 endnotes; ch.8тАУ19 via
  OLE WordDocument UTF-16 extract of legacy `.doc`), Mah─Бbh─Бgavata-pur─Бс╣Зa
  (78 ch / 4232 v; source lacks ch.36тАУ37 and 56 headings). All registered in
  `Programdata/data.txt`, all ru_only-aligned (no Sanskrit e-text for these),
  all HTML round-trip тЙе99% (measured 100%┬▒0.1). Parser hardening this wave:
  ToC leader-dot reject; per-part multi-file parse so part-1 endnotes cannot
  leak; last-chapter ALL-CAPS title no longer mistaken for back-matter
  (which had emptied Kul─Бrс╣Зava ch.8/17 and Mah─Бbh─Бgavata ch.35/81). Three new
  regression tests (19 total in `test_ignatiev_book_units.py`). M─Бy─Б-tantra
  and Waves CтАУD remain open. Dual-run residual for intended Sonnet tier
  minted at close.


## [0.15.0] - 2026-07-31
### Added
- **Regression guard for Cyrillic homoglyphs in `#sa` corpus fields (H1694, issue #16, Sonnet 5
  `claude-sonnet-5`).** The 5 words / 21 field-occurrences named in #16 were already fixed on `main`
  (PR #46, 12-07-2026) via `web/corpus_builder/scan_cyrillic_homoglyphs.py`; this session re-verified the
  corpus jsonl is clean (`saс╣Гcukoca`, `cal─Бgramukuс╣нapr─Бс╣Г┼Ыu┼Ы`, `cekс╣гv─Бkuvaс╣Г┼Ыasya`, `ch─лlav─Бn`,
  `tad-vip─Бka-anuguс╣З─Бn─Бm` all round-trip to their Latin-IAST form, no Cyrillic remains in any `#sa`
  segment) and added `web/tests/test_cyrillic_homoglyphs.py` тАФ a hermetic pytest guard (imports the
  existing scanner, no `corpus.db` needed) so a future re-ingest can't silently reintroduce the leak.
  Russian-field mixed script (e.g. Vasmer `*Dunaj╤М`) is untouched by design тАФ the scanner is
  script-tag-gated to `#sa` only.
- **KSS book 12тАУ14 low-confidence alignment groups re-verified with quoted evidence (H1687, Sonnet 5
  `claude-sonnet-5`).** The H927 review sheet's 70 low-confidence (<0.6) SAтЖФRU alignment groups were
  re-derived directly from `web/corpus_builder/jsonl/kathasaritsagara-12.jsonl`/`-14.jsonl` (the original
  sheet HTML had been lost тАФ gitignored `/review/`, its worktree removed before copy-out тАФ but the
  underlying jsonl counts matched exactly: 62+8=70) and each group now carries an agent verdict
  (`alignment-holds`/`confirmed-break`/`uncertain`) with quoted SA/RU evidence, committed as
  `web/corpus_builder/jsonl/kathasaritsagara-12-14_lowconf_agent-verdicts.json`. Result diverges sharply
  from H927's prior note ("mostly granularity mismatches, not mis-alignment"): **27 alignment-holds ┬╖ 40
  confirmed-break ┬╖ 3 uncertain** тАФ several real off-by-one/displacement clusters found (a Russian
  passage's true translation turns up verbatim in a *neighboring* group instead of its own paired
  Sanskrit line). Human vote reduced to the 43 confirmed-break+uncertain rows only, in
  `web/corpus_builder/jsonl/kathasaritsagara-12-14_lowconf_reduced-human-ask.json`. No alignment jsonl
  file was changed by this pass тАФ re-alignment fixes are applied only after the human vote (per H1687 DoD).

### Removed
- **Dead `morph_cache` table dropped from `corpus.db` schema (H1503, Sonnet 5
  `claude-sonnet-5`).** `web/app/db.py::create_schema` no longer creates
  `morph_cache` тАФ it was migrated to `state.db` in Track B (v1.9.1) and had
  been re-created empty on every fresh `corpus.db` since. `create_schema` now
  runs an idempotent `DROP TABLE IF EXISTS morph_cache` so existing DB files
  get the leftover table dropped on next startup. +2 hermetic tests
  (`web/tests/test_db_schema.py`).

### Added
- **Structured JSON/CSV export for search results (H1502, Sonnet 5 `claude-sonnet-5`).**
  `GET /api/search/export` now accepts `format=json` and `format=csv` alongside the
  existing HTML default, reusing the same `dispatch_search` result set and metadata
  block (`query`, `mode`, `corpus_version`, `timestamp`, `source_filter`,
  `live_search_url`) already rendered into the HTML export. JSON returns
  `{metadata, results}` with the full result fields (`source_id`, `source_title`,
  `chapter`, `line_num`, `link_id`, `line_html`, `line_text`); CSV writes the same
  metadata as `# key,value` comment rows followed by a data table. +4 tests; existing
  HTML export and its tests unaffected.
- **Residual replan pack (stale-roadmap `/ask-batch`, Grok 4.5 `grok-4.5`, 26-07-2026):** living status [docs/ROADMAP_SAMUDRAMANTHANAM_RESIDUAL_2026H2.md](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/ROADMAP_SAMUDRAMANTHANAM_RESIDUAL_2026H2.md) + unattended [docs/PLAN_SAMUDRAMANTHANAM_RESIDUAL_2026H2.md](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/PLAN_SAMUDRAMANTHANAM_RESIDUAL_2026H2.md) with ARCHITECTURE / IMPLEMENTATION / VERIFICATION / `.meta.md`. Supersede banners on H2 mobile roadmap, Somadeva scale-up roadmap, and ARCHITECTURE_REVIEW_6_MONTH. Wave-1 spine: H1502/H1503 + integrity (DBhP IDs, #16) + SSE tests; H1438 parallel; H1485 wave-2.

## [0.14.0] - 2026-07-25
### Added
- **Shared inline `<w><ana/>` scheme for both corpus sides тАФ the last H905/H906
  item (Opus 5 `claude-opus-5[1m]`).** `nkrya_export.py --inline-ana` folds the
  morphology *into* the para-XML as ╨Э╨Ъ╨а╨п `<w><ana lex= gr= gramset=/>` per token,
  instead of only alongside it as a TSV. Both handoffs had deferred this so
  neither side would fix the attribute scheme unilaterally; the agreement is one
  element shape with two honest tagsets (`opencorpora` for RU via pymorphy3,
  `dcs-ud` for SA via DCS gold тАФ they do not map 1-to-1, and merging them would
  have silently corrupted the grammar). The annotated unit is the **surface
  word**: `<se>` text is never rewritten or re-segmented, and concatenating the
  `<w>` content reproduces the segment byte-for-byte (test-enforced). A word may
  carry several `<ana>` children тАФ the RNC ambiguity construct, reused for the
  sandhi-split compound (`tapaс╕еsv─Бdhy─Бyanirataс╣Г` = one word, three DCS tokens).
  **RU coverage 100 %** of pairs. **SA coverage 15.5 %** of gold-bearing verses
  (37.6 % / 34.9 % on the analytically-printed GRETIL k─Бс╣Зс╕Нas, ~1 % on the
  bilingual editions that write long unresolved compounds) тАФ H905 had called this
  step "small, mechanical", but DCS is sandhi-*split*: it holds more tokens than
  surface words in ~89 % of verses and its gold does not re-concatenate to the
  surface, because sandhi is undone. So the SA side attaches gold only where a
  sandhi-tolerant matcher accounts for the verse end-to-end, and emits plain text
  otherwise тАФ never a guessed analysis, following the rule `align_sanskrit.py`
  already sets. Precision was not traded for coverage: on the 18,228 annotated
  Yuddhak─Бс╣Зс╕Нa words an initial-consonant gate found **0 disagreements**. The
  `sa_morph.tsv` sidecar still carries 100 % of the gold. +6 tests (23 pass);
  two runs byte-identical. Full write-up:
  [`web/corpus_builder/INLINE_ANA_H906_REPORT.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/INLINE_ANA_H906_REPORT.md).

## [0.13.0] - 2026-07-25
### Fixed
- **Bс╣Ыhann─лla-tantra JSONL duplicate comment IDs** (48 identical double rows) blocked full-pin web publish; dropped dups (2533тЖТ2485 records). Rebuild corpus-manifest pin: **230** sources / **723тАп229** records. `*.jsonl text eol=lf` in `.gitattributes` so Windows pin builds match Linux publish.
- **SA morphology no longer keyed off bilingual pairs тАФ unlocks 7,123 R─Бm─Бyaс╣Зa
  verses of DCS gold (H906, Opus 5 `claude-opus-5[1m]`).** The `--sa-morph` and
  `--vidyut-diff` layers iterated `classify()`'s `pairs`, which by design require
  **both** a Sanskrit and a Russian side. The GRETIL-ingested
  `06_ramayana-yuddhakanda` and `07_ramayana-uttarakanda` are **Sanskrit-only**
  (untranslated), so they produced zero pairs and wrote header-only morphology
  files тАФ recorded in the build report as "0 % DCS coverage; the ref mapper
  doesn't parse their passage convention". That diagnosis was wrong: their
  passages are plain `N.N`, `dcs_target()` mapped them correctly all along, and
  at the passage level they align to DCS at **100.0 %** and **99.9 %** тАФ the best
  figures in the whole R─Бm─Бyaс╣Зa. A new `sa_units()` builder (every group with a
  non-empty Sanskrit side, translated or not) now feeds the SA-side layers, while
  `classify()`/`pairs` keep driving the genuinely bilingual para-XML/TMX/TSV/RU
  outputs. Net **+7,123 covered verses and +98,753 gold tokens**; R─Бm─Бyaс╣Зa gold
  coverage 8,193 тЖТ 15,316 verses (**+87 %**). Purely additive тАФ every
  previously-covered source re-measures byte-identical. +4 tests (17 pass).
- **R─Бm─Бyaс╣Зa "verse-number offset" diagnosis corrected тАФ there is no offset
  (H906, Opus 5 `claude-opus-5[1m]`).** The build report attributed the 62тАУ80 %
  R─Бm─Бyaс╣Зa coverage to verse-numbering divergence ("the misses are alignment, not
  missing DCS data"). Categorising every chapter/verse of the four bilingual
  k─Бс╣Зс╕Нas shows the opposite: the dominant miss is **3,696 verses our edition
  carries that DCS never annotated**, and of the 1,422 verses DCS holds that we
  don't match, **98.7 % lie beyond our last verse in that chapter** (DCS's
  chapter simply runs longer) with only **19 in total** a genuine in-range hole.
  The verse map is already correct and at its ceiling; the 62тАУ80 % is DCS's own
  annotation density and recension, and is now reported as such. Full evidence:
  [`web/corpus_builder/RAMAYANA_VERSE_MAP_H906_REPORT.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/RAMAYANA_VERSE_MAP_H906_REPORT.md).

### Added
- **vidyut second-opinion layer + agreement diff against the DCS gold (H906,
  Opus 4.8 `claude-opus-4-8[1m]`).**
  [`web/corpus_builder/vidyut_diff.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/vidyut_diff.py)
  runs vidyut 0.4.0's `cheda.Chedaka` over each `seg=sa` group's SLP1 surface and
  pairs its tokens against the DCS gold tokens of the same group, emitting
  `<slug>.vidyut_diff.tsv` behind `nkrya_export.py --vidyut-diff` (one row per
  matched / dcs-only / vidyut-only token, tri-state agree flag per feature) plus a
  `vidyut_diff` aggregate block in `export_report.json`. The join is a group-level
  multiset match on the sandhi-folded SLP1 form (`M`тЖТ`m`, `H`тЖТ`s`), which buys a
  measured **+14 pp** form-match (35 %тЖТ49 %) because DCS keeps the printed surface
  (`evaM`, `pArTAH`) where vidyut returns the underlying pada form (`evam`,
  `pArTAs`); both sides are mapped into the DCS feature vocabulary so the
  comparison is like-for-like. **Headline result on ─Аraс╣Зyakaparva** (2033 pairs,
  152,196 gold tokens): form-match **49.2 %**, and over the matched tokens
  lemma 69.3 % ┬╖ coarse POS 69.3 % ┬╖ case 70.5 % ┬╖ gender 73.7 % ┬╖ number 90.4 %.
  The 49 % is a property of vidyut, not a bug in the diff тАФ its unsupervised
  segmenter picks different token boundaries from DCS on roughly half of this
  compound-heavy epic text (`dy┼лtajit─Бс╕е` тЖТ `dyU┬╖ut┬╖ajitAs`), and feeding it
  danda-delimited hemistichs instead of whole groups moved this by <0.1 pp. This
  **vindicates the DCS-is-gold ordering**: on epic register vidyut is not close
  enough to arbitrate, but on the half it segments identically it is a useful
  independent check. Categorised disagreement sample (Nom/Acc/Voc syncretism,
  vidyut's masculine over-assignment, its subanta-fallback NOUN labelling, and
  the pronoun-lemma split) in
  [`web/corpus_builder/VIDYUT_DIFF_H906_REPORT.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/VIDYUT_DIFF_H906_REPORT.md).
  Deterministic; the vidyut data pack (`$VIDYUT_DATA`) is a large local-only
  fetch and the layer degrades to empty when absent, never guessed тАФ same
  contract as the DCS sqlite. +5 tests (14 pass, 2 data-pack-gated skips).

## [0.12.0] - 2026-07-22
### Added
- **Ignatiev Wave-A-tail ingest: 4/4 remaining PDF tantras (H1438, Sonnet 5
  `claude-sonnet-5`).** Niruttara-tantra (15 ch, 674 verses), Guptas─Бdhana-tantra
  (12 ch, 319 verses) and Yoni-tantra (8 ch, 221 verses) ingested via the
  generalized `ignatiev_book_to_canonical.py`, all registered in
  `Programdata/data.txt`, all FTS5-searchable, all round-trip
  `html_to_canonical.py`-verified at 100% verse reproduction. Three real parser
  bugs found and fixed along the way (each with its own regression test, 6 new
  tests, 16 total): a chapter heading glued to its own first body sentence with
  no paragraph break (Niruttara ch.5); an ALL-CAPS running section title glued
  onto the FRONT of a chapter heading, which also exposed a latent
  case-sensitivity bug (`re.IGNORECASE` made the "ALL-CAPS" class match
  lowercase too, letting a table-of-contents line masquerade as a heading and
  corrupt Niruttara's own chapter numbering тАФ fixed with scoped `(?-i:...)`
  groups); and an appendix's own later "╨Ъ╨╛╨╝╨╝╨╡╨╜╤В╨░╤А╨╕╨╣" section (for its own
  quoted-hymn citations) being mistaken for Yoni-tantra's real endnotes,
  dragging its chapter-8 body 140+ lines past the true boundary. Full writeups:
  `web/corpus_builder/PDF_INGESTION_PIPELINE.md` ┬зSingle-book generalization.
  **M─Бy─Б-tantra deliberately deferred** тАФ a different, larger front-end gap
  (per-page glued-digit footnotes, not the bracket-style `[N]` convention) that
  needs a real design extension, not a regex tweak; see the pipeline doc and
  `.ai_state.md` for the diagnosis. Remaining ~14 works (Waves BтАУD) stay scoped
  in [H1438](https://github.com/gasyoun/Uprava/blob/main/handoffs/H1438-Sonnet_SamudraManthanam_ignatjev-tantras-puranas-ingest_22.07.26.md).
- **Generalized single-book Ignatiev converter + 2-work proof (H1438, Sonnet 5
  `claude-sonnet-5`).**
  [`web/corpus_builder/ignatiev_book_to_canonical.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/ignatiev_book_to_canonical.py)
  generalizes the DBhP-shaped `ignatjev_pdf_to_canonical.py` pipeline
  (H534/H558) to ╨Р. ╨Ш╨│╨╜╨░╤В╤М╨╡╨▓'s ~20 other tantra/upapur─Бс╣Зa translations тАФ
  standalone single-book works (flat `chapter.verse` ids, heading-only
  chapter splitting, bracket-style `[N]` Word-footnote endnotes) sourced as
  a single `.docx` (pandoc) or `.pdf` (pdftotext), not DBhP's 6-volume set.
  Rights cleared for "all my works ... whether published or unpublished" тАФ
  [RIGHTS_GRANT_IGNATJEV_DBHP_2026H2.md](https://github.com/gasyoun/Uprava/blob/main/RIGHTS_GRANT_IGNATJEV_DBHP_2026H2.md).
  Proved on 2 works as the H1438 pilot: C─лn─Бc─Бra-tantra (docx, 5 ch, 225
  verses, 154 endnotes) and Nirv─Бс╣Зa-tantra (PDF, 15 ch, 821 verses), both
  registered in `Programdata/data.txt` and browser-verified searchable via
  FTS5. 10 hermetic unit tests
  ([`web/tests/test_ignatiev_book_units.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/tests/test_ignatiev_book_units.py)).
  Remaining ~18 works scoped as a wave-ordered backlog in
  [H1438](https://github.com/gasyoun/Uprava/blob/main/handoffs/H1438-Sonnet_SamudraManthanam_ignatjev-tantras-puranas-ingest_22.07.26.md)
  and `PDF_INGESTION_PIPELINE.md` ┬зSingle-book generalization.
- **Re-implement╨░╤Ж╨╕╤П ╤Б╨║╨╗╨╛╨╜╨╡╨╜╨╕╤П ╤А╤Г╨▒╤А╨╕╨║ ╤Г╨║╨░╨╖╨░╤В╨╡╨╗╤П ╨▓ ╨┐╨╛╤А╤В╤Г тАФ ╨│╨╡╨╜╨╡╤А╨░╤В╨╛╤А ╨▓╨╝╨╡╤Б╤В╨╛
  ╤Б╤В╨░╤В╨╕╤З╨╡╤Б╨║╨╛╨│╨╛ ╨╕╨╝╨┐╨╛╤А╤В╨░ (H1207, Sonnet 5 `claude-sonnet-5`).**
  [`web/corpus_builder/sanskritisms/ru_rubric_decline.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/sanskritisms/ru_rubric_decline.py) тАФ
  reproduce+fix ╨┤╨╗╤П [`rus_index_declined.txt`](https://github.com/gasyoun/SamudraManthanam/blob/main/nkrya-parallel/diplom-rubanova/rus_index_declined.txt)
  (292 ╤А╤Г╨▒╤А╨╕╨║╨╕), ╨╖╨░╨║╤А╤Л╨▓╨░╨╡╤В H1204-╤Б╤В╨░╤В╤Г╤Б-╨┤╨╛╨║╤Г╨╝╨╡╨╜╤В. `Index_items_declension.ipynb`
  + `index_lone_declined_manual.json` + `pyphrasy` ╨╜╨╡ ╨╜╨░╨╣╨┤╨╡╨╜╤Л ╨╜╨╕ ╨▓ ╤Н╤В╨╛╨╝ ╤А╨╡╨┐╨╛, ╨╜╨╕
  ╨▓╤Л╤И╨╡ ╨┐╨╛ ╨┐╨╛╤В╨╛╨║╤Г ╨▓ `github.com/evgeniarubanova/sanskrit_stemmer` (╨┐╨╛╨╗╨╜╨╛╨╡ ╨┤╨╡╤А╨╡╨▓╨╛
  ╨╕╨╖ ╤В╨╡╤Е ╨╢╨╡ 18 ╨┐╨╗╨╛╤Б╨║╨╕╤Е ╤Д╨░╨╣╨╗╨╛╨▓, ╨▒╨╡╨╖ ╨╜╨╛╤Г╤В╨▒╤Г╨║╨░ ╨╕ ╨▒╨╡╨╖ ╨╝╨░╨╜╤Г╨╗╤М╨╜╨╛╨│╨╛ gold) тАФ ╨╝╨╡╤В╨╛╨┤
  ╨┐╨╡╤А╨╡╨╕╨╖╨╛╨▒╤А╨╡╤В╤С╨╜ ╨╕╨╖ `rus_index.txt` + ╨╜╨░╨▒╨╗╤О╨┤╨░╨╡╨╝╤Л╤Е ╨┤╨╡╤Д╨╡╨║╤В╨╛╨▓ ╤Б╤В╨░╤А╨╛╨│╨╛ ╤Д╨░╨╣╨╗╨░:
  ╤З╨╕╤Б╨╗╨╕╤В╨╡╨╗╤М╨╜╨╛╨╡ ╤Б╨╛╨│╨╗╨░╤Б╨╛╨▓╨░╨╜╨╕╨╡ (╨┤╨▓╨░/╤В╤А╨╕/╤З╨╡╤В╤Л╤А╨╡ тЖТ gen.sg ╨▓ ╨╕╨╝./╨▓╨╕╨╜., ╨┐╤П╤В╤М+ тЖТ gen.pl,
  ╨▓╨╛ ╨▓╤Б╨╡╤Е ╨╛╤Б╤В╨░╨╗╤М╨╜╤Л╤Е ╨┐╨░╨┤╨╡╨╢╨░╤Е тАФ plural ╤Д╨╛╤А╨╝╤Л), ╨╛╨▒╤Й╨╕╨╣ per-word ╨┤╨╡╨║╨╗╨╡╨╜╨░╤В╨╛╤А ╤Б
  ╨┐╤А╨╡╨┤╨┐╨╛╤З╤В╨╡╨╜╨╕╨╡╨╝ ADJF/PRTF ╨┐╤А╨╕ ╨╖╨░╨▓╤П╨╖╨░╨╜╨╜╨╛╨╝ ╤Б╨║╨╛╤А╨╡ (╤З╨╕╨╜╨╕╤В ┬л╨▓╨╡╨╖╨┤╨╡╤Б╤Г╤Й╨╕╤П┬╗тЖТ┬л╨▓╨╡╨╖╨┤╨╡╤Б╤Г╤Й╨╕╨╣┬╗),
  ╤Д╨╕╨║╤Б╨░╤Ж╨╕╤П ╤Г╨╢╨╡-╨║╨╛╤Б╨▓╨╡╨╜╨╜╤Л╤Е ╤Е╨▓╨╛╤Б╤В╨╛╨▓ (┬л╤Б╤Л╨╜ ╨┤╤Е╨░╤А╨╝╤Л┬╗, ╨┐╤А╨╡╨┤╨╗╨╛╨╢╨╜╤Л╨╡ ╨┤╨╛╨┐╨╛╨╗╨╜╨╡╨╜╨╕╤П), ╨║╨╗╨░╤Б╤Б
  ┬л╤В╨╛╤В, тАж┬╗ ╨┤╨╗╤П ╨╛╤В╨╜╨╛╤Б╨╕╤В╨╡╨╗╤М╨╜╤Л╤Е ╨┐╤А╨╕╨┤╨░╤В╨╛╤З╨╜╤Л╤Е (╨▒╤Л╨╗╨╕ ╨┐╤Г╤Б╤В╤Л╨╝╨╕ ╨▓ ╤Б╤В╨░╤А╨╛╨╝ ╤Д╨░╨╣╨╗╨╡ тАФ 7 ╤А╤Г╨▒╤А╨╕╨║),
  ╤Б╨┐╨╕╤Б╨╛╨║ ╨╕╨╖ 9 ╤Е╤Н╨╜╨┤╨╗d homograph-╨╗╨╛╨▓╤Г╤И╨╡╨║ (╨│╨░╨┤╤Л/╨┤╤А╨╛╨╜╤Л/╨╗╤Г╨║╨░/╨│╨░╨╜╨│╨╕/╨╝╨░╨╜╨░╤Б╤Л/╨┐╨░╨║╨╕/╨▒╨░╨╗╤Л/
  ╨╖╨╜╨░╨║/╨╕╨╜╨┤╤А╨░/╨┐╨░╤Б╤В╤М тАФ ╨│╨┤╨╡ pymorphy3 ╨╛╨┤╨╜╨╛╨╖╨╜╨░╤З╨╜╨╛ ╨▓╤Л╨▒╨╕╤А╨░╨╡╤В ╨╜╨╡ ╤В╤Г ╨╗╨╡╨╝╨╝╤Г). ╨Я╤А╨░╨▓╨╕╤В
  ┬л╤В╤А╨╕ ╨╝╨╕╤А╨░┬╗тЖТ┬л╤В╤А╨╕ ╨╝╨╕╤А┬╗ ╨╕ ┬л╨▓╨╡╨╖╨┤╨╡╤Б╤Г╤Й╨╕╤П┬╗, ╨┐╨╗╤О╤Б truncation-╨▒╨░╨│ ╤Б╤В╨░╤А╨╛╨│╨╛ `both`-╨║╨╗╨░╤Б╤Б╨░
  (╤В╨╡╤А╤П╨╗ 3-╨╡+ ╤Б╨╗╨╛╨▓╨╛ ╤Д╤А╨░╨╖╤Л тАФ ┬л╨▓╨╗╨░╨┤╤Л╨║╨░ ╤А╤Л╨╢╨╕╤Е┬╗ ╨▓╨╝╨╡╤Б╤В╨╛ ┬л╨▓╨╗╨░╨┤╤Л╨║╨░ ╤А╤Л╨╢╨╕╤Е ╨║╨╛╨╜╨╡╨╣┬╗, 15+
  ╤А╤Г╨▒╤А╨╕╨║) ╨╕ ╨┐╨╛╨╗╨╜╨╛╤Б╤В╤М╤О ╨┐╤Г╤Б╤В╤Л╨╡ ╤Д╨╛╤А╨╝╤Л ╤Г 11 ╤А╤Г╨▒╤А╨╕╨║ (comma-list-╨┐╨╡╤А╨╡╤Б╤В╨░╨╜╨╛╨▓╨║╨╕ +
  ┬л╤В╨╛╤В, тАж┬╗-╨║╨╗╨░╤Б╤Б). ╨а╤Г╤З╨╜╨╛╨╣ gold тАФ
  [`rus_index_declined_manual_gold.json`](https://github.com/gasyoun/SamudraManthanam/blob/main/nkrya-parallel/diplom-rubanova/rus_index_declined_manual_gold.json)
  (104 ╤А╤Г╨▒╤А╨╕╨║╨╕, ╨╜╨╡╨╖╨░╨▓╨╕╤Б╨╕╨╝╨╛ ╨▓╤Л╨▓╨╡╨┤╨╡╨╜╨╜╤Л╨╡ ╨┐╨╛ ╨┐╤А╨░╨▓╨╕╨╗╨░╨╝ ╨│╤А╨░╨╝╨╝╨░╤В╨╕╨║╨╕): **paradigm
  accuracy 100 % (╨▒╤Л╨╗╨╛ 86.5 % ╨▓ ╨╖╨░╨╝╨╡╤В╨║╨╡ 2024-11)**. ╨в╨╡╤Б╤В╤Л:
  [`web/tests/test_ru_rubric_decline.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/tests/test_ru_rubric_decline.py) тАФ
  26 hermetic + 2 `-m corpus` (parity: ╤А╨╡╨│╨╡╨╜╨╡╤А╨░╤Ж╨╕╤П == ╨╖╨░╨║╨╛╨╝╨╝╨╕╤З╨╡╨╜╨╜╤Л╨╣ ╤Д╨░╨╣╨╗;
  accuracy-gate тЙе86.5 %); ╤Б╤Г╤Й╨╡╤Б╤В╨▓╤Г╤О╤Й╨╕╨╡ sanskritisms corpus-╤В╨╡╤Б╤В╤Л (╤Н╨┐╨╕╤В╨╡╤В-╤Б╨╗╨╛╨╣
  ╨▓╤Б╤С ╨╡╤Й╤С ╨╜╨░╤Е╨╛╨┤╨╕╤В ╨╕╨╖╨▓╨╡╤Б╤В╨╜╤Л╨╡ ╨╕╨╝╨╡╨╜╨░) ╨┐╤А╨╛╨│╨╜╨░╨╜╤Л ╨╖╨░╨╜╨╛╨▓╨╛, ╨╖╨╡╨╗╤С╨╜╤Л╨╡. ╤С ╨▓╤Л╤А╨╡╨╖╨░╨╜╨╛ ╨╕╨╖
  ╨▓╤Л╨▓╨╛╨┤╨░ (╨┤╨╛╨╝. ╤Б╤В╨╕╨╗╤М); `╤В╤А╨╕╨┤╨╡╤Б╤П╤В╤М` ╨╜╨╡ ╨▓ OpenCorpora тАФ ╨┐╨░╤А╨░╨┤╨╕╨│╨╝╨░ ╨╖╨░╨┤╨░╨╜╨░ ╨▓╤А╤Г╤З╨╜╤Г╤О.

## [0.11.1] - 2026-07-17
### Added
- **╨Ф╨╛╨║╤Г╨╝╨╡╨╜╤В-╨╛╤В╨▓╨╡╤В: ╤Б╨║╨╗╨╛╨╜╨╡╨╜╨╕╨╡ ╤А╤Г╨▒╤А╨╕╨║ ╤Г╨║╨░╨╖╨░╤В╨╡╨╗╤П тАФ ╤Г╤З╤В╨╡╨╜╨╛ ╨╗╨╕, ╨╡╤Б╤В╤М ╨╗╨╕ ╤Д╤Г╨╜╨║╤Ж╨╕╨╛╨╜╨░╨╗
  (Opus 4.8 `claude-opus-4-8`).** [`docs/RUBANOVA_NKRYA_RUBRIC_DECLENSION_STATUS_2024_11.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/RUBANOVA_NKRYA_RUBRIC_DECLENSION_STATUS_2024_11.md):
  ╨┐╨╛ ╨╖╨░╨┐╤А╨╛╤Б╤Г тАФ ╨╡╤Б╤В╤М ╨╗╨╕ ╨▓ ╤А╨╡╨┐╨╛ ╤Д╤Г╨╜╨║╤Ж╨╕╨╛╨╜╨░╨╗ ╤Б╨║╨╗╨╛╨╜╨╡╨╜╨╕╤П ╤А╤Г╨▒╤А╨╕╨║ ╤Г╨║╨░╨╖╨░╤В╨╡╨╗╤П ╨╕╨╖ ╨╖╨░╨╝╨╡╤В╨║╨╕
  2024-11 (`Index_items_declension`). ╨Т╤Л╨▓╨╛╨┤: **╤А╨╡╨╖╤Г╨╗╤М╤В╨░╤В** ╤Б╨║╨╗╨╛╨╜╨╡╨╜╨╕╤П ╨╡╤Б╤В╤М ╨╕ ╤Г╨╢╨╡
  ╨╕╤Б╨┐╨╛╨╗╤М╨╖╤Г╨╡╤В╤Б╤П ╨▓ ╨┐╨╛╨╕╤Б╨║╨╡ (╤Д╨░╨╣╨╗ [`rus_index_declined.txt`](https://github.com/gasyoun/SamudraManthanam/blob/main/nkrya-parallel/diplom-rubanova/rus_index_declined.txt) тАФ
  292 ╤А╤Г╨▒╤А╨╕╨║╨╕ / 1346 ╤Д╨╛╤А╨╝, 1148 ╨╝╨╜╨╛╨│╨╛╤Б╨╗╨╛╨▓╨╜╤Л╤Е ╤Б╨╕╨╜╨╛╨╜╨╕╨╝╨╕╤З╨╜╤Л╤Е ╤Д╤А╨░╨╖; ╨╕╨╝╨╡╨╜╨╜╨╛ ╨╕╤Е ╨╕╤Й╨╡╤В
  ╤Г╤Б╨║╨╛╤А╨╡╨╜╨╜╤Л╨╣ H1204 ╨Р╤Е╨╛-╨Ъ╨╛╤А╨░╤Б╨╕╨║ ╤Б╨╗╨╛╨╣), ╨╜╨╛ **╨│╨╡╨╜╨╡╤А╨░╤В╨╛╤А** (`Index_items_declension.ipynb`,
  `index_lone_declined_manual.json`, `pyphrasy`, ╤А╨░╨╖╨▒╨╕╨▓╨║╨░ ╨╜╨░ ╤Б╨╕╨╜╨╛╨╜╨╕╨╝╨╕╤З╨╜╤Л╨╡ ╤Д╤А╨░╨╖╤Л,
  ╨╗╨╛╨│ ╤В╨╛╤З╨╜╨╛╤Б╤В╨╕ 89.6 % / 86.5 %) ╨▓ ╤А╨╡╨┐╨╛ **╨╛╤В╤Б╤Г╤В╤Б╤В╨▓╤Г╨╡╤В** тАФ ╨╕╨╖ ╤Б╨║╨╗╨╛╨╜╤П╤В╨╡╨╗╨╡╨╣ ╨╡╤Б╤В╤М ╤В╨╛╨╗╤М╨║╨╛
  ╤Г╨┐╤А╨╛╤Й╤С╨╜╨╜╤Л╨╣ `decline()` ╨а╤Г╨▒╨░╨╜╨╛╨▓╨╛╨╣ (pymorphy2 + ╤А╤Г╤З╨╜╨░╤П ╤В╨░╨▒╨╗╨╕╤Ж╨░ ~50 ╨╝╨╜╨╛╨│╨╛╤Б╨╗╨╛╨▓╨╜╤Л╤Е).
  H1204-╤Г╤Б╨║╨╛╤А╨╡╨╜╨╕╨╡ тАФ ╨╜╨╕╨╢╨╡ ╨┐╨╛ ╨┐╨╛╤В╨╛╨║╤Г (╨┐╨╛╨╕╤Б╨║ ╨┐╨╛ ╤Г╨╢╨╡ ╤Б╨║╨╗╨╛╨╜╤С╨╜╨╜╤Л╨╝ ╤Д╨╛╤А╨╝╨░╨╝), ╤Б╨║╨╗╨╛╨╜╨╡╨╜╨╕╨╡ ╨╜╨╡
  ╤В╤А╨╛╨│╨░╨╡╤В ╨╕ ╨╜╨╡ ╨▓╨╛╤Б╨┐╤А╨╛╨╕╨╖╨▓╨╛╨┤╨╕╤В.

## [0.11.0] - 2026-07-17
### Changed
- **╨г╤Б╨║╨╛╤А╨╡╨╜╨╕╨╡ ╨┐╨░╨╣╨┐╨╗╨░╨╣╨╜╨░ ╨а╤Г╨▒╨░╨╜╨╛╨▓╨╛╨╣ тАФ ╨║╨╛╨┤-╤А╨╡╨▓╤М╤О + ╨╛╨┐╤В╨╕╨╝╨╕╨╖╨░╤Ж╨╕╤П ╨│╨╛╤А╤П╤З╨╕╤Е ╨┐╤Г╤В╨╡╨╣
  (H1204, Opus 4.8 `claude-opus-4-8`).** Stage B ([`sans_stemmer.ipynb`](https://github.com/gasyoun/SamudraManthanam/blob/main/nkrya-parallel/diplom-rubanova/sans_stemmer.ipynb))
  ╨▒╤Л╨╗ ╤В╨╡╨╝ ╤Б╨░╨╝╤Л╨╝ ┬л╤Б╨╗╨╕╤И╨║╨╛╨╝ ╨╝╨╡╨┤╨╗╨╡╨╜╨╜╨╛┬╗: ╨╡╨│╨╛ ╤Б╨╛╨▒╤Б╤В╨▓╨╡╨╜╨╜╨░╤П ╤П╤З╨╡╨╣╨║╨░ `%%time` ╨┐╨╛╨║╨░╨╖╤Л╨▓╨░╨╡╤В
  **5 ╨╝╨╕╨╜ 8 ╤Б ╨╜╨░ 32 ╨┐╤А╨╡╨┤╨╗╨╛╨╢╨╡╨╜╨╕╤П**. ╨Ш╤Б╨┐╤А╨░╨▓╨╗╨╡╨╜╤Л ╨│╨╛╤А╤П╤З╨╕╨╡ ╨┐╤Г╤В╨╕ ╨▓╨╛ ╨▓╤Б╨╡╤Е ╤В╤А╨╡╤Е ╨╜╨╛╤Г╤В╨▒╤Г╨║╨░╤Е
  **╨╕** ╨▓ Python-╨┐╨╛╤А╤В╨╡ тАФ **╨▒╨╡╨╖ ╨╕╨╖╨╝╨╡╨╜╨╡╨╜╨╕╤П ╨▓╤Л╨▓╨╛╨┤╨░** (╨║╨░╨╢╨┤╨╛╨╡ ╨╕╤Б╨┐╤А╨░╨▓╨╗╨╡╨╜╨╕╨╡ ╨┐╤А╨╛╨▓╨╡╤А╨╡╨╜╨╛
  ╨┐╨╛╨▒╨░╨╣╤В╨╛╨▓╨╛ ╨╗╨╕╨▒╨╛ ╨┤╨╛╨║╨░╨╖╨░╨╜╨╛ ╨╕╨┤╨╡╨╜╤В╨╕╤З╨╜╤Л╨╝ ╨╜╨░ ╤А╨╡╨┐╤А╨╡╨╖╨╡╨╜╤В╨░╤В╨╕╨▓╨╜╤Л╤Е ╨┤╨░╨╜╨╜╤Л╤Е; ╤Б╤В╤А╤Г╨║╤В╤Г╤А╨░ Colab тАФ
  Drive-mount, `input()`, `!pip` тАФ ╤Б╨╛╤Е╤А╨░╨╜╨╡╨╜╨░). ╨в╨░╨▒╨╗╨╕╤Ж╨░ before/after ╨╕ ╤А╨░╨╖╨▒╨╛╤А ╨┐╤А╨╕╤З╨╕╨╜:
  [`docs/RUBANOVA_NKRYA_PIPELINE_MANUAL.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/RUBANOVA_NKRYA_PIPELINE_MANUAL.md) ┬з10.
  - **╨Я╨╛╤А╤В** [`web/corpus_builder/sanskritisms/extract.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/sanskritisms/extract.py):
    ╤Б╨╗╨╛╨╣ ╤Н╨┐╨╕╤В╨╡╤В╨╛╨▓ ╤Б╨║╨░╨╜╨╕╤А╨╛╨▓╨░╨╗ ╨┐╨╗╨╛╤Б╨║╤Г╤О `re`-╨░╨╗╤М╤В╨╡╤А╨╜╨░╤Ж╨╕╤О ╨╕╨╖ 1346 ╤Б╨║╨╗╨╛╨╜╨╡╨╜╨╜╤Л╤Е ╤Д╨╛╤А╨╝ ╨┐╨╛
    ╨║╨░╨╢╨┤╨╛╨╝╤Г ╤Б╤В╨╕╤Е╤Г (`O(╤В╨╡╨║╤Б╤В ├Ч ╤Д╨╛╤А╨╝╤Л)`) тЖТ ╨░╨▓╤В╨╛╨╝╨░╤В ╨Р╤Е╨╛-╨Ъ╨╛╤А╨░╤Б╨╕╨║ (╨╜╨╛╨▓╤Л╨╣
    [`_aho.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/sanskritisms/_aho.py),
    ╨▒╨╡╨╖ ╨╖╨░╨▓╨╕╤Б╨╕╨╝╨╛╤Б╤В╨╡╨╣). ╨Э╨░ ╨Ь╨С╤Е ╨Р╤А╨░╨╜╤М╤П╨║╨░╨┐╨░╤А╨▓╨╡ (2033 ╤Б╤В╨╕╤Е╨░, 199 570 ╤В╨╛╨║╨╡╨╜╨╛╨▓) extract+index
    **10.82 ╤Б тЖТ 3.45 ╤Б (3.1├Ч)**; ╨╛╤В╨┐╨╡╤З╨░╤В╨║╨╕ lexicon/epithets/index ╨╜╨╡ ╨╕╨╖╨╝╨╡╨╜╨╕╨╗╨╕╤Б╤М (0
    ╤А╨░╤Б╤Е╨╛╨╢╨┤╨╡╨╜╨╕╨╣ ╨┐╨╛ ╨▓╤Б╨╡╨╝ 2033 ╤Б╤В╨╕╤Е╨░╨╝), 30 hermetic + 3 corpus ╤В╨╡╤Б╤В╨░ ╨╖╨╡╨╗╨╡╨╜╤Л╨╡.
  - **`sans_stemmer.ipynb`**: `open_files` (`lem not in forn + sans` ╨┐╨╡╤А╨╡╤Б╨╛╨▒╨╕╤А╨░╨╗
    ~24 k-╤Б╨┐╨╕╤Б╨╛╨║ ╨╜╨░ ╨║╨░╨╢╨┤╤Г╤О ╨╕╨╖ ~390 k ╨┐╨░╤А╨░╨┤╨╕╨│╨╝ OpenCorpora тЖТ `set(forn) | set(sans)`
    ╨╛╨┤╨╕╨╜ ╤А╨░╨╖, ~1900├Ч ╨╜╨░ ╤Н╤В╨╛╨╝ ╤И╨░╨│╨╡); `search` (`.lower()` ╨┐╨╡╤А╨╡╤Б╤З╨╕╤В╤Л╨▓╨░╨╗╤Б╤П ╨╜╨░ ╨║╨░╨╢╨┤╤Л╨╣
    ╨║╨╗╤О╤З-╤А╤Г╨▒╤А╨╕╨║╤Г + list-comp ╨╜╨░ ╨║╨░╨╢╨┤╨╛╨╡ ╤Б╨╗╨╛╨▓╨╛ тЖТ ╨▓╤Л╨╜╨╛╤Б `sent_low`/`text_low` +
    ╨┐╤А╨╡╤Д╨╕╨║╤Б╨╜╤Л╨╡ ╨╝╨╜╨╛╨╢╨╡╤Б╤В╨▓╨░, ~15├Ч ╨╜╨░ ╤П╨┤╤А╨╡ ╤Б╨╛╨┐╨╛╤Б╤В╨░╨▓╨╗╨╡╨╜╨╕╤П); `index_unite` (╨┐╨╡╤А╨╡╤Б╨▒╨╛╤А╨║╨░
    `list(set(clean))` ╨▓╨╛ ╨▓╨╜╤Г╤В╤А╨╡╨╜╨╜╨╡╨╝ ╤Ж╨╕╨║╨╗╨╡ + `re.match` ╨╜╨░ ╤Н╨╗╨╡╨╝╨╡╨╜╤В ╨╖╨░ ╨┐╤А╨╛╤Е╨╛╨┤ тЖТ ╨▓╤Л╨╜╨╛╤Б
    `uniq` + ╨┐╤А╨╡╨┤╨▓╤Л╤З╨╕╤Б╨╗╨╡╨╜╨╕╨╡ ╤Б╨╗╨╛╨▓╨░, ~3тАУ4├Ч); `get_wordforms` (╨┐╨╡╤А╨╡╤З╨╕╤В╤Л╨▓╨░╨╗+╤З╨╕╤Б╤В╨╕╨╗ ╨▓╨╡╤Б╤М
    ╤Д╨░╨╣╨╗ ╨╜╨░ ╨║╨░╨╢╨┤╤Л╨╣ ╨▓╤Л╨╖╨╛╨▓ тЖТ ╨║╤Н╤И ╨╛╤З╨╕╤Й╨╡╨╜╨╜╤Л╤Е ╤В╨╛╨║╨╡╨╜╨╛╨▓); `capital_search` (╨║╨╛╨╜╨║╨░╤В╨╡╨╜╨░╤Ж╨╕╤П
    `sans + index3 + tr` ╨╜╨░ ╨║╨░╨╢╨┤╨╛╨╡ ╤Б╨╗╨╛╨▓╨╛ тЖТ ╨▓╤Л╨╜╨╛╤Б).
  - **`corpus_marker.ipynb`**: `translate()` (IASTтЖТ╨║╨╕╤А╨╕╨╗╨╗╨╕╤Ж╨░, ╨▓╤Л╨╖╤Л╨▓╨░╨╡╤В╤Б╤П ╨╜╨░ ╨║╨░╨╢╨┤╨╛╨╡
    ╤Б╨╗╨╛╨▓╨╛ ╨╕ ╨╜╨░ ╨║╨░╨╢╨┤╤Л╨╣ ╤Б╨╕╨╝╨▓╨╛╨╗ ╨▓ `proc_short`/`proc_long`) ╨╝╨╡╨╝╨╛╨╕╨╖╨╕╤А╨╛╨▓╨░╨╜ ╨┐╨╛ ╨▓╤Е╨╛╨┤╤Г тАФ
    ╤З╨╕╤Б╤В╨░╤П ╤Д╤Г╨╜╨║╤Ж╨╕╤П, ╨▓╤Л╨▓╨╛╨┤ ╨╜╨╡ ╨╕╨╖╨╝╨╡╨╜╨╕╨╗╤Б╤П.

## [0.10.0] - 2026-07-17
### Added
- **╨б╤В╨╕╤Е╨╛╨▓╨░╤П ╨┐╤А╨╛╨▓╨╡╤А╨║╨░: ╤А╨░╨╖╨╗╨╕╤З╨░╤О╤В ╨╗╨╕ ╤А╤Г╤Б╤Б╨║╨╕╨╡ ╨┐╨╡╤А╨╡╨▓╨╛╨┤╤З╨╕╨║╨╕ ╤Б╨░╨╜╤Б╨║╤А╨╕╤В╤Б╨║╨╕╨╡ ╨┐╤А╨╛╤И╨╡╨┤╤И╨╕╨╡ ╨▓╤А╨╡╨╝╨╡╨╜╨░
  (H1052, Fable 5 `claude-fable-5`; ╨┤╨╕╤А╨╡╨║╤В╨╕╨▓╨░ ╨░╨┤╤К╤О╨┤╨╕╨║╨░╤Ж╨╕╨╕ A65 ╨║ HB-57).** ╨Э╨╛╨▓╤Л╨╣ ╨╕╨╜╤Б╤В╤А╤Г╨╝╨╡╨╜╤В
  [`nkrya-parallel/export/past_tense_translation_check.py`](nkrya-parallel/export/past_tense_translation_check.py)
  (+ stats JSON + ╨╛╤В╤З╨╡╤В [`PAST_TENSE_TRANSLATION_CHECK.md`](nkrya-parallel/export/PAST_TENSE_TRANSLATION_CHECK.md)):
  41 023 ╤Н╨┐╨╕╤З╨╡╤Б╨║╨╕╨╡ ╨┐╨░╤А╤Л ╤Б╤В╨╕╤ЕтЗД╨┐╨╡╤А╨╡╨▓╨╛╨┤, DCS-╨▓╤Л╨▓╨╡╨┤╨╡╨╜╨╜╤Л╨╡ ╨╗╨╡╨║╤Б╨╕╨║╨╛╨╜╤Л ╨▓╤Л╤Б╨╛╨║╨╛╨╣ ╤В╨╛╤З╨╜╨╛╤Б╤В╨╕ (╨╕╨╝╨┐╨╡╤А╤Д╨╡╨║╤В
  342 ╤Д╨╛╤А╨╝ ╨┐╨╛ ╤В╨╡╨│╨░╨╝ ┬╖ ╨░╨╛╤А╨╕╤Б╤В 179 ╨┐╨╛ formation-╤В╨╡╨│╨░╨╝ ┬╖ ╨┐╨╡╤А╤Д╨╡╨║╤В 193 ╤З╨╡╤А╨╡╨╖ ╤В╨╡╤Б╤В ╤А╨╡╨┤╤Г╨┐╨╗╨╕╨║╨░╤Ж╨╕╨╕ тАФ
  ╤А╨╡╨┤╤Г╨┐╨╗╨╕╤Ж╨╕╤А╨╛╨▓╨░╨╜╨╜╤Л╨╣ ╨┐╨╡╤А╤Д╨╡╨║╤В ╨▓ DCS ╨╜╨╡ ╤В╨╡╨│╨╕╤А╨╛╨▓╨░╨╜). **╨Ш╤В╨╛╨│: ╨┐╨╡╤А╨╡╨▓╨╛╨┤ ╨Э╨Х╨Щ╨в╨а╨Р╨Ы╨Ш╨Ч╨г╨Х╨в
  ╨┐╤А╨╛╤В╨╕╨▓╨╛╨┐╨╛╤Б╤В╨░╨▓╨╗╨╡╨╜╨╕╨╡** тАФ ╨╕ ╨┐╨╡╤А╤Д╨╡╨║╤В╨╜╤Л╨╡, ╨╕ ╨╕╨╝╨┐╨╡╤А╤Д╨╡╨║╤В╨╜╤Л╨╡ ╤Б╤В╨╕╤Е╨╕ ╤Г╤Е╨╛╨┤╤П╤В ╨▓ ╤А╤Г╤Б╤Б╨║╨╛╨╡ ╨┐╤А╨╛╤И╨╡╨┤╤И╨╡╨╡
  ╤Б╨╛╨▓╨╡╤А╤И╨╡╨╜╨╜╨╛╨│╨╛ ╨▓╨╕╨┤╨░ (64,7 % ╨┐╤А╨╛╤В╨╕╨▓ 67,7 %), ╨┐╤А╨╛╤Д╨╕╨╗╨╕ ╨┐╨╛╤З╤В╨╕ ╤Б╨╛╨▓╨┐╨░╨┤╨░╤О╤В; ╧З┬▓ = 38,7 ╨╖╨╜╨░╤З╨╕╨╝, ╨╜╨╛
  V ╨Ъ╤А╨░╨╝╨╡╤А╨░ = 0,084 тАФ ╤А╨░╨╖╨╝╨╡╤А ╤Н╤Д╤Д╨╡╨║╤В╨░ ╨╜╨╕╤З╤В╨╛╨╢╨╡╨╜. ╨Я╤А╤П╨╝╨╛╨╡ ╨┐╨╛╨┤╤В╨▓╨╡╤А╨╢╨┤╨╡╨╜╨╕╨╡ ╨┤╨╛╨║╤В╤А╨╕╨╜╤Л ┬л╤В╨╛ ╨╢╨╡
  ╨╖╨╜╨░╤З╨╡╨╜╨╕╨╡┬╗ ╨┐╨╡╤А╨╡╨▓╨╛╨┤╤З╨╡╤Б╨║╨╛╨╣ ╨┐╤А╨░╨║╤В╨╕╨║╨╛╨╣. ╨Ю╤Б╤В╨░╤В╨╛╨║: ╨┐╨╡╤А╤Д╨╡╨║╤В╨╜╤Л╨╡ ╤Б╤В╨╕╤Е╨╕ ╤З╤Г╤В╤М ╤З╨░╤Й╨╡ ╨╕╨┤╤Г╤В ╨╜╨░╤Б╤В╨╛╤П╤Й╨╕╨╝
  ╨╕╤Б╤В╨╛╤А╨╕╤З╨╡╤Б╨║╨╕╨╝ (10,3 % vs 5,5 %); ╨║╨╗╨╕╤И╨╡ ┬лuv─Бca тЖТ ╨│╨╛╨▓╨╛╤А╨╕╤В┬╗ ╨╡╨│╨╛ ╨╜╨╡ ╨╛╨▒╤К╤П╤Б╨╜╤П╨╡╤В (3,5 % ╨╕╨╖ 2 652).

## [0.9.0] - 2026-07-16
### Added
- **Chronology dashboard тАФ Minimal design mockup (H563 fan-out, H1057).** [web/corpus_builder/chronology/mockups/minimal.html](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/chronology/mockups/minimal.html): CSS-only restyle of the live [chronology page](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/chronology/index.html) into the Minimal direction (paper-white, single indigo accent, hairline rules) тАФ markup, 934-text data island and render JS byte-identical (sha1-verified); JSON parses, JS syntax-checked. The Flask compare pages (`web/templates/compare_*.html`) need a live backend and are out of mockup scope (H815 precedent). Live page untouched pending a human's promotion call. Fable 5 (`claude-fable-5`).

## [0.8.0] - 2026-07-14

### Added
- **Somadeva KSS books 1тАУ10 sloka re-key (H928) тАФ all 18 KSS books now uniformly
  ┼Ыloka-keyed.** Re-ingested books 1-10 from lingtrain sentence-ordinal keys to true
  ┼Ыloka keys (`lambaka.taraс╣Еga.┼Ыloka(-range)`, `structure="verse"`), matching books
  11-18's H910 keying. Per-taraс╣Еga Workflow fan-out (76 tasks: 66 taraс╣Еgas + 10 maс╣Еgala
  verses), ground-truth sliced directly from `parse_sanskrit`/`parse_russian`'s own
  record grouping (`web/corpus_builder/h928_prep_taranga_slices.py`, assertion-checked
  exact match against whole-book totals: 12,806 ┼Ыlokas / 1,658 RU sentences) тАФ supersedes
  an inherited `h928_plan.json` found to drift from real per-book counts. Fixed the RU
  wave-header regex in `somadeva_gretil_to_canonical.py` (optional trailing dot тАФ books
  1-10's first `## L.T` header per chapter lacks it, previously misattributing taraс╣Еga-1
  Russian text to taraс╣Еga 0). Two genuine alignment defects caught by `validate_mapping`
  and fixed via targeted re-alignment: book 10 taraс╣Еga 3 (8 Russian sentences degenerately
  collapsed onto one ┼Ыloka) and book 8 taraс╣Еga 6 (off-by-one at a real source-numbering
  gap, ┼Ыloka 244 skipped). Final: 1,658 groups, mean confidence 0.82 (0.68тАУ0.87 per book),
  searchable in FTS5. `web/corpus_builder/h928_aggregate_and_emit.py` converts per-taraс╣Еga
  local Russian indices to global per-book indices and runs the existing
  `validate_mapping`/`emit_jsonl` pipeline.

### Fixed
- **Bс╣Ыhann─лla-tantra JSONL duplicate comment IDs** (48 identical double rows) blocked full-pin web publish; dropped dups (2533тЖТ2485 records). Rebuild corpus-manifest pin: **230** sources / **723тАп229** records. `*.jsonl text eol=lf` in `.gitattributes` so Windows pin builds match Linux publish.
- **Full-corpus `ingest.py` was failing on the combined DBhP source (H941).**
  `data.txt` lists the real, intentionally-built `devibhagavata-purana.html`
  but its canonical `web/corpus_builder/jsonl/devibhagavata-purana.jsonl` was
  never persisted (H558's `emit_dbhp_corpus.py` only ever wrote it to a temp
  path). Regenerated by concatenating skandhas 1тАУ12 in order (37,984 lines,
  matching the documented record count, zero id collisions); full ingest now
  completes 182/182 sources with exit 0.

## [0.7.0] - 2026-07-14

### Added
- **Somadeva KSS book 12 complete (all 37 taraс╣Еgas) + book 14 QA re-run (H927).**
  Book 12 (┼Ъa┼Ы─Бс╣Еkavat─л, 4 931 ┼Ыlokas incl. the 25 Vet─Бlapa├▒caviс╣Г┼Ыati tales) fully
  aligned via a 34-agent per-taraс╣Еga Workflow fan-out тАФ 900 groups, 1 800 records,
  confidence min 0.15 mean 0.81. Book 14's old positional alignment (mean 0.53,
  a token-limit fallback from H910) replaced with a content-anchored per-taraс╣Еga
  re-run тАФ mean confidence 0.53 тЖТ 0.80, low-confidence groups 122 тЖТ 8. **18 of 18
  lambakas now in the corpus.** Caught + fixed a real fan-out defect: one taraс╣Еga's
  first pass produced inverted ┼Ыloka ranges, re-run with an explicit self-check.
  70 low-confidence groups routed to a review sheet. Reproducible artifacts:
  `somadeva_alignments/book12.alignment.json` / `book14.alignment.json`,
  `h927_prep_taranga_slices.py`. Report:
  `web/corpus_builder/SOMADEVA_KSS_BOOK12_BOOK14QA_FANOUT_REPORT.md`.
- **Somadeva KSS books 13тАУ18 aligned + ingested (H910 fan-out).** Six more
  lambakas ┼Ыloka-keyed and searchable (13 Madir─Бvat─л, 14 *pa├▒ca*, 15 Mah─Бbhiс╣гeka,
  16 Suratama├▒jar─л, 17 Padm─Бvat─л, 18 Viс╣гama┼Ы─лla) тАФ **17 of 18 books now in the
  corpus**. 3 683 ┼Ыlokas тЖТ 681 groups; alignment maps committed under
  `web/corpus_builder/somadeva_alignments/`. Two upstream data defects found +
  handled reproducibly: the **SA/RU file swap at lambakas 14тЖФ15** (added a
  `--ru-book` converter option; passage keys always from the Sanskrit lambaka) and
  the **book-12 Vet─Бla-ref annotation** that silently dropped 1 958 ┼Ыlokas (regex
  loosened). `build_corpus_html._ROMAN` extended XIIтЖТXX for 18 books. Book 12
  (giant, 4 931 ┼Ыlokas) deferred to a per-taraс╣Еga run; book 14 is positional
  (token-limit fallback), flagged for review. Report:
  `web/corpus_builder/SOMADEVA_KSS_BOOKS_11_18_FANOUT_REPORT.md`.
- **Somadeva KSS book-11 pilot тАФ LLM-assisted ┼Ыloka alignment (H910).** New
  `web/corpus_builder/somadeva_gretil_to_canonical.py` parses the in-repo
  `sokss`-keyed Sanskrit + Serebryakov Russian prose for books 11тАУ18; an LLM
  aligner produces a monotonic ┼Ыloka-range mapping. **Book 11 (Vel─Б) aligned +
  ingested end-to-end**: 116 ┼Ыlokas тЖФ 27 Russian sentences тЖТ 27 ┼Ыloka-range groups
  (`structure="verse"`, keys like `11.1.4-10`), searchable in FTS5. Reproducible
  artifacts: converter, `somadeva_alignments/book11.alignment.json`,
  `jsonl/kathasaritsagara-11.jsonl`, `Data/kathasaritsagara-11.html`. **Measured
  Human vs. Agent:** 8.8 min (agent) vs ~15.7 days (human pace) for book 11 тАФ
  `web/corpus_builder/SOMADEVA_KSS_ALIGNMENT_PILOT_REPORT.md`.
- **`/corpus-rights-unlock` skill** referenced in
  `docs/SOMADEVA_KSS_RIGHTS_COPYRIGHT_UNLOCK.md` (+ a plain-language "what opens up
  when copyright clears" example): the reusable playbook for publishing any
  grey-rights corpus once rights are cleared.

### Changed
- **`morph_service.py` dropped `indic_transliteration` for the canonical
  `sanskrit-util` package (H922 momentum-axis track).** The three transliterate
  calls (IAST/Devan─Бgar─лтЖТSLP1, SLP1тЖТIAST, SLP1тЖТDevan─Бgar─л) now use
  `sanskrit_util.to_slp1`/`deva_to_slp1`/`from_slp1`/`slp1_to_devanagari`.
  Vendored (not pip-installed) as `web/app/vendor/sanskrit_util.py` тАФ a
  byte-identical copy of `sanskrit-util/py/sanskrit_util/__init__.py` v0.4.0 тАФ
  because the Docker build (`COPY web/ .`) has no access to the sibling
  `sanskrit-util` repo; same "re-copy on update, never hand-edit" pattern as the
  org's JS vendor copies (csl-atlas, csl-apidev). 96 old-vs-new comparisons
  across 4 directions on real Sanskrit words matched byte-for-byte; the one
  intentional difference found is a **fix**, not a regression тАФ the old library
  silently passed `с╣Б` (U+1E41) through unconverted, sanskrit-util correctly
  folds it to SLP1 `M`. All 568 pre-existing tests (9 in `test_morph.py`) pass
  unchanged before and after. `indic-transliteration` stays in
  `web/requirements.txt` тАФ `web/corpus_builder/html_to_canonical.py` (an offline
  ingestion script, not part of the running app) still depends on it; that file
  and `slug.py` (Cyrillic transliteration, out of scope) are unchanged. See
  [SHARED_CODE.md](https://github.com/gasyoun/github-spine/blob/main/SHARED_CODE.md)
  ┬з1-2 row 4.

## [0.6.0] - 2026-07-14

### Added
- **SA-side morphology anchored on DCS gold (H906).** New
  [`web/corpus_builder/dcs_align.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/dcs_align.py)
  aligns each `seg=sa` verse to the matching DCS chapter (`passage B.C.V` тЖТ
  `MBh, B, C` / `R─Бm, <k─Бс╣Зс╕Нa>, C`; DCS `sent_counter` = verse) and emits the DCS
  **gold** per-token analysis (lemma ┬╖ UPOS ┬╖ case ┬╖ gender ┬╖ number) behind
  `nkrya_export.py --sa-morph` as an additive `<slug>.sa_morph.tsv` (deterministic).
  Coverage: **MBh ~99%** (most parvas 98тАУ100%; 152k gold tokens on ─Аraс╣Зyakaparva),
  R─Бm─Бyaс╣Зa partial (62тАУ80%, verse-map divergence). The Bhagavadg─лt─Б gap surfaces
  as bhishmaparva 47.6% (G─лt─Б absent from DCS, H848). DCS sqlite is local-only
  (`$DCS_SQLITE`); the layer degrades to empty if absent. +3 tests (12 pass).
  Report: [`SA_MORPHOLOGY_H906_REPORT.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/SA_MORPHOLOGY_H906_REPORT.md).
  The vidyut second-opinion diff is a scoped follow-up (needs the vidyut data download).

## [0.5.0] - 2026-07-14

### Added
- **RU-side morphology + ╨Ъ╨░╨╗╨╕тЖТ╨║╨░╨╗ filter (H905).** New [`web/corpus_builder/ru_morph.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/ru_morph.py)
  tags every Cyrillic token of a `seg=ru` segment with **lemma ┬╖ POS ┬╖ case ┬╖ number** via
  **pymorphy3** (which ships the OpenCorpora dictionary тАФ the same ╨Ъ╨а╨б data Rubanova's 271 MB
  `dict.opcorpora.txt` held), emitted behind `nkrya_export.py --ru-morph` as an additive
  `<slug>.ru_morph.tsv` (deterministic, byte-identical across `PYTHONHASHSEED`). The inline ╨Э╨Ъ╨а╨п
  `<w><ana/>` fold is deferred to the H906-coordinated per-token scheme.
### Fixed
- **Bс╣Ыhann─лla-tantra JSONL duplicate comment IDs** (48 identical double rows) blocked full-pin web publish; dropped dups (2533тЖТ2485 records). Rebuild corpus-manifest pin: **230** sources / **723тАп229** records. `*.jsonl text eol=lf` in `.gitattributes` so Windows pin builds match Linux publish.
- **╨Ъ╨░╨╗╨╕тЖТ╨║╨░╨╗ false positives (H905).** `sanskritisms/filters.py` gains `is_russian_word()`
  (pymorphy3 `word_is_known`, minus Rubanova's curated collision exceptions); `extract.py` now
  drops any non-capitalized candidate that is a known Russian wordform тАФ reproducing Rubanova's
  `rus_words` opcorpora filter without the 271 MB dump. Lowercase ┬л╨║╨░╨╗╨░┬╗ (genitive of the common
  word *╨║╨░╨╗*) no longer captured as the Sanskritism *╨║╨░╨╗╨░*; capitalized proper names stay exempt.
  Measured 41тЖТ37 lemmas on `01_atharvaveda` (4 false positives removed). +3 regression tests.
  Report: [`web/corpus_builder/RU_MORPHOLOGY_H905_REPORT.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/RU_MORPHOLOGY_H905_REPORT.md).
### Changed
- **Somadeva KSS scale-up P0 resolved + made execution-ready (H910).** Confirmed
  the complete Serebryakov Russian and ┼Ыloka-keyed Sanskrit (`sokss_L,T.S` refs)
  for **all 18 books** already exist as `.txt` in the upstream repo (~21 538
  ┼Ыlokas; books 11тАУ18 = ~8 730). Books 11тАУ18 need alignment only тАФ no sourcing,
  no external fetch, no human gate. Rewrote
  `docs/ROADMAP_SOMADEVA_KSS_ALIGNMENT_SCALEUP_2026_2027.md` execution-ready and
  added `docs/SOMADEVA_KSS_RIGHTS_COPYRIGHT_UNLOCK.md` (what a proven copyright /
  redistribution licence unlocks: ╨Э╨Ъ╨а╨п export, kosha datasets.json, Zenodo DOI,
  bulk download).

## [0.4.1] - 2026-07-14

### Added
- **Somadeva Kath─Бsarits─Бgara SAтЖФRU corpus тАФ 10 lambakas ingested (H907).**
  Absorbed the [Marc-Winner/somadeva](https://github.com/Marc-Winner/somadeva)
  lingtrain alignment into the corpus: new
  `web/corpus_builder/somadeva_lingtrain_to_canonical.py` converts the Lingtrain
  XML (8 chapters) + `.lt` `doc_index` (ch4, ch10) into canonical JSONL тАФ
  **9 998 aligned sentence-pairs across lambakas 1тАУ10**, keyed
  `lambaka.taraс╣Еga.sentence-ordinal`, DevanagariтЖТIAST/SLP1. Emitted
  `kathasaritsagara.meta.json`, combined + per-lambaka `jsonl/kathasaritsagara*.jsonl`,
  10 `Data/kathasaritsagara-{N}.html`+`.no_tags`+meta, `data.txt` registration.
  Verified searchable via real `ingest.py` тЖТ FTS5 (10 sources / 19 994 rows;
  `somaprabh─Б` 33, `╨╛╨║╨╡╨░╨╜` 58 hits) + schema contract tests green. Russian inherits
  the corpus "grey per project ruling" rights status (`corpus.db` gitignored).
  Scale-up plan (full 18 lambakas, LLM-assisted, GRETIL spine) +
  lingtrain-vs-LLM method comparison in
  `docs/ROADMAP_SOMADEVA_KSS_ALIGNMENT_SCALEUP_2026_2027.md`.
- **╨Э╨Ъ╨а╨п morphology Wave 0: Rubanova pipeline documented (H904).** E. A.
  Rubanova's two source notebooks (`sans_stemmer.ipynb` +
  `deeppavlov_parsing.ipynb`, as updated by Marsel) are now tracked in
  `nkrya-parallel/diplom-rubanova/`, and `docs/RUBANOVA_NKRYA_PIPELINE_MANUAL.md`
  (+ `.meta.md`) documents the whole pipeline line-by-line: the 10 data inputs,
  Stage A (DeepPavlov UD morphosyntax) тЖТ Stage B (sanskritism proper-name index),
  the **╨Ъ╨░╨╗╨╕тЖТ╨║╨░╨╗ root cause** (the dropped 271 MB opcorpora corpus filter), and an
  original-vs-current-port delta table that is the work-list for the RU-morphology
  (H905) and SA-morphology (H906) builds. The Sanskrit side used **DCS** as its
  markup source (no home-grown analyzer) тАФ documented as a reproduction target for
  H906, not a port.
- **Third notebook + upstream source (H904 follow-up).** Took
  `corpus_marker.ipynb` from Rubanova's upstream repo
  ([evgeniarubanova/sanskrit_stemmer](https://github.com/evgeniarubanova/sanskrit_stemmer))
  тАФ the **RUтЖФSA word aligner** that transliterates IASTтЖТCyrillic (via
  `translation.txt`/`correct_trans.txt`) and prefix-matches Russian sanskritisms
  to their Sanskrit source words over a verse-block-aligned corpus, then
  colour-highlights both sides. Now tracked as Stage C; the manual's ┬з6 corrected
  accordingly тАФ the SA side uses **transliteration+alignment, not DCS** (DCS
  morphology stays an H906 reproduction target). MANIFEST now points at the
  upstream repo for the bulk data; noted that `dict.opcorpora.txt` is absent even
  upstream (third-party OpenCorpora).

## [0.4.0] - 2026-07-13

### Added
- **╨Э╨Ъ╨а╨п Wave 4: full-corpus export freeze (H821).** `nkrya_export.py` gains an
  `--all-ru` mode that exports **every seg=ru source** (131, via `discover_ru_sources()`)
  with `--with-sanskritisms`, not just the 4-source pilot: **95,260 pairs across 131 sources**.
  Two committed sidecars тАФ `nkrya-parallel/export/RIGHTS_TABLE.md` (per-source rights; 4 of 131
  documented from the H231 pilot meta, 127 flagged `needs_review` with no sidecar yet тАФ a noted
  metadata-population follow-up) and `FULL_CORPUS_VALIDATION.md` (per-source classify() stats).
  The bulk per-source export bundle stays gitignored and ships as a **release artifact**.
### Fixed
- **Bс╣Ыhann─лla-tantra JSONL duplicate comment IDs** (48 identical double rows) blocked full-pin web publish; dropped dups (2533тЖТ2485 records). Rebuild corpus-manifest pin: **230** sources / **723тАп229** records. `*.jsonl text eol=lf` in `.gitattributes` so Windows pin builds match Linux publish.
- **Sanskritisms index was non-deterministic** тАФ the singular/plural canonical merge
  (`sanskritisms/disambiguate.py`) and the candidate-set iteration (`extract.py`) depended on
  hash order, flipping the index `lemma`/`display` across runs. Now sorted тЖТ byte-identical
  output even across `PYTHONHASHSEED`, guarded by a new order-independence unit test. This was
  the blocker on Wave 4's determinism gate.

## [0.3.1] - 2026-07-12

### Fixed
- **Bс╣Ыhann─лla-tantra JSONL duplicate comment IDs** (48 identical double rows) blocked full-pin web publish; dropped dups (2533тЖТ2485 records). Rebuild corpus-manifest pin: **230** sources / **723тАп229** records. `*.jsonl text eol=lf` in `.gitattributes` so Windows pin builds match Linux publish.
- **Cyrillic homoglyph contamination in Sanskrit-IAST (`sa`) segments** тАФ 7 verses
  across 4 corpus files carried a Cyrillic letter mis-encoded where a Latin IAST
  letter belongs (`╤Б` U+0441 тЖТ `c`, `╨░` U+0430 тЖТ `a`): Sundarak─Бс╣Зс╕Нa 1.35 / 22.25 /
  31.4 / 37.12 and yoga-s┼лtra 4.8 (Vy─Бsa, Sharma, Zagumennov editions), in the
  `text` / `html` / `slp1` fields. Surfaced by the CommentaryStrategies
  helayo-alignment apparatus run (those verses were quarantined out of
  `apparatus_sundara_variants.json`). Fixed in place; re-scan confirms zero remain
  ([#45](https://github.com/gasyoun/SamudraManthanam/issues/45)).

### Added
- **`web/corpus_builder/scan_cyrillic_homoglyphs.py`** тАФ stdlib-only corpus-integrity
  scanner/fixer for Cyrillic homoglyphs inside `sa` segments. Token-aware: only a
  Cyrillic letter inside a mixed Latin+Cyrillic letter-run (the homoglyph signature)
  is substituted; pure-Cyrillic runs тАФ legitimate Russian editorial notes such as
  `{╨Я╤А╨╛╨▓╨╡╤А╨╕╤В╤М!}` or `[╨╜╨░ GRETIL ╨╜╨╡ ╤И╨╗╨╛╨║╨░]`, 2802 of them corpus-wide тАФ are left
  verbatim. `--fix` rewrites in place; report mode is read-only.

## [0.3.0] - 2026-07-12

### Added
- **Sanskrit-side 3-path annotation comparison** (╨Э╨Ъ╨а╨п Wave 2, H759):
  `web/corpus_builder/nkrya_annotate.py` (+ `web/tests/test_nkrya_annotate.py`)
  compares plain SLP1 (A) vs a text-keyed DCS lemma/morph crosswalk (B) vs
  vidyut-cheda fresh tagging (C) on the 11,055-pair pilot; committed
  metrics/report/adjudication-sample under `nkrya-parallel/export/`
  (`ANNOTATION_3PATH_COMPARISON.md`); new A41 ┬з6 records the resulting
  annotation policy (A always; B where DCS covers, CC BY 4.0; C not shipped).
- **╨Э╨Ъ╨а╨п / ruscorpora parallel-export programme** тАФ `nkrya-parallel/`: the
  SanskritтЖФRussian corpus export track toward the Russian National Corpus.
  Wave 0 landed the export roadmap and its eight MG rulings ([PR #39](https://github.com/gasyoun/SamudraManthanam/pull/39),
  H753) plus the curated diplom-rubanova reference artifacts and hardened bulk
  `.gitignore` ([PR #40](https://github.com/gasyoun/SamudraManthanam/pull/40)).
- **╨Э╨Ъ╨а╨п Wave-1 pilot triple export** (H754) тАФ Mah─Бbh─Бrata 3 + R─Бm─Бyaс╣Зa 1тАУ3
  exported in the parallel `#sa`/`#ru`/annotation triple schema
  ([PR #41](https://github.com/gasyoun/SamudraManthanam/pull/41)), the first
  end-to-end pilot of the export pipeline over real books.
- **Docusaurus review-packet site** for the ╨Т╨Ъ╨а/VKR review of the ╨Э╨Ъ╨а╨п export,
  with a GitHub Pages deploy workflow ([PR #38](https://github.com/gasyoun/SamudraManthanam/pull/38)).
- Reusable **PDF тЖТ canonical-JSONL тЖТ app-HTML** corpus-ingestion pipeline in
  `web/corpus_builder/` (the free-toolchain successor to the Delphi `cb.exe` for
  new ingestion): `ignatjev_pdf_to_canonical.py`, `align_sanskrit.py`,
  `build_corpus_html.py` тАФ documented in `web/corpus_builder/PDF_INGESTION_PIPELINE.md` (H534).
- **Dev─лbh─Бgavata-pur─Бс╣Зa Skandha 1** (A. Ignatjev, ╨Ъ╨░╤Б╤В╨░╨╗╨╕╤П 2018) ingested as
  `Data/devibhagavata-purana-1.html` (20 chapters, 1181 verses, 429 comments);
  152 тЖТ 153 active sources.
- **Sanskrit verse alignment for DBhP Skandha 1** тАФ `sanskritdocuments_dbhp_to_canonical.py`
  transcodes the sanskritdocuments.org ITRANS source (`devIbhAgavatam01.itx`) to
  the canonical `#sa` schema; the source-agnostic aligner joins it onto the
  Russian at **1180/1181 verses (99.9%)**. Sanskrit source chosen by MG
  (`@DECIDE` 10-07-2026) because the full DBhP is absent from GRETIL. Aligned
  IAST now renders alongside the Russian in `Data/devibhagavata-purana-1.html`.

- **Dev─лbh─Бgavata-pur─Бс╣Зa skandhas 2тАУ12** (A. Ignatjev, ╨Ъ╨░╤Б╤В╨░╨╗╨╕╤П 2018) ingested
  and Sanskrit-aligned (H558): 11 per-skandha `Data/devibhagavata-purana-<N>.html`
  files plus a combined `devibhagavata-purana.html` (all registered in
  `data.txt`), completing the 12-skandha work. ~17,300 RU verses / ~3,600
  comments; per-skandha RUтЖТSanskrit match ~99% (from `devIbhAgavatam02тАУ12.itx`,
  sanskritdocuments.org). 153 тЖТ 165 active sources.
- Batch drivers `web/corpus_builder/build_dbhp_skandhas.py` (RU parse тЖТ Sanskrit
  convert тЖТ align) and `emit_dbhp_corpus.py` (per-skandha + combined HTML).

### Changed
- Hardened `ignatjev_pdf_to_canonical.py` for all six Ignatjev volumes (H558):
  gap-tolerant endnote re-join (fixes the Vol 2/4/5 18/2/71 comment desync),
  plural/all-caps note headings, varied/wrapped chapter colophons, note-block
  skandha rollover, Dev─л-g─лt─Б chapter offset, and a duplicate passage-id
  integrity guard. Skandha 1 output unchanged (20 ch / 1181 v / 429 c).

### Deprecated

### Removed

### Fixed
- **Bс╣Ыhann─лla-tantra JSONL duplicate comment IDs** (48 identical double rows) blocked full-pin web publish; dropped dups (2533тЖТ2485 records). Rebuild corpus-manifest pin: **230** sources / **723тАп229** records. `*.jsonl text eol=lf` in `.gitattributes` so Windows pin builds match Linux publish.
- `html_to_canonical.py` now unescapes HTML entities in searchable text, so
  Ignatjev's OCR-mangled editorial brackets (`>тАж@`) round-trip exactly (16180/
  16180 RU verses reproduce); `build_corpus_html.py`'s sort key tolerates the
  integrity guard's disambiguation suffix.

### Security

## [0.2.0] - 2026-07-07

### Added
- Re-ingested 4 dharma┼Ы─Бstra texts (`naradasmriti`, `vishnu-smriti`, `yajnavalkyasmriti`, `yajnavalkyasmriti_add`) that existed on disk but were never added to the corpus manifest; 148 тЖТ 152 active sources.

## [0.1.1] - 2026-07-06

### Changed
- Filled `title_en`/`provenance`/`rights` across all 148 active corpus `meta.json` (Phase 0 hygiene, H231) via a reproducible per-slug script (`web/ingest/fill_meta_phase0.py`).

## [0.1.0] - 2026-06-30

### Added
- Initial release of Samudra Manthanam project structure and web platform foundation.

