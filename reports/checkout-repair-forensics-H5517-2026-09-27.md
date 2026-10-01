# Checkout repair forensics — shared SamudraManthanam checkout (H5517)

_Created: 27-09-2026 · Last updated: 27-09-2026_

## Incident (from GTD @DO 24-09-2026, unit H5517)

The shared checkout `C:/Users/user/Documents/GitHub/SamudraManthanam` was found with the whole
tree staged-deleted, a 2-day-old 0-byte `index.lock` (dated 2026-09-22 16:41, removed 24-09), and
HEAD behind origin/main (`6b66aaa` vs `68a2b9e+`). Rescue snapshots `fd02dee` and `3048f67`
(H4357, "dirty snapshot … tree untouched") were the candidate sole copies of uncommitted WIP.
Standing recipe: compare the index against the snapshots FIRST, salvage any surviving deltas to a
salvage branch, only then `git reset --hard origin/main` + pull — zero data loss.

## Salvage analysis (executed 27-09-2026, OxAlpha/glm-5.3-flash)

Both rescue snapshots were diffed against their base and against `origin/main`:

| Object | Diff vs parent `6b66aaa` | Files with added lines | Verdict |
|---|---|---|---|
| `fd02dee` (rescue 2026-09-24T03:25Z) | pure deletions | **0** | captured the already staged-deleted tree |
| `3048f67` (rescue 2026-09-23T20:51Z) | pure deletions | **0** | same |
| `d97cf51` (dangling, rescue 2026-09-23T18:31Z) | pure deletions | **0** | same — third snapshot of the same state |

Evidence commands: `git diff --numstat 6b66aaa fd02dee | awk '$1>0'` → 0 rows; same for `3048f67`.
Both snapshots and `6b66aaa` are reachable; `6b66aaa` IS an ancestor of `origin/main`
(`git merge-base --is-ancestor` → YES), so every file deleted in the snapshots survives in
`origin/main` history.

Dangling-object sweep (`git fsck --dangling`): one dangling blob `550b2ec7` — a 147 KB
conflict-marker scratch of `CHANGELOG.md` (`<<<<<<< HEAD`) whose unique entries (H4715 name-glossary
join, H4254 release-envelope-v1 adoption) are both present in `origin/main:CHANGELOG.md`
(`git grep -c` → 1 match each). Superseded; nothing lost.

## Verdict: EMPTY DIFF — no salvage branch needed

Zero surviving deltas existed in either snapshot or among dangling objects: the rescue mechanism
had snapshotted the index in its post-deletion state, so there was no WIP content to rescue. The
reset half of the recipe (`git reset --hard origin/main` + pull) had already been applied by the
time this unit ran; this unit verified the salvage question end-to-end and records the explicit
empty-diff note required by the H5517 acceptance clause.

## Post-repair state (verified 27-09-2026)

- `git status` → working tree clean, branch `main` up to date with `origin/main`.
- HEAD == `origin/main` == `d6e7d7438afe2b4946f8c6b19e7d7e8bdb40229e` (H5426, PR #374);
  `git rev-list --left-right --count origin/main...HEAD` → `0  0`.
- All four missing-on-disk E015 units are back on disk, byte-identical to `origin/main`
  (clean status over tracked files proves byte parity):
  1. `ARCHITECTURE_REVIEW_6_MONTH_ROADMAP.md`
  2. `ROADMAP_2026_H2_DH_MOBILE.md`
  3. `docs/ROADMAP_SAMUDRAMANTHANAM_2026_2027.md`
  4. `docs/ROADMAP_SAMUDRAMANTHANAM_RESIDUAL_2026H2.md`

Unblocks the E015 roadmap-verdict units that were re-doing per-file forensics against this checkout.

_Гасунс_
