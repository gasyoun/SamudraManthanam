# Use Case Scenarios - Samudra Manthanam

This document outlines the primary ways scholars, students, and developers interact with the Samudra Manthanam platform.

## 1. Comparative Philological Research
**User:** A Sanskrit scholar researching the concept of *Dharma* in the Mahabharata.
- **Scenario:** The scholar wants to see every instance where "Dharma" (or its inflections like *dharmasya*, *dharmena*) appears in the first book (Adiparva).
- **Workflow:**
    1. Selects "Morphological Search".
    2. Enters "dharma" in IAST.
    3. Selects only "Махабхарата. Книга 1" from the source grid.
    4. Clicks "Найти".
- **Outcome:** The system expands "dharma" into all its inflected forms and returns high-fidelity citations with both the original Sanskrit (often in IAST/Devanagari) and the corresponding Russian translation.

## 2. Translation Audit & Verification
**User:** A translator working on a new Russian version of the Bhagavad Gita.
- **Scenario:** The user wants to compare how a specific difficult verse (e.g., BG 2.47) was handled by Smirnov, Erman, and Sementsov.
- **Workflow:**
    1. Selects "Regex Search".
    2. Enters the verse ID or a unique phrase from the verse.
    3. Filters for all "Bhagavad Gita" sources.
    4. Clicks "Найти".
- **Outcome:** The results area displays the verse from multiple translators side-by-side (grouped by source), allowing for instant stylistic and semantic comparison.

## 3. Language Learning & Contextual Usage
**User:** A student of Sanskrit learning verbal roots.
- **Scenario:** The student wants to find real-world examples of the root *√bhū* (to be) in the Rigveda to understand its Vedic usage.
- **Workflow:**
    1. Selects "Plain Search" or "Morphological Search".
    2. Enters common forms like "bhavati" or "babhuva".
    3. Selects "Ригведа" (all mandalas).
- **Outcome:** The student sees dozens of verses where the word appears, providing authentic context for grammatical study.

## 4. Offline Scholar Sync (Legacy Support)
**User:** A researcher working in a remote area with unstable internet.
- **Scenario:** The researcher uses the legacy Windows desktop application but wants the latest corrections made to the corpus on the central server.
- **Workflow:**
    1. Opens the Samudra Manthanam desktop app.
    2. Clicks "Check for Updates".
    3. The desktop app calls the Web API's `/api/corpus-sync/manifest`.
    4. The app identifies that 3 files have changed based on SHA-256 mismatches and downloads them automatically.
- **Outcome:** The researcher's local library is perfectly synchronized with the web version without needing to download a giant ZIP file.

## 5. Technical Maintenance & Data Integrity
**User:** System Administrator / Content Curator.
- **Scenario:** New HTML files have been uploaded to the `Data/` directory on the server.
- **Workflow:**
    1. The automated `reindex.sh` script runs via cron at 3:00 AM.
    2. `ingest.py` parses the new files, updates the FTS5 index, and regenerates SHA-256 hashes.
- **Outcome:** The web search and the sync API are instantly updated with the new content without manual intervention.
