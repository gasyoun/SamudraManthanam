# CORPUS_BUNDLE_SPEC.md — metadoc

_Created: 05-08-2026 · Last updated: 05-08-2026_

Companion record for
[CORPUS_BUNDLE_SPEC.md](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/CORPUS_BUNDLE_SPEC.md).

## Purpose

Defines the corpus bundle contract: what a bundle is, what its manifest must
contain, how publication verifies it, and how every generated view is tied back
to the bundle it came from. It is the document a session reads before touching
ingest, publish, the offline-pack builder, or the desktop emitter.

## Audience

Agents and maintainers working on the corpus pipeline. Not user-facing; assumes
familiarity with the canonical JSONL format and the FastAPI/SQLite platform.

## Provenance

- Handoff: [H1924](https://github.com/gasyoun/Uprava/blob/main/handoffs/H1924-Opus_SamudraManthanam_canonical-manifest-artifact-bundle_30.07.26.md)
  (**Opus 5**) — canonical manifest and immutable corpus bundle, Wave-1 Lane A.
- Executed by Opus 5 (`claude-opus-5`), 05-08-2026.
- Source plan: [PLAN_SAMUDRAMANTHANAM_ARCHITECTURE_2026_2027.md](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/PLAN_SAMUDRAMANTHANAM_ARCHITECTURE_2026_2027.md)
  Lane A; acceptance criteria A1–A7 in
  [VERIFICATION_SAMUDRAMANTHANAM_ARCHITECTURE_INTEGRITY.md](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/VERIFICATION_SAMUDRAMANTHANAM_ARCHITECTURE_INTEGRITY.md).
- Prior-art check before building: repo-wide grep for existing manifest code
  (none — `data.txt` was the only "manifest"), and
  `Uprava/tools/hub_grep.py "corpus manifest checksum bundle resolver"` returned
  no hits. The org's [kosha datasets.json](https://github.com/gasyoun/kosha/blob/main/data/manifest/datasets.json)
  is a *publication* registry for cross-repo datasets, a different concern from
  an intra-repo build bundle; it is a registration target, not a substitute.

## Ranked improvement backlog

1. **Make `generated_artifacts` a gate.** It currently declares expectations that
   nothing enforces; a `required: true` view can go unproduced silently. Belongs
   with Lane D's full corpus-changing workflow (D5/D6).
2. **Retire the `data.txt` publication path.** It still permits publishing bytes
   that were never hashed. Removable once Lane B/D consumers are all
   manifest-driven; until then the fallback warns.
3. **Commit a real bundle manifest.** Only the fixture manifest is checked in.
   A committed production manifest would let CI diff bundle changes per PR.
4. **Per-record identity coverage.** The manifest records first/last canonical id
   per source; a full id census would let Lane B's zero-orphan report resolve
   against the manifest instead of a rebuilt database.
5. **Additional transports.** `s3://` and friends are deliberately absent — add
   as `Transport` subclasses only when a real deployment needs one, never by
   relaxing verification.

## Limitations

- Measured numbers in §8 are from one Windows host (Python 3.14); they are a
  reproducibility check, not a cross-platform performance baseline.
- The spec covers Lane A only. Durable identity (Lane B), bounded regex and
  admin trust (Lane C), and migrations/deployment (Lane D) are separate lanes
  and separate handoffs.
- `rights` fields carry recorded facts only. Per the org standing policy, rights
  uncertainty is not a blocker and this spec does not adjudicate it.

## Revision history

| Date | Change | By |
|---|---|---|
| 05-08-2026 | Created with Lane A implementation (H1924) | Opus 5 (`claude-opus-5`) |

_Dr. Mārcis Gasūns_
