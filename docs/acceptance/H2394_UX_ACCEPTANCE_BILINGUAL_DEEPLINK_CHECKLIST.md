# H2394 — P9 UX acceptance: bilingual Sa+Ru + deep-link on prod

_Created: 08-08-2026 · Last updated: 08-08-2026_

**Handoff:** [H2394-Grok_SamudraManthanam_prod-ux-acceptance-bilingual-deeplink_07.08.26](https://github.com/gasyoun/Uprava/blob/main/handoffs/H2394-Grok_SamudraManthanam_prod-ux-acceptance-bilingual-deeplink_07.08.26.md)  
**Executor:** Grok 4.5 (`grok-4.5`)  
**Prod base:** [https://samudra.193.232.229.92.sslip.io/](https://samudra.193.232.229.92.sslip.io/)  
**Corpus at probe time:** `2026.08`, **230** sources (`GET /api/health`)  
**Reproduce:** `python docs/acceptance/h2394_prod_ux_probe.py`  
**Machine evidence:** [H2394_prod_ux_probe_results.json](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/acceptance/H2394_prod_ux_probe_results.json)

## Verdict

**PASS — 11/11 probes green.** Fail gate (“fails on vishnu-smriti or similar parallel”) did **not** fire.

## Acceptance criteria

| Criterion | Result | Evidence |
|---|---|---|
| Bilingual Sa+Ru visible on parallel search hit | **PASS** | `chapter_block iast` + `chapter_block translation` + Cyrillic on `vishnu-smriti` / `yajnavalkyasmriti` hits |
| Deep-link opens correct line | **PASS** | `/sources/{slug}/anchor/{link_id}` → **302** `?highlight={link_id}`; reader marks matching `.line-row.highlighted` with `data-link-id` |
| Flex CSS still served on prod | **PASS** | `/static/style.css` contains flex rules for `.chapter_block.iast` / `.translation` |
| Stop after ≤10 content probes | **PASS** | P1–P10 (+ free P0 health) |

## Probe table

| ID | Probe | Pass | Detail |
|---|---|---|---|
| P0 | health ok | yes | sources=230 ver=2026.08 |
| P1 | bilingual flex CSS served | yes | flex + iast/translation selectors |
| P2 | vishnu-smriti search hit Sa+Ru | yes | `link_id=c1.p1` (IAST + RU Корнеева) |
| P3 | `html_fragment` bilingual | yes | frag includes both blocks |
| P4 | anchor deep-link 302 | yes | → `/sources/vishnu-smriti?highlight=c1.p1` |
| P5 | reader `?highlight=` correct line | yes | `data-link-id=c1.p1` row highlighted |
| P6 | reader page bilingual + lang toolbar | yes | Sa/Ru/Оба toolbar present |
| P7 | yajnavalkyasmriti parallel bilingual | yes | `link_id=c2.p1` |
| P8 | yajnavalkya deep-link open+highlight | yes | 302 + highlighted |
| P9 | rigveda deep-link lands | yes | `?highlight=1.1` → highlighted (merged Sa+Ru) |
| P10 | RU query «дхарма» → parallel bilingual | yes | first hit may be monoglot front-matter (`p1`); first true `citation_block` hit (`c1.p5`) is bilingual |

## Sample URLs

1. Anchor deep-link (vishnu-smriti c1.p1):  
   [https://samudra.193.232.229.92.sslip.io/sources/vishnu-smriti/anchor/c1.p1](https://samudra.193.232.229.92.sslip.io/sources/vishnu-smriti/anchor/c1.p1)
2. Reader highlight (same line):  
   [https://samudra.193.232.229.92.sslip.io/sources/vishnu-smriti?highlight=c1.p1](https://samudra.193.232.229.92.sslip.io/sources/vishnu-smriti?highlight=c1.p1)
3. Yājñavalkya-smṛti deep-link:  
   [https://samudra.193.232.229.92.sslip.io/sources/yajnavalkyasmriti/anchor/c2.p1](https://samudra.193.232.229.92.sslip.io/sources/yajnavalkyasmriti/anchor/c2.p1)
4. Ṛgveda deep-link:  
   [https://samudra.193.232.229.92.sslip.io/sources/01_rigveda?highlight=1.1](https://samudra.193.232.229.92.sslip.io/sources/01_rigveda?highlight=1.1)
5. Health:  
   [https://samudra.193.232.229.92.sslip.io/api/health](https://samudra.193.232.229.92.sslip.io/api/health)

## Vishnu-smṛti sample (P2)

| Side | Snippet |
|---|---|
| Sa (IAST) | `brahmarātryāṃ vyatītāyāṃ prabuddhe padmasaṃbhave… // ViS_1.1` |
| Ru | `Когда ночь Брахмы закончилась и Падмасамбхава пробудился, Вишну пожелал творить живые существа…` |

## Caveats (not FAIL)

- **RU query front-matter first hit:** searching «дхарма» on `vishnu-smriti` can return `link_id=p1` (title/preface HTML without `chapter_block iast|translation`). Parallel citation rows still render Sa+Ru. Documented in P10; not a bilingual-layout defect.
- **JSONL segment sources** (e.g. `01_rigveda`): search API may return a single `#sa` segment row; the **reader** merge still shows Sa+Ru side-by-side after deep-link (P9).
- **No screenshot capture** in this pass — HTML/CSS asserts + redirect/highlight markers satisfy the handoff “curl+HTML asserts” option.

## Roadmap tick

Wave P unit **P9** in [ROADMAP_SAMUDRAMANTHANAM_2026_2027.md](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/ROADMAP_SAMUDRAMANTHANAM_2026_2027.md): UX acceptance bilingual + deep-link on prod → **checklist green** (this file).

_Dr. Mārcis Gasūns_
