# Local-only data inventory

_Recorded: 19-07-2026. Sizes are metadata-only measurements rounded to MiB; file
contents were not reviewed during audit hardening._

These paths are intentionally local and must never be staged by a broad Git add.
The corpus-distribution policy finding is documented separately as `[IGNORE]`;
this operational inventory does not reopen it or add a release gate.

| Exact repository path | Purpose | Approx. size | Provenance / source | Regeneration status | Backup status |
|---|---|---:|---|---|---|
| `GRETIL-1_sanskr/2_epic/` | Local Sanskrit epic inputs used by GRETIL conversion work. | 2.7 MiB (7 files) | Local subset of the GRETIL Sanskrit distribution; the exact acquisition event is not recorded in Git. | Reacquirable from the same upstream distribution in principle; byte-identical regeneration is not documented. | Not verified in this pass. |
| `GRETIL-1_sanskr/corpustei/` | Local TEI corpus input for GRETIL converters. | 4.0 MiB (1 file) | GRETIL corpus/TEI distribution; exact acquisition event is not recorded in Git. | Reacquirable in principle; byte-identical regeneration is not documented. | Not verified in this pass. |
| `archive_ignatiev_2026/` | 2026 working archive/snapshot for the Ignatiev/DBhP ingestion lane. | 490.6 MiB (214 files) | Local project archive assembled during the 2026 ingest work; no canonical remote bundle is registered. | Treat as non-regenerable until a manifest and source recipe are recorded. | Not verified; needs an owner-confirmed external backup before deletion is ever considered. |
| `archive_anatoly_mbh_word/` | Anatoly Drive «Для Пахтания» Word dumps (MBH articles, comments, indexes) + pandoc extracts. Gitignored. | ~8 MiB | Shared Google Drive folder `1m1tDLvWJu4DrK9-q0DVbAfnNaLiiLC8Y`. Canonical copies stay on Drive. | Re-download via `gdown` of the four file ids in [H2738 census](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/H2738_MBH_WORD_ARTICLES_INDEXES.md). | Drive original is the backup. |
| `nkrya-parallel/marsel/` | Local Marsel/Rubanova НКРЯ pipeline handoff material and upstream workspace. | 52.2 MiB (5 files) | Material supplied from Marsel's continuation of E. A. Rubanova's pipeline; tracked documentation records the delivered lineage. | The production port and key outputs are tracked, but this local bundle is not reproducibly regenerated from Git. | Not verified in this pass. |
| `_pytest_tmp_samudra/` | Pytest temporary/basetemp workspace. | Not measurable (directory access denied during census) | Generated locally by test execution. | Fully disposable and regenerable by pytest. | Not applicable. |

Backup status is deliberately conservative: “not verified” means this audit found
no repository evidence of a separate backup and did not inspect external drives,
cloud storage, or the directory contents.
