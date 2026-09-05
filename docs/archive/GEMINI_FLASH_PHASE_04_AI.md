_Created: 25-08-2026 · Last updated: 05-09-2026_

# Gemini Flash Phase 04: AI

Goal: add optional provider-agnostic AI without making AI canonical.

## Task 4.1: AI Package Skeleton

Files:

- new `web/app/ai/`
- `web/app/settings.py`
- tests

Create:

- `models.py`,
- `service.py`,
- `providers/base.py`,
- `providers/fake_provider.py`.

Acceptance:

- App runs with `AI_ENABLED=false`.
- Tests use fake provider only.

## Task 4.2: Provider Interface

Implement:

- `AIRequest`,
- `AIResponse`,
- `AIProvider.complete()`.

Request includes:

- task type,
- model,
- system instructions,
- user prompt,
- structured corpus context,
- max output tokens.

Response includes:

- text,
- provider,
- model,
- usage if available,
- context references if available.

## Task 4.3: Providers

Files:

- `openai_provider.py`
- `local_openai_provider.py`
- `gemini_provider.py`

Implement:

- OpenAI provider.
- OpenAI-compatible local provider with configurable `base_url`.
- Gemini provider for tests/experiments.

Manual first local runner: Ollama through OpenAI-compatible endpoint if available.

Acceptance:

- Missing keys disable provider gracefully.
- Fake provider covers tests.

## Task 4.4: AI Cache and Logs

Files:

- `web/app/state_db.py`
- AI service/tests

Implement:

- `ai_cache`,
- `ai_requests`,
- cache by input hash,
- provider/model/latency/status/error logs.

Do not store unnecessary personal data.

## Task 4.5: First AI Feature

Recommended first feature: summarize current visible result set.

Endpoint:

- `POST /api/ai/summarize-results`.

Acceptance:

- Works with fake provider.
- Fails gracefully when AI disabled.
- Output is visually secondary to corpus text.

_Dr. Mārcis Gasūns_
