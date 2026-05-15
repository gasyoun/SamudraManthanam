# Gemini Flash Phase 03: Identity and Corrections

Goal: add low-friction Systema-Sanscriticum identity and correction proposals.

## Task 3.1: Lead/User Tables

Files:

- `web/app/state_db.py`
- tests

Implement tables:

- users,
- consent records,
- reading events.

Minimum user fields: email, name, role default `user`, created_at, last_seen_at.

Consent types: `personal_data_processing`, `marketing_email`.

Acceptance:

- Schema init is idempotent.
- Email is unique.

## Task 3.2: Lead Capture API

Files:

- new `web/app/routers/leads.py`
- `web/app/main.py`
- tests

Implement:

- `POST /api/leads`.
- Validate name and email.
- Require personal-data consent.
- Marketing/news consent is optional.
- Store source URL and timestamps.
- Create or update user by email.

Acceptance:

- Missing required consent is rejected.
- Marketing consent is never assumed.

## Task 3.3: Lead Capture UI

Implement:

- Trigger after around 50 percent page scroll.
- Ask name/email.
- Show two unchecked checkboxes.
- Do not show repeatedly after dismiss/submit.
- Do not aggressively block reading.

## Task 3.4: Magic-Link Skeleton

Files:

- new `web/app/routers/auth.py`
- state DB tables/tests

Implement:

- request magic link by email,
- verify token,
- create session placeholder.

Acceptance:

- Login identifies user.
- Role remains `user` unless manually changed.

## Task 3.5: Correction Proposals

Files:

- new `web/app/routers/corrections.py`
- reader/search UI
- tests

Implement:

- Email-identified users can propose corrections.
- Store proposals in `state.db`.
- Basic admin/editor JSON review endpoints.
- Export approved proposals as JSON.

Acceptance:

- Canonical corpus files are not changed.
- Anonymous users cannot submit corrections.
