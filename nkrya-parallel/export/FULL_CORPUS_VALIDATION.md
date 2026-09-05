# НКРЯ full-corpus triple-export — validation report (Wave 4)

_Created: 13-07-2026 · Last updated: 13-07-2026_

Full-corpus export of **all 131 seg=ru sources** (the Wave-1 pilot covered 4), via [`web/corpus_builder/nkrya_export.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/nkrya_export.py) `--all-ru --with-sanskritisms` (H821). Each source → best-guess НКРЯ para-XML + TMX 1.4b + TSV + a sanskritisms proper-name index. Bulk artifacts gitignored (in-copyright); shipped as a release. Model: Opus 4.8 (`claude-opus-4-8[1m]`).

## Per-source results

| Source | Pairs | Mono-RU (flagged) | Untransl-SA (flagged) | Commentary (excl.) | Empty side |
|---|---:|---:|---:|---:|---:|
| `01_atharvaveda` | **153** | 0 | 0 | 144 | 0 |
| `01_mahabharata-adiparva` | **1387** | 0 | 0 | 968 | 0 |
| `01_ramayana-balakanda` | **2268** | 0 | 0 | 519 | 0 |
| `01_rigveda` | **1976** | 0 | 0 | 2194 | 0 |
| `02_atharvaveda` | **207** | 0 | 0 | 169 | 0 |
| `02_mahabharata-sabhaparva` | **438** | 0 | 0 | 1256 | 0 |
| `02_ramayana-ayodhyakanda` | **4307** | 0 | 0 | 944 | 0 |
| `02_rigveda` | **429** | 0 | 0 | 449 | 0 |
| `03_atharvaveda` | **230** | 0 | 0 | 199 | 0 |
| `03_mahabharata-aranyakaparva` | **2033** | 0 | 0 | 1319 | 0 |
| `03_ramayana-aranyakanda` | **2447** | 0 | 0 | 694 | 0 |
| `03_rigveda` | **617** | 0 | 0 | 602 | 0 |
| `04_atharvaveda` | **324** | 0 | 0 | 293 | 0 |
| `04_mahabharata-virataparva` | **360** | 0 | 0 | 476 | 0 |
| `04_rigveda` | **589** | 0 | 0 | 645 | 0 |
| `05_atharvaveda` | **376** | 0 | 0 | 288 | 0 |
| `05_mahabharata-udyogaparva` | **1006** | 0 | 0 | 1866 | 0 |
| `05_ramayana-sundarakanda` | **2859** | 0 | 0 | 82 | 0 |
| `05_rigveda` | **725** | 0 | 0 | 878 | 0 |
| `06_atharvaveda` | **454** | 0 | 0 | 412 | 0 |
| `06_mahabharata-bhishmaparva` | **1337** | 0 | 0 | 776 | 0 |
| `06_rigveda` | **765** | 0 | 0 | 744 | 0 |
| `07_atharvaveda` | **286** | 0 | 0 | 333 | 0 |
| `07_mahabharata-dronaparva` | **1219** | 0 | 0 | 1929 | 0 |
| `07_rigveda` | **841** | 0 | 0 | 931 | 0 |
| `08_atharvaveda` | **259** | 0 | 0 | 209 | 0 |
| `08_mahabharata-karnaparva` | **618** | 0 | 0 | 490 | 0 |
| `08_rigveda` | **1716** | 0 | 0 | 1240 | 0 |
| `09_atharvaveda` | **302** | 0 | 0 | 249 | 0 |
| `09_mahabharata-shalyaparva` | **533** | 0 | 0 | 929 | 0 |
| `09_rigveda` | **1108** | 0 | 0 | 1008 | 0 |
| `10_atharvaveda` | **350** | 0 | 0 | 215 | 0 |
| `10_mahabharata-sauptikaparva` | **85** | 0 | 0 | 290 | 0 |
| `10_rigveda` | **1751** | 0 | 0 | 1992 | 0 |
| `11_atharvaveda` | **313** | 0 | 0 | 202 | 0 |
| `11_mahabharata-striparva` | **122** | 0 | 0 | 224 | 0 |
| `12_atharvaveda` | **304** | 0 | 0 | 168 | 0 |
| `12_mahabharata-shantiparva` | **12692** | 0 | 0 | 139 | 0 |
| `13_atharvaveda` | **187** | 0 | 1 | 127 | 0 |
| `13_mahabharata-anushasanaparva` | **6537** | 0 | 0 | 0 | 0 |
| `14_atharvaveda` | **139** | 0 | 0 | 110 | 0 |
| `14_mahabharata-ashvamedhikaparva` | **517** | 0 | 0 | 883 | 0 |
| `15_atharvaveda` | **220** | 0 | 0 | 52 | 0 |
| `15_mahabharata-ashramavasikaparva` | **162** | 0 | 0 | 320 | 0 |
| `16_atharvaveda` | **103** | 0 | 0 | 31 | 0 |
| `16_mahabharata-mausalaparva` | **42** | 0 | 0 | 177 | 0 |
| `17_atharvaveda` | **30** | 0 | 0 | 20 | 0 |
| `17_mahabharata-mahaprasthanikaparva` | **26** | 0 | 0 | 61 | 0 |
| `18_atharvaveda` | **283** | 0 | 0 | 176 | 0 |
| `18_mahabharata-svargarohanikaparva` | **28** | 0 | 0 | 121 | 0 |
| `19_atharvaveda` | **311** | 0 | 0 | 191 | 0 |
| `ait-up` | **33** | 0 | 0 | 26 | 0 |
| `amaru-shataka` | **193** | 0 | 0 | 31 | 0 |
| `atma-up` | **3** | 0 | 0 | 3 | 0 |
| `bhagavadgita-1788` | **697** | 0 | 0 | 124 | 0 |
| `bhagavadgita-1909` | **691** | 0 | 0 | 535 | 0 |
| `bhagavadgita-1914` | **701** | 0 | 0 | 255 | 0 |
| `bhagavadgita-burba` | **719** | 0 | 0 | 593 | 0 |
| `bhagavadgita-erman` | **700** | 0 | 0 | 301 | 0 |
| `bhagavadgita-prabhupada` | **657** | 0 | 0 | 624 | 0 |
| `bhagavadgita-radha` | **647** | 0 | 0 | 1227 | 0 |
| `bhagavadgita-sementsov` | **696** | 0 | 0 | 94 | 0 |
| `bhagavadgita-sharma` | **660** | 0 | 0 | 57 | 0 |
| `bhagavadgita-smirnov` | **700** | 0 | 0 | 589 | 1 |
| `bhagavadgity` | **701** | 0 | 0 | 28 | 0 |
| `br-up` | **438** | 0 | 0 | 346 | 0 |
| `brb-up` | **22** | 0 | 0 | 11 | 0 |
| `buddhacharita` | **1033** | 0 | 0 | 163 | 0 |
| `buddhacharita-balmont` | **0** | 8852 | 0 | 45 | 0 |
| `ch-up` | **628** | 1 | 0 | 462 | 0 |
| `chag-up` | **5** | 0 | 0 | 5 | 0 |
| `chaurapanchashika` | **50** | 0 | 0 | 9 | 0 |
| `devi-gita` | **492** | 0 | 0 | 463 | 0 |
| `devibhagavata-purana-1` | **1180** | 1 | 0 | 429 | 0 |
| `devibhagavata-purana-10` | **501** | 3 | 0 | 188 | 0 |
| `devibhagavata-purana-11` | **1188** | 50 | 0 | 340 | 0 |
| `devibhagavata-purana-12` | **942** | 6 | 0 | 348 | 0 |
| `devibhagavata-purana-2` | **722** | 1 | 0 | 0 | 0 |
| `devibhagavata-purana-3` | **1739** | 5 | 0 | 392 | 0 |
| `devibhagavata-purana-4` | **1395** | 4 | 0 | 285 | 0 |
| `devibhagavata-purana-5` | **2063** | 13 | 0 | 459 | 0 |
| `devibhagavata-purana-6` | **923** | 5 | 0 | 180 | 0 |
| `devibhagavata-purana-7` | **2232** | 11 | 0 | 826 | 0 |
| `devibhagavata-purana-8` | **789** | 34 | 0 | 0 | 0 |
| `devibhagavata-purana-9` | **3447** | 7 | 0 | 155 | 0 |
| `gitagovinda` | **289** | 0 | 0 | 250 | 0 |
| `gitartha-samgraha_yamunacharya` | **32** | 0 | 0 | 14 | 0 |
| `gitarthasamgraha-abhinavagupta` | **748** | 0 | 0 | 402 | 0 |
| `hatha-yoga-pradipika` | **384** | 0 | 0 | 151 | 0 |
| `isha-up` | **19** | 0 | 0 | 15 | 0 |
| `jab-up` | **1** | 0 | 0 | 1 | 0 |
| `jabala-up` | **42** | 0 | 0 | 40 | 0 |
| `kai-up` | **25** | 0 | 0 | 17 | 0 |
| `kama-sutra` | **1502** | 0 | 0 | 460 | 0 |
| `kan-up` | **1** | 0 | 0 | 1 | 0 |
| `kat-up` | **119** | 0 | 0 | 100 | 0 |
| `kau-up` | **50** | 0 | 0 | 46 | 0 |
| `kena-up` | **35** | 0 | 0 | 24 | 0 |
| `kumarasambhava` | **614** | 0 | 0 | 82 | 0 |
| `mai-up` | **73** | 0 | 0 | 66 | 0 |
| `man-up` | **12** | 0 | 0 | 12 | 0 |
| `manavadharmashastra` | **2686** | 0 | 0 | 1140 | 0 |
| `megha-duta` | **115** | 0 | 0 | 82 | 0 |
| `mify-drind` | **0** | 1154 | 0 | 293 | 0 |
| `mnar-up` | **111** | 0 | 0 | 46 | 0 |
| `mun-up` | **65** | 0 | 0 | 55 | 0 |
| `nr-up` | **11** | 0 | 0 | 5 | 0 |
| `nyaya-bhashya` | **531** | 0 | 0 | 598 | 0 |
| `pai-up` | **19** | 0 | 0 | 9 | 0 |
| `paramarthasara-abhinavagupta` | **105** | 0 | 0 | 172 | 0 |
| `pr-up` | **67** | 0 | 0 | 41 | 0 |
| `pratyabhijna-hridaya_kshemaraja` | **21** | 0 | 0 | 223 | 0 |
| `raghuvamsha` | **399** | 1 | 0 | 205 | 0 |
| `ramanuja_gitabhashya` | **702** | 0 | 0 | 4 | 0 |
| `rampt-up` | **10** | 0 | 0 | 7 | 0 |
| `sankhya-karika` | **215** | 0 | 0 | 416 | 0 |
| `shatakatrayam` | **310** | 0 | 0 | 124 | 0 |
| `shatakatrayam-serebryakov` | **301** | 0 | 0 | 124 | 0 |
| `shiva-sutry_sharma` | **77** | 0 | 0 | 20 | 0 |
| `shukasaptati` | **260** | 0 | 79 | 177 | 0 |
| `shv-up` | **113** | 0 | 0 | 102 | 0 |
| `sub-up` | **13** | 0 | 0 | 11 | 0 |
| `tai-up` | **58** | 0 | 0 | 43 | 0 |
| `vajs-up` | **9** | 0 | 0 | 7 | 0 |
| `vedanga_jyotisha` | **84** | 0 | 0 | 17 | 0 |
| `vedartha-samgraha_ramanuja` | **143** | 0 | 0 | 394 | 0 |
| `yoga-sutry` | **195** | 0 | 0 | 0 | 0 |
| `yoga-sutry_sharma` | **195** | 0 | 0 | 50 | 0 |
| `yoga-sutry_vyasa-bhashya` | **203** | 0 | 0 | 933 | 0 |
| `yoga-sutry_zagumennov` | **195** | 0 | 0 | 14 | 0 |
| `yotat-up` | **143** | 0 | 0 | 144 | 0 |
| **Total (131)** | **95260** | **10148** | **80** | **45464** | **1** |

**95,260 exported pairs** across 131 sources. Determinism: a second `--all-ru` run is byte-identical (the pilot gate in `test_nkrya_export.py`, extended).

_Dr. Mārcis Gasūns_
