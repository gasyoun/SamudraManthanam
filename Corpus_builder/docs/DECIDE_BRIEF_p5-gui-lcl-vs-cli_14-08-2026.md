# @DECIDE brief — Corpus_builder Phase 5: keep the LCL GUI or go CLI + light web

_Created: 14-08-2026 · Last updated: 14-08-2026_

**Source:** [H2435 (Grok 4.6) — Corpus_builder Phase 5: human DECIDE GUI LCL vs CLI-only](https://github.com/gasyoun/Uprava/blob/main/handoffs/archive/H2435-Grok_SamudraManthanam_corpus-builder-p5-gui-fate-decide_08.08.26.md) · Grok 4.6 (`grok-4.6`)

**Hub copy (same text):** [Uprava/decide_briefs/DECIDE_BRIEF_corpus-builder-p5-gui-fate_14-08-2026.md](https://github.com/gasyoun/Uprava/blob/main/decide_briefs/DECIDE_BRIEF_corpus-builder-p5-gui-fate_14-08-2026.md)

**Human 14-08-2026 (second pass):** `cb.exe` as translator — **nobody**. Rebuilds — **yes**, via Python recipes; `01/02/03` folder still unknown. Book is a bundle. Catalog: [KATALOG_KOMBINACIJ_SBORKI_KORPUSA.md](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/KATALOG_KOMBINACIJ_SBORKI_KORPUSA.md).

This is a **recommendation, not a ruling**. A human decides. No GUI file was deleted.

## Decision

After headless CLI exists, does Corpus Builder keep its Lazarus desktop window (option A) or drop the desktop app for CLI + a new light web (option B)?

## Context

[Corpus_builder/ROADMAP.md](https://github.com/gasyoun/SamudraManthanam/blob/main/Corpus_builder/ROADMAP.md) Phase 5 is an explicit human fork: A = keep the LCL GUI for translators who want an integrity-check window before a build; B = collapse to CLI + a light web and put integrity checks in that CLI. The roadmap says the human writes the ruling when the queue reaches it.

Phases 0–4 of the Lazarus port are done. Soft dependency [H2432 (Grok 4.5) — Corpus_builder Phase 4: headless CLI cb --build](https://github.com/gasyoun/Uprava/blob/main/handoffs/archive/H2432-Grok_SamudraManthanam_corpus-builder-p4-cli-headless-build_08.08.26.md) shipped, so B is a real option rather than a wish.

The desktop builder is the **historical** HTML compiler (`01_Sanskrit.txt` / `02_Transl.txt` / `03_Comments.txt` → `Data/*.html`). New Ignatiev/PDF titles already ingest through the Python pipeline ([H534 note in the same ROADMAP](https://github.com/gasyoun/SamudraManthanam/blob/main/Corpus_builder/ROADMAP.md)), not through `cb`. The two paths are not substitutes for the same books.

## Evidence (verified 14-08-2026)

| Fact | Where | Why it matters |
|---|---|---|
| Headless CLI exists: `cb_headless --build <config.ini\|dir> [--out html] [--check]` | [H2432](https://github.com/gasyoun/Uprava/blob/main/handoffs/archive/H2432-Grok_SamudraManthanam_corpus-builder-p4-cli-headless-build_08.08.26.md) · [SamudraManthanam PR #201](https://github.com/gasyoun/SamudraManthanam/pull/201) · [docs/H2432_CLI_HEADLESS_BUILD.md](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/H2432_CLI_HEADLESS_BUILD.md) · [cb_headless.lpr](https://github.com/gasyoun/SamudraManthanam/blob/main/Corpus_builder/PSRCBuilder/cb_headless.lpr) (222 lines) | B's "can we build without a window?" is already yes. |
| `--check` already runs `TOKBottomDlg.CheckAll` and writes `_err.txt` / `_check.json` / `_check.tsv` | same `cb_headless.lpr` · [README § Headless CLI](https://github.com/gasyoun/SamudraManthanam/blob/main/Corpus_builder/README.md) | B's "put integrity checks in the CLI" is already done. |
| CLI Confirm is **auto-yes** (never a modal) | `TCLIHost.Confirm` in `cb_headless.lpr` | A translator cannot refuse a confirm from the CLI. The window still can (`MessageDlg` in [fMainForm.pas](https://github.com/gasyoun/SamudraManthanam/blob/main/Corpus_builder/PSRCBuilder/fMainForm.pas) `BuilderConfirm`). |
| Web-pipeline hook exists (optional jobs JSONL, skip-if-absent) | [H2433 (Grok 4.5) — Phase 4 web-pipeline hook](https://github.com/gasyoun/Uprava/blob/main/handoffs/archive/H2433-Grok_SamudraManthanam_corpus-builder-p4-web-pipeline-hook_08.08.26.md) · [PR #263](https://github.com/gasyoun/SamudraManthanam/pull/263) · [docs/H2433_WEB_PIPELINE_HOOK.md](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/H2433_WEB_PIPELINE_HOOK.md) | Prod cron is unchanged when no jobs file is present. |
| Golden CI builds `cb_headless` on Linux and byte-compares case01 | [H2434](https://github.com/gasyoun/Uprava/blob/main/handoffs/archive/H2434-Grok_SamudraManthanam_corpus-builder-p4-ci-job-fpc-golden_08.08.26.md) · PRs [#264](https://github.com/gasyoun/SamudraManthanam/pull/264)–[#267](https://github.com/gasyoun/SamudraManthanam/pull/267) · [corpus-builder-golden.yml](https://github.com/gasyoun/SamudraManthanam/blob/main/.github/workflows/corpus-builder-golden.yml) | CI does not need a desktop window. |
| Multi-book split / concat still lives **only** in the form | [ARCHITECTURE.md](https://github.com/gasyoun/SamudraManthanam/blob/main/Corpus_builder/ARCHITECTURE.md) §1.2–1.3, §2.1.2, §3 · `PrepareBook` / `ConcatAllHTMLFiles` / `PutFile1ToFile2` in [fMainForm.pas](https://github.com/gasyoun/SamudraManthanam/blob/main/Corpus_builder/PSRCBuilder/fMainForm.pas) (1,584 lines) | Deleting the GUI **now** drops the only multi-book rebuild path. That extract is a named Phase 4 residual, not Phase 5. |
| Target architecture still draws **three** thin frontends: CLI + LCL GUI + CI | [ARCHITECTURE.md](https://github.com/gasyoun/SamudraManthanam/blob/main/Corpus_builder/ARCHITECTURE.md) §2 | Option A is the already-written to-be, not a nostalgia add-on. |
| LCL GUI already ports and builds (`cb.lpi`, `.lfm` forms, Linux CI) | [H2417](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/H2417_PHASE3_LAZARUS_PORT.md) · [H2431](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/H2431_LINUX_LAZBUILD.md) | Keeping A is not "finish a Delphi port". The port is done; the cost of A is maintenance, not a rewrite. |
| New-text ingest already has a Python path | ROADMAP H534 banner · [PDF_INGESTION_PIPELINE.md](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/PDF_INGESTION_PIPELINE.md) | B is not required to ingest *new* books. `cb` is for reproducing historical GUI logic and rebuilding already-loaded sources. |
| No light-web builder exists | grep of `web/` + `Corpus_builder/` — no builder UI route | B is not "flip a flag". It is a new product surface (auth, file upload, check report, job queue). |
| ROADMAP Phase 4 "стык с веб-конвейером" checkbox is still `[ ]` even though H2433 shipped | [ROADMAP.md](https://github.com/gasyoun/SamudraManthanam/blob/main/Corpus_builder/ROADMAP.md) Фаза 4 | Stale checkbox, not a missing hook. Do not treat it as a reason to delay this ruling. |
| Who last launched the desktop `cb` window is **unmeasured** | no telemetry, no dated operator log in `OPS.md` | The "translators need the window" claim is the roadmap's premise, not a counted fact. |

### Clone census (14-08-2026, same session, after the human deferral)

| Fact | Number | Why it matters |
|---|---|---|
| Live `01_Sanskrit.txt` / `02_Transl.txt` / `03_Comments.txt` triples in the clone | **1** — only [tests/golden/case01/input/](https://github.com/gasyoun/SamudraManthanam/tree/main/Corpus_builder/tests/golden/case01/input) | No authoring workspace is checked in. |
| `ManyBooks_01_Sanskrit.txt` / `many_books_config.ini` | **0** in Corpus_builder, `web/corpus_builder`, Programdata, and `Index/.../Data` | The MultiBook path has no on-disk input in this clone. |
| Local Lazarus `lib/x86_64-win64/cb.exe` and `cb_headless.exe` | **absent** (`lib/` is gitignored and empty here) | This machine is not currently running the windowed or headless binary. |
| Committed Delphi `PSRCBuilder/cb.exe` | 522,240 bytes, mtime **2026-05-14** | Last rebuilt before the Lazarus port; not evidence of a 2026-08 launch. |
| `fMainForm.pas` history since first commit (15-05-2026) | H1485, H2417, H2428, H2431 only | Port/maintenance commits, not translator feature requests. |
| Python ingest vs published HTML | **269** `.jsonl` under `web/corpus_builder/jsonl/` (749 MB) · **193** `.html` under `Index/.../Data` (199 MB) | New titles already go through [PDF_INGESTION_PIPELINE.md](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/PDF_INGESTION_PIPELINE.md). |
| Still unmeasured (outside this clone) | a private disk / old Windows box / translator laptop | Only a human can say whether such a folder exists. |

## Options

### A — Keep the desktop GUI on LCL

**What it unblocks.** Translators keep the window (open config, run "Проверка_Перевода", see memos, refuse a Confirm). Multi-book rebuild keeps working. Target architecture stays honest. No new product to design.

**What it forecloses.** A future "one web tool for everyone" is delayed. Two binaries (`cb` + `cb_headless`) stay in the tree. LCL remains a compile dependency for the windowed target.

**Effort / risk.** Near zero now (forms already ported). Ongoing: do not put new logic in `fMainForm`; extract MultiBook when someone next rebuilds a many-book corpus from CLI. Reversible later: B can still be chosen after MultiBook is in the core.

**Cost if wrong.** A few years of a desktop binary almost nobody opens, while CLI + Python do the real work.

### B — CLI only + a light web; drop the desktop app

**What it unblocks.** One operator story (script or browser). No LCL on translator machines. Integrity reports stay the existing `_check.json` / `_check.tsv`. Fits CI and the web hook already shipped.

**What it forecloses.** Multi-book rebuild **until** `PrepareBook` / `ConcatAllHTMLFiles` move into a core `MultiBook` unit (ARCHITECTURE §2.1.2). Interactive Confirm. IAST / danda / Valmiki helper menu items that still live only on the form. A translator who works offline with a `.ini` next to three `.txt` files.

**Effort / risk.** Medium–heavy: design a web UI, wire it to `cb_headless` or the Python ingest, decide auth (this is an authoring tool, not public search), and extract MultiBook first or lose that path. High risk of a half-built web that nobody prefers to the CLI they already have.

**Cost if wrong.** Rebuild the LCL forms from git history; the `.lfm` / `.pas` are cheap to keep and expensive to recreate from a translator's memory.

### C — Status quo / do nothing (keep files, spend nothing)

Leave `cb.lpi` and `cb_headless.lpi` as they are. No deletion, no new web, no new GUI features. Next engineering unit remains MultiBook-into-core (already a Phase 4 residual).

This is A without a "first-class product" promise. It is the cheap default if a human does not want to think about translators this week. It is **not** B.

### D — Delete the GUI now (the option that looks clean and is wrong)

Remove `cb.lpr` / `fMainForm` / `fCheckDialog` because CLI + CI exist. This is the handoff's explicit fail ("removing GUI without human ruling") and it is also substantively wrong: MultiBook has no other host. Listed so the next session does not re-propose it.

## Recommendation

**No A/B pick.** Labelled as a recommendation, not a ruling. The human said there is not enough data; the clone census confirms that. Default until the two facts exist: **C** (keep the files, spend nothing, do not delete).

The two facts that would make A vs B decidable:

1. Does anyone still have a **private** `01_Sanskrit.txt` / `02_Transl.txt` / `03_Comments.txt` (or `ManyBooks_*`) folder they open in desktop `cb`?
2. Will any of the 193 `Data/*.html` titles be **rebuilt via `cb`**, or only via the Python ingest?

- If (1) is yes → A.
- If (1) is no **and** (2) is "Python only" → B is cheap, or C forever.
- If (1) is "maybe, on another disk" → still C; do not delete.

**Confidence: high** that the *clone* cannot settle A vs B. **Confidence: none** on private disks.

**If a human is away and this sits:** nothing is blocked. CLI, CI, Python ingest, and prod reindex keep working. The only frozen thing is deletion of the window.

_Dr. Mārcis Gasūns_
