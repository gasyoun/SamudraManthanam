# Samudra Manthanam — Identity and Trust Contract

_Created: 05-08-2026 · Last updated: 05-08-2026_

Companion to [SEARCH_CONTRACT.md](https://github.com/gasyoun/SamudraManthanam/blob/main/web/SEARCH_CONTRACT.md). Where that document specifies what the search boundary accepts, this one specifies who the write boundaries believe, and on what evidence. Delivered by [H1926](https://github.com/gasyoun/Uprava/blob/main/handoffs/archive/H1926-Opus_SamudraManthanam_bounded-regex-correction-trust_30.07.26.md) (Lane C of the architecture-integrity wave), acceptance criteria C3–C7.

## 1. Administrative authentication

Administrative endpoints — `POST /api/admin/vacuum`, `GET /api/corrections/pending` — authenticate from a **request header only**:

```text
X-Admin-Key: <ADMIN_SECRET_KEY>
Authorization: Bearer <ADMIN_SECRET_KEY>
```

| Presentation | Result |
|---|---|
| Correct key in `X-Admin-Key` or `Authorization: Bearer` | 200 |
| Wrong or missing header | 403 `Forbidden` |
| **Any** credential-shaped query parameter (`key`, `token`, `secret`, `api_key`, `admin_key`) | 400 — refused without being compared |

### Why the correct key in a query string is still refused

A query string is written verbatim to the nginx access log and the uvicorn access log, retained in browser history, and forwarded in the `Referer` header to any third party the page links to. By the time the application sees `?key=…`, the credential has already been distributed; rotating it does not retract any of those copies.

Accepting it "for compatibility" would make the leak permanent, because nothing would ever tell a client to stop. There is deliberately **no time-bounded compatibility path**: the only two callers were this repository's own test suite and the operator runbook, both updated in the same pass, so the migration cost is a header flag on two `curl` invocations.

Comparison uses `hmac.compare_digest` — a plain `==` leaks the key prefix-by-prefix through response timing.

With `ADMIN_SECRET_KEY` unset, the administrative surface is **closed in production** (403 for everything). The development-only `dev` key applies solely when `APP_ENV != "production"`.

## 2. Credential log hygiene

A logging filter ([`app/security.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/app/security.py)) rewrites credential-shaped query values to `key=REDACTED` in every emitted record. It is attached both to the application/server loggers and to the **root handlers**, because a filter on a logger never sees records propagated up from child loggers — only a handler filter sees everything that reaches output, including URLs logged by third-party libraries.

The filter redacts the *rendered* message and then clears the record's args. Redacting the format template in place is the obvious alternative and is wrong: it rewrites `key=%s` to `key=REDACTED` while the argument survives, and the handler dies with `not all arguments converted` — a logging filter that can silence logging is a worse failure than the leak it prevents. Pinned by `test_filter_does_not_break_records_whose_template_holds_the_parameter_name`.

Records with no credential in them are left untouched, so ordinary lazy formatting is preserved.

## 3. Correction trust tiers

| Tier | Granted by | Recorded | Proposals per hour |
|---|---|---|---|
| `anonymous` | nothing at all | `trust_tier`, `actor_ip_hash` (SHA-256, truncated) | 10 |
| `verified` | a redeemed session (§4) | the above plus `user_id` | 60 |

Both tiers write an append-only row to `correction_audit` naming the action, the trust tier, the actor (user id where known, IP hash otherwise), and the canonical `link_id` when the client supplied one. A reviewer can therefore tell an anonymous proposal from a verified one without re-deriving it from absent evidence.

**Anonymous intake stays open by design** (C7). A reader who spots a typo in a verse must be able to say so without an account; the cap exists so that openness is not also a way to fill the state database.

### Submitted email text is not identity

The `email` field of a correction proposal is **contact information**. It is stored in `contact_email`, it is never resolved against the users table, and it grants no attribution and no elevated capability.

Before H1926 it did exactly that: the endpoint looked the address up and attached the matching account to the correction, so typing a known scholar's address was enough to file corrections under their name — with no verification step anywhere in the loop. `user_id` is now written only from a session.

`POST /api/identity/lead` no longer returns the internal `users.id`. A database primary key is not a capability, and echoing it to an anonymous caller publishes the account sequence while inviting clients to treat a guessed integer as identity.

## 4. Verified sessions

Two steps, so that possession of the address — not knowledge of it — is what counts:

1. `POST /api/identity/verify/request` `{"email": …}` → **202**. Mints a single-use token with a 30-minute expiry.
2. `POST /api/identity/verify/confirm` `{"token": …}` → **200** with `session_token` (also set as the `sm_session` HttpOnly cookie), valid 30 days.

The session is then presented as `X-Session-Token: <token>` or via the cookie.

- Only token **hashes** are stored, so a leaked `state.db` yields no usable session or challenge.
- The `verify/request` response is identical for a known and an unknown address — it is not an account-enumeration oracle.
- A rejected token gets one undifferentiated 400. Distinguishing expired from unknown from already-redeemed tells an attacker which guess was closer.
- Challenges are single-use; a replayed token is refused.

### Delivery — a stated limitation

**No mail is sent, and none is faked.** Message delivery (SMTP, provider, templates, bounce handling) is out of scope for this lane. In a non-production environment the challenge token is returned in the `verify/request` response, which is what makes the whole loop testable end to end; in production it is written to the application log for an operator to relay.

That means the production verification path is **operator-assisted, not self-service**, until a mailer is wired in. It is recorded here rather than left to be discovered, and it does not weaken the property C6 asks for: what grants attribution is possession of the token, and typed email text still grants nothing either way.

## 5. Rate limiting

Fixed-window counters in `state.db` ([`app/services/rate_limit.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/app/services/rate_limit.py)), keyed by user id for verified callers and by truncated IP hash otherwise. Exceeding a window returns **429** with a `Retry-After` header.

Two properties worth stating because their absence is invisible:

- **Stored in SQLite, not in a process dict.** The application runs multiple workers, and a per-process counter silently multiplies the real limit by the worker count. A limit that is not the limit is worse than none, because it reads as protection.
- **Fails open on a storage error**, loudly logged. A broken rate-limit table must not take down correction intake — but the failure is never silent.

Known trade-off of fixed windows: a caller can spend a full quota at the end of one window and again at the start of the next. For an abuse cap measured in proposals per hour that burst is acceptable; it is documented rather than discovered.

## 6. Operator migration

- Admin calls move from `?key=…` to a header:
  ```sh
  curl -X POST -H "X-Admin-Key: $ADMIN_SECRET_KEY" https://<host>/api/admin/vacuum
  ```
- `state.db` gains `email_verifications`, `user_sessions`, `correction_audit` and `rate_limits`, plus `trust_tier` / `actor_ip_hash` / `contact_email` / `link_id` / `corpus_version` columns on `corrections`. All additive and idempotent, applied at startup; pre-existing rows default to `trust_tier = 'anonymous'`, which is the correct reading — none of them carried verified identity.
- Existing corrections keep whatever `user_id` the old email-lookup wrote. Those links are **not evidence of verification** and should not be treated as attribution.

_Dr. Mārcis Gasūns_
