# CORPUS BUNDLE SPEC — canonical manifest and immutable bundle

_Created: 05-08-2026 · Last updated: 05-08-2026_

Lane A of
[PLAN_SAMUDRAMANTHANAM_ARCHITECTURE_2026_2027.md](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/PLAN_SAMUDRAMANTHANAM_ARCHITECTURE_2026_2027.md).
Ordered steps: [IMPLEMENTATION_SAMUDRAMANTHANAM_ARCHITECTURE_INTEGRITY.md](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/IMPLEMENTATION_SAMUDRAMANTHANAM_ARCHITECTURE_INTEGRITY.md)
§Lane A · acceptance: [VERIFICATION_SAMUDRAMANTHANAM_ARCHITECTURE_INTEGRITY.md](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/VERIFICATION_SAMUDRAMANTHANAM_ARCHITECTURE_INTEGRITY.md)
§Lane A (A1–A7).

## 1. What a bundle is

A **bundle** is one immutable set of canonical JSONL files plus the manifest
that enumerates them. Everything the platform ships — the web `corpus.db`, the
offline packs, the desktop HTML and its `.no_tags` sidecars — is a **generated
view** of exactly one bundle.

Before this spec, the enumeration of record was
[web/../Programdata/data.txt](https://github.com/gasyoun/SamudraManthanam/blob/main/web/ingest/ingest.py):
a bare list of legacy HTML filenames. That list can say *which* sources exist.
It cannot say *what they contain*, so nothing in the pipeline could tell a
correct corpus from a corrupted one, and no artifact could name the corpus it
came from. The manifest closes both gaps.

| Concern | Before | Now |
|---|---|---|
| Enumeration | `Programdata/data.txt` (HTML filenames) | manifest `bundle.sources` |
| Content integrity | none | SHA-256 + byte count + record count per file |
| What publish validated | the legacy HTML tree | the JSONL actually published |
| Corpus identity | a build-date string | `content_hash` over the bundle |
| Artifact lineage | none | build report naming `input_manifest_hash` |

## 2. Files

| Path | Role |
|---|---|
| [web/corpus_builder/manifest/schema-v1.json](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/manifest/schema-v1.json) | JSON Schema (draft 2020-12) — the single validator |
| [web/corpus_builder/manifest/corpus-manifest.fixture.json](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/manifest/corpus-manifest.fixture.json) | Worked example, validated by the test suite against its real files |
| [web/corpus_builder/corpus_manifest.py](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/corpus_manifest.py) | `build` · `validate` · `diff` |
| [web/corpus_builder/build_report.py](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/build_report.py) | Generated-view registration |
| [web/ingest/artifact_resolver.py](https://github.com/gasyoun/SamudraManthanam/blob/main/web/ingest/artifact_resolver.py) | Checksum-pinned fetch for off-git objects |
| [web/tests/fixtures/corpus_bundle/](https://github.com/gasyoun/SamudraManthanam/tree/main/web/tests/fixtures/corpus_bundle) | Hermetic JSONL fixtures |

## 3. Manifest shape

```text
{
  "schema_version": 1,
  "bundle": {
    "bundle_version": "2026.08",
    "corpus_root": "web",
    "sources": [ { … } ],
    "generated_artifacts": [ {"name": "base.db", "kind": "offline-pack", "required": true} ],
    "totals": {"source_count": 197, "record_count": 703726, "canonical_bytes": 0}
  },
  "build": {"generator": "corpus_manifest/1", "revision": "<git sha>"},
  "content_hash": "sha256:…"
}
```

Each entry of `bundle.sources` carries identity (`slug`, `filename`,
`sort_order`, `title`), required `provenance`, optional `rights`, and a
`canonical` block naming the JSONL with `path`, `sha256`, `bytes`,
`record_count`, and the first/last canonical id. Optional `source_file` and
`metadata` blocks reference the legacy HTML view and the `.meta.json` sidecar.

### 3.1 Why there is no timestamp

`bundle` is a pure function of its inputs. A `generated_at` field would make
every rebuild a different document, which would destroy both criterion A2
(byte-identical rebuilds) and the usefulness of `content_hash` as an identity.

**A manifest records what a bundle is; a build report records when something was
made from it.** Event time therefore lives in build reports only. A test asserts
that no clock-shaped key ever appears in a manifest, so this cannot regress by
someone helpfully adding one.

### 3.2 `content_hash` covers `bundle` only

`content_hash` is SHA-256 over the canonical serialization (sorted keys, 2-space
indent, no ASCII escaping, LF, trailing newline) of the `bundle` object alone —
not of `build`. So rebuilding identical content at a new git revision yields the
same content hash. That is what lets a web DB, an offline pack, and a desktop
view produced weeks apart still name one input (criterion A6).

### 3.3 Path rules

Every `path` is relative to `bundle.corpus_root` (itself relative to the
repository root), POSIX-separated, with absolute paths and `..` traversal
rejected by the schema. A manifest built on Windows validates byte-for-byte on a
Linux runner.

### 3.4 What is not a source

The canonical JSONL directory also holds converter intermediates —
`<slug>.raw.jsonl`, `<slug>.aligned.jsonl`. They are inputs to the converter,
not publishable sources, and are recognised by their multi-part suffix and
excluded. **Every exclusion is printed by name.** A bundle that silently drops or
silently absorbs a file is the failure this manifest exists to prevent, so the
omission is always announced rather than inferred from a count.

## 4. Commands

```text
python corpus_builder/corpus_manifest.py build \
    --corpus-path <corpus tree> --bundle-version 2026.08 \
    --out corpus_builder/manifest/corpus-manifest.json

python corpus_builder/corpus_manifest.py validate <manifest>      # hashes every file
python corpus_builder/corpus_manifest.py validate <manifest> --no-files   # structure only
python corpus_builder/corpus_manifest.py diff <old> <new> [--json] [--fail-on-change]
```

`build` takes source order and legacy filenames from `Programdata/data.txt` when
`--corpus-path` is given, and falls back to the canonical JSONL directory
otherwise. Everything else — identity, content, counts — always comes from the
JSONL.

Publication consumes the manifest:

```text
python ingest/publish.py --manifest <manifest> --db-path corpus.db
python ingest/publish.py --rollback-from backups/corpus_20260805_101500.db --db-path corpus.db
```

Without `--manifest`, `publish` falls back to the legacy HTML-tree check and
**says so in its output** — that path does not hash the bytes it publishes.

## 5. Publication contract

1. `validate_bundle` opens and hashes every canonical JSONL the manifest names.
2. `ingest` re-verifies each hash before inserting a row, and rejects a manifest
   whose declared `record_count` disagrees with what it actually inserted.
3. Ingest writes `input_manifest_hash` and `bundle_version` into `corpus_meta`;
   `corpus_version` becomes the bundle version, not a build date.
4. Integrity check, smoke check, backup, atomic swap.
5. A build report is written naming the input manifest hash.

Any abort before step 4 leaves the live database untouched. `restore_backup()`
re-activates a previous bundle from the copy step 4 wrote, refusing a backup
that fails its own integrity check (criterion A7).

## 6. Generated-view registration

A build report ties one derivative to one bundle:

```text
{
  "report_version": 1,
  "artifact": {"name": "base.db", "kind": "offline-pack"},
  "input_manifest": {"content_hash": "sha256:…", "bundle_version": "2026.08", …},
  "outputs": [{"name": "base.db", "sha256": "…", "bytes": 1234, "record_count": 703726}],
  "counts": {"sources": 197, "rows": 703726},
  "generator": "build_offline_pack/1",
  "generated_at": "2026-08-05T10:15:00+00:00"
}
```

Registered generators today:

| Generator | Kind | How it learns the input hash |
|---|---|---|
| [ingest/publish.py](https://github.com/gasyoun/SamudraManthanam/blob/main/web/ingest/publish.py) | `web-db` | from the manifest it published |
| [scripts/build_offline_pack.py](https://github.com/gasyoun/SamudraManthanam/blob/main/web/scripts/build_offline_pack.py) | `offline-pack` | inherited from `corpus.db`'s `corpus_meta` |
| [corpus_builder/build_corpus_html.py](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/build_corpus_html.py) | `desktop-view` | from `--manifest` |

A generator whose source database carries no `input_manifest_hash` is **refused**
rather than given a placeholder: a derivative of an unregistered corpus must not
fabricate a lineage.

`bundle.generated_artifacts` declares the views a bundle is *expected* to
produce. Actual output hashes are never written back into the manifest — that
would make the manifest depend on its own consumers.

## 7. Artifact resolution

Large immutable objects that do not live in git are fetched by
`resolve_artifact(uri, expected_sha256, dest_dir)`:

- staged to a temporary file, hashed there, and moved into place **only** after
  the digest matches — nothing extracts or opens an unverified download;
- `file://`, bare filesystem paths, and `http(s)://` behind one `Transport`
  interface, so no vendor SDK is on the critical path and tests exercise the
  same verification code as production;
- a cached copy is **re-hashed, never trusted**, so a file that rotted on disk is
  refetched;
- every URL in a log line or exception passes through `redact_url`. Object
  stores authenticate with pre-signed query strings, so an un-redacted URL in a
  build log is a leaked credential.
- `extract_verified` takes a `ResolvedArtifact`, not a path — there is no way to
  extract something that was never verified — and refuses archive members that
  escape the destination or are links.

## 8. Measured behaviour

Against the real canonical JSONL directory (05-08-2026, Opus 5
(`claude-opus-5`), Windows 10, Python 3.14):

| Measurement | Value |
|---|---|
| Sources enumerated | 197 (22 pipeline intermediates excluded and named) |
| Records | 703,726 |
| Two builds byte-identical | yes |
| Full validation, hashing every file | 3.1 s |
| Hermetic Lane-A tests | 59 (34 manifest + 25 resolver) |

Validation is a single streamed pass per file, meeting the plan's budget of
linear-in-bundle-bytes with no duplicate full-file reads.

## 9. Limits, stated rather than implied

- **Sources ≠ the full JSONL directory.** 197 of 219 `.jsonl` files are
  publishable sources; the rest are converter intermediates. That split is
  printed on every build, not inferred.
- **The legacy `data.txt` path still exists.** Bundles without a manifest can
  still be published, and that path cannot verify content. It warns; it is not
  yet removed. Removing it is Lane B/D work, once every consumer is
  manifest-driven.
- **`generated_artifacts` is an expectation, not a gate.** Nothing yet fails a
  build because a `required: true` view was not produced; the full corpus-changing
  workflow that would enforce it is Lane D (D5/D6).
- **Rights are recorded, not adjudicated.** A `rights` field carries known facts.
  Its absence means *not yet recorded*, never *unrestricted*.

## 10. Downstream lanes

- **Lane B ([H1925](https://github.com/gasyoun/Uprava/blob/main/handoffs/H1925-Opus_SamudraManthanam_durable-reference-zero-orphan_30.07.26.md))**
  consumes the identity fields this spec fixes: `slug` (as `source_slug`),
  `canonical_id`, and `bundle_version` (as `corpus_version`) are the canonical
  tuple it propagates. `corpus_meta.input_manifest_hash` is the pin its
  zero-orphan report should compare across.
- **Lane D ([H1927](https://github.com/gasyoun/Uprava/blob/main/handoffs/H1927-Opus_SamudraManthanam_runtime-migrations-dual-deploy_30.07.26.md))**
  consumes `resolve_artifact` for the pinned-bundle workflow, and
  `bundle_version` / `input_manifest_hash` for the deployment smoke's
  version-exposure check.
- **Lanes E/F** register accepted output through `corpus_manifest.py build` and
  gate on `diff --fail-on-change`.

_Dr. Mārcis Gasūns_
