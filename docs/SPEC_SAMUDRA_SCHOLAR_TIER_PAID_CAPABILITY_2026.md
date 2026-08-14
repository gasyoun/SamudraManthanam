# Scholar tier — the paid corpus capability, costed against Samudra's real surface

_Created: 14-08-2026 · Last updated: 14-08-2026_

Executor: **Opus 5 (`claude-opus-5`)** under
[H2640](https://github.com/gasyoun/Uprava/blob/main/handoffs/H2640-Opus_SamudraManthanam_scholar-tier-paid-capability-membership-top_13.08.26.md),
minted from
[H2567](https://github.com/gasyoun/Uprava/blob/main/handoffs/archive/H2567-Opus_Uprava_membership-ladder-4-levels-sept-2026_10.08.26.md)
§5.2b after MG ruled **D8 = «rebuilt»** on 13-08-2026. Companion measurement data:
[H2640_AI_QUERY_COST_MEASUREMENT.json](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/H2640_AI_QUERY_COST_MEASUREMENT.json);
reproducer:
[web/tools/measure_ai_query_cost.py](https://github.com/gasyoun/SamudraManthanam/blob/main/web/tools/measure_ai_query_cost.py).

---

## 0. The three findings that change the brief

H2640 was written on a premise. Measured against the running system, the premise
does not hold, and saying so is the deliverable.

**1. The AI layer is dark on production, and has been.** `POST /api/ai/explain`
against [samudra…sslip.io](https://samudra.193.232.229.92.sslip.io/) — the same box
now also served as the branded [samudra.samskrte.ru](https://samudra.samskrte.ru/)
(H2391) — returns
**HTTP 503**; the service log gives the reason —
`AI provider error: Client error '403 Forbidden' for url 'https://openrouter.ai/api/v1/chat/completions'`
(measured 14-08-2026, `journalctl -u samudra`). `/opt/samudra/.env` carries
`AI_PROVIDER=openai-compatible`, `AI_BASE_URL=https://openrouter.ai/api/v1`,
`AI_MODEL=deepseek/deepseek-chat`, and an `AI_API_KEY` of 73 characters that the
provider rejects. The routes are mounted; the provider is unreachable.

This is the finding that settles the additive-only question **by measurement
rather than by argument**. Selling the AI layer withdraws nothing, because no
user has it today. It is the one candidate whose additivity does not rest on a
promise about future restraint.

**2. Candidate 5 does not decide the price — because it barely costs anything.**
H2640 states «Candidate 5 is the one that decides the price, because it is the
only one with a real marginal cost per use.» Measured against the real prompts
and real corpus context: **₽8.77 per 100 AI-assisted queries** (§2). At ₽0.088
a call, a 1 000-query monthly quota costs **₽88**. Cost-plus pricing of this
feature yields a number two orders of magnitude below any membership rung. The
price has to come from willingness-to-pay, and §4 derives it that way.

The cost figure was still worth measuring, because it inverts what the number is
*for*: it is not a pricing input, it is a **quota-sizing** input, and it makes
the generosity of the quota nearly free.

**3. There is no rate limiting anywhere on the public surface.**
[`rate_limit.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/app/services/rate_limit.py)
exists and is well-built, but it is wired to **corrections intake only** —
`search.py` and `ai.py` never call it, and `grep -rn 'limit_req\|limit_conn'
/etc/nginx/` on the prod box returns nothing. `/api/ai/*` therefore has **no
authentication and no cap**. The only thing standing between this project and an
unbounded OpenRouter bill is that the key is currently 403. That has two
consequences, and they pull in opposite directions:

- It **breaks candidate 3** as written (§3), because there is no free cap to
  raise above.
- It is a **denial-of-wallet liability** the moment the key is funded: at a
  sustained 10 req/s an anonymous caller draws ~864 000 calls/day, i.e.
  **₽75 800/day** at the measured rate — filed as
  [issue #307](https://github.com/gasyoun/SamudraManthanam/issues/307) in the
  same pass as this spec.

---

## 1. The hard rule, restated because §3 tests it

**Every capability shipped here must be something no user has today, and no
capability currently free may move behind the paywall.** Where the additive set
cannot carry a price, the answer is a lower price — never a smaller free tier.

§3 candidate 3 is the first real test of that rule, and it fails it. The finding
is recorded rather than engineered around.

---

## 2. Measured run-cost of the AI layer

### 2.1 Method

Prompt sizes were measured, not assumed. The reproducer pulls **real result
lines** for eight representative scholarly queries from the live public export
API, rebuilds the exact system+user prompts `ai_service` sends (importing
[`build_compare_prompt`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/app/services/ai_service.py)
rather than re-typing it, so the measurement cannot drift from the code), and
counts tokens with `tiktoken` `cl100k_base`. A `chars/4` estimate was rejected:
Russian and IAST both tokenize far worse than English, and the estimate would
have understated the bill.

Context is capped at **25 lines per call** — the frontend's real cap, not the
server's 50-line ceiling. Completion is taken from the compare prompt's own
stated bound («200–400 слов»), 300 words at 2.2 tokens/word for Russian
academic prose = 660 tokens.

### 2.2 Measured prompt sizes (8 queries, 14-08-2026, corpus `2026.08`, 235 sources)

| Task | median prompt tok | p90 | max | completion (assumed) |
|---|---:|---:|---:|---:|
| `/api/ai/explain` | **1 391.5** | 1 452 | 1 608 | 660 |
| `/api/ai/compare-translations` | **1 026.5** | 1 058 | 1 072 | 660 |

### 2.3 Cost per 100 queries

Priced against the provider **actually configured on prod** —
`deepseek/deepseek-chat` via OpenRouter, $0.2574/1M prompt and $1.0287/1M
completion (OpenRouter `/api/v1/models`, fetched 14-08-2026) — at
**USD/RUB 84.5449** (CBR official rate effective 15-08-2026, published 14-08-2026).

| Task | ₽/query | **₽/100 queries** |
|---|---:|---:|
| `explain` (median) | 0.0877 | **8.77** |
| `explain` (p90) | 0.0890 | 8.90 |
| `compare` (median) | 0.0797 | **7.97** |

**Provider sensitivity** — the same 1 391.5 + 660 tokens, other plausible models,
same FX:

| Model | ₽/100 queries |
|---|---:|
| `openai/gpt-4o-mini` | 5.11 |
| **`deepseek/deepseek-chat`** (prod-configured) | **8.77** |
| `openai/gpt-5-mini` | 14.10 |
| `google/gemini-2.5-flash` | 17.48 |

**The whole plausible band is ₽5–18 per 100 queries.** No provider choice inside
it changes any pricing conclusion below. The figure is also an **upper bound in
practice**: `ai_cache.py` keys on SHA-256(system+user+model) with a 30-day TTL, so
a repeated scholarly query costs ₽0.

### 2.4 Bounded default quota

**1 000 AI-assisted queries per member per month.**

| | deepseek (prod) | gemini-2.5-flash (worst in band) |
|---|---:|---:|
| Quota COGS / member / month | **₽87.68** | ₽174.79 |
| As a share of the ₽1 490 price (§4) | **5.9 %** | 11.7 % |

Sized by what keeps COGS under ~12 % at the worst provider in the band, not by
what a scholar plausibly consumes — because at these unit costs the binding
constraint is abuse, not usage. A working philologist will not approach 1 000
calls a month; the quota exists so that an automated caller cannot.

**The quota is a hard cap, not a soft one.** A quota that logs an overage and
serves the request anyway is not a cap, and this endpoint's failure mode is
financial.

---

## 3. Per-candidate build verdicts

Each row restates its rights line and names the substrate that exists today.

### Candidate 1 — Saved searches + change alerts → **SHIP**

- **Substrate:** [`identity.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/app/routers/identity.py)
  + `session_service` (`SESSION_TTL_DAYS = 30`, hashed tokens, live on prod —
  `POST /api/identity/verify/request` returns **202**).
- **Rights:** clean — a user's own queries are the user's own data. No corpus
  text is redistributed; an alert carries a query and a count.
- **Additive:** nothing comparable exists. Verified against the live route list.
- **Caveat that must ship with it:** an alert is only as good as its delivery
  channel, and Samudra has none (§5). Telegram is the honest first channel.

### Candidate 2 — API key + programmatic search → **SHIP** (the anchor for tooling value)

- **Substrate:** [`search.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/app/routers/search.py)
  for the query path; `rate_limit.py`'s `check_and_consume` for metering — it is
  already bucket-keyed and multi-worker-safe, so the paid meter needs a new
  bucket, not a new mechanism.
- **Rights:** clean — returns **results**, not bulk corpus text. Consistent with
  the standing posture that result export is in scope.
- **Additive:** yes. There is no key issuance today.
- **Note:** the free web search stays exactly as it is — unauthenticated, uncapped,
  no key required. The key buys a *stable, documented, quota'd* interface, not
  access to something withheld.

### Candidate 3 — Raised rate / result-cap tier → **REJECT as framed**

This is the rule's first real test, and it fails.

A «raised cap» presupposes a free cap. **There is none** — neither in the app nor
in nginx (§0.3). So there is nothing to raise, and the only way to make this
candidate sellable is to *introduce* a cap on free search and then sell relief
from it. That is a withdrawal in the precise sense §2.7 of H2567 objected to: the
free user's experience gets worse so the paid one can look better.

**Rejected.** What survives from it is a raised *export row* cap, folded into
candidate 4.

> This does not mean free search should stay uncapped forever. An abuse cap set
> far above any human usage is ordinary hygiene and is **not** a paid-tier
> feature. If one is ever added, it must be justified and sized as abuse
> protection, on its own ticket, and the scholar tier must not be its rationale.

### Candidate 4 — Bulk result-set export → **DEFER** (ship as a rider on #2, never as a selling point)

- **Substrate:** shipped. `GET /api/search/export` (html/json/csv).
- **Rights:** clean — H1831 already reduced JSON export to KWIC snippets rather
  than full `line_html`, so this is explicitly result-export, not bulk corpus.
- **Why defer:** **the free export limit is already 5 000 rows** (hardcoded
  `limit = 5000` in `get_export`). A paid tier can only differentiate by going
  above that. Worth doing — 50 000 rows for a key holder is a real convenience —
  but a capability whose free version already covers the 99th-percentile scholarly
  query cannot be sold as a reason to pay. Ships as a line item under the API key,
  and **the free 5 000 does not move.**

### Candidate 5 — AI-assisted query / gloss layer → **SHIP** (the anchor for perceived value)

- **Substrate:** [`ai.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/app/routers/ai.py)
  + `ai_service` + `ai_cache`, all built; provider dark (§0.1).
- **Rights:** clean — the model reads corpus lines the caller already has on
  screen and returns commentary, not corpus text.
- **Additive:** **verified by measurement** (503 on prod), not asserted.
- **Cost:** ₽0.088/query, quota 1 000/mo (§2.4).
- **Ships with a hard cap and authentication, or it does not ship.** See §0.3.

### Rejected outright, restated so the record is auditable

| | Why |
|---|---|
| Bulk corpus text download | Out of scope by standing rights posture. Not built, not planned. |
| Gating existing search / reader / morph / compare | Withdrawal. Banned by H2567 §2.7. |

---

## 4. Price recommendation — ₽1 490/mo, not ₽5 000

### 4.1 Why not cost-plus

At ₽0.088 a query, cost-plus on the only metered capability yields a price around
₽100/mo. The measured cost sets a **floor**, not a price, and the floor is
irrelevant. Willingness-to-pay decides.

### 4.2 What the wallet evidence actually supports

From [SPEC_SAMSKRTE_MEMBERSHIP_LADDER_FOUR_LEVELS_2026.md](https://github.com/gasyoun/Uprava/blob/main/docs/SPEC_SAMSKRTE_MEMBERSHIP_LADDER_FOUR_LEVELS_2026.md):

| Evidence | Figure |
|---|---|
| §3.2 — active payers clearing ₽60 000/yr (₽5 000/mo) | **87 of 558** (15.6 %) |
| §3.2 — median active payer trailing-12 wallet | ₽21 150/yr = **₽1 762/mo** |
| §3.6 — proven recording-buyers clearing ₽60 000/yr | **26 of 88** |
| §3.6 — proven recording-buyers clearing ₽18 000/yr | **65 of 88** |

H2640 is right that **26**, not 87, is the realistic ceiling — affordability
among people with *revealed* willingness to buy non-live content. But 26 is the
ceiling for *any* ₽5 000 product, and the scholar tier is not competing for a
share of it against nothing: H2567 §6 already books a **₽1 500/mo club** aimed at
65 of those same 88 buyers. A ₽5 000 scholar rung stacked on that asks the same
narrow segment for ₽6 500/mo.

### 4.3 The audience mismatch that decides it

The ₽5 000 wallet segment and the scholar-tooling audience are **not the same
people**. §3.6's 26 are buyers of *recorded teaching*. Saved searches, an API key,
and an AI gloss layer address **working philologists** — a set defined by research
practice, not by wallet size, and much smaller than 26 among this school's base.

Pricing a researcher-tooling bundle at the top of a teaching-content wallet
distribution is a category error. It would produce a tier that 26 people can
afford and roughly none want.

### 4.4 The recommendation

> **₽1 490/mo**, sold as a **parallel «Scholar» add-on**, not as the membership's
> top rung.

Derivation, each step from measured evidence:

1. **Ceiling ₽5 000** — 26 of 88 can afford it (§3.6), but stacked on the ₽1 500
   club it asks ₽6 500/mo of a segment whose *median* total spend is ₽1 762/mo
   (§3.2). Rejected as an anchor.
2. **Floor ~₽100** — cost-plus (§4.1). Rejected: prices the tier as a commodity
   and signals it is worth nothing.
3. **₽1 490** sits just below the ₽1 762/mo median wallet, on the same logic
   H2567 §6 used to land the club at ₽1 500, and inside the ₽18 000/yr band that
   **65 of 88** proven buyers clear (§3.6).
4. **Parallel, not stacked** — a researcher who wants an API key and an AI gloss
   layer should not first have to buy a video club. Stacking is what forces the
   ₽6 500 arithmetic in step 1.

**Unit economics at ₽1 490:**

| | deepseek | gemini-2.5-flash |
|---|---:|---:|
| COGS (1 000-query quota) | ₽87.68 | ₽174.79 |
| Gross margin | **94.1 %** | 88.3 % |

**Revenue, stated conservatively.** The honest first-year estimate is **single
digits to ~15 members** — the scholar-practice audience, not the 26 wallet-capable
ones. At 12 members: **₽17 880/mo gross, ~₽16 800/mo net.** That is a real
contribution against curator payroll and it is not a rounding error, but it is
**not a replacement for H2567 §6's ₽108 000 autumn shortfall**, and must not be
booked as one.

### 4.5 Timetable — unchanged, and this must not be read as autumn revenue

Nothing here ships by 01-09-2026. H2567 §5.2b already books the top tier at **₽0**
for Sep–Oct and that stands. The tier is announced as «готовится»; the price above
is what it is announced *at*, once §5's substrate work is done.

---

## 5. Auth substrate decision

> **Samudra's own `identity.py` sessions authenticate. Systema owns entitlement.
> A signed, short-lived grant token carries membership across the two hosts.**

### 5.1 What exists on each side

| | Status |
|---|---|
| Samudra `identity.py` sessions | **Live.** Email challenge → 30-day hashed session, cookie + `X-Session-Token`. `verify/request` returns 202 on prod. |
| Samudra mail delivery | **Absent.** `/opt/samudra/.env` has no `MAIL_*`/`SMTP_*` key at all; the docstring is explicit that the token is *logged*, not sent. **Self-serve email verification is not usable on prod today.** |
| Samudra → Systema link | `SYSTEMA_SANSCRITICUM_URL` — an outbound marketing CTA only ([`site_context.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/app/site_context.py)). No entitlement flow. |
| Systema `ClubMembership` | **Live**, shipped 13-08-2026 (H2644). Date-based activity (`revoked_at IS NULL AND grace_until > now()`). |
| Systema `ClubMembership` tiering | **Absent.** No `tier`/`plan` column in `2026_08_13_160000_create_club_memberships_table.php`. Single-rung. |

### 5.2 The decision and why

**Systema is the entitlement authority.** It owns the money contour — `Payment`,
`BillingSubscription`, `PaymentWebhookEvent`, `ClubMembership` — and Samudra must
never learn payment data. Duplicating subscription state into Samudra's `state.db`
would create a second source of truth for who has paid, which is the classic
canonical-vs-derived drift the org already has an integrity rule against.

**Samudra authenticates.** It already stores sessions, hashes tokens, and resolves
them per request. Building a second session system would be pure duplication.

**The bridge is a signed short-lived grant token**, redeemed through the existing
`redeem_verification` → session shape:

1. A member with an active `ClubMembership` (scholar plan) clicks «Открыть
   Пахтанье океана» in the Systema cabinet.
2. Systema mints a **single-use, ≤5-minute** token — HMAC over
   `(user_ref, plan, expiry, nonce)` with a shared secret — and redirects to
   Samudra carrying it.
3. Samudra verifies the signature, redeems the nonce once, and issues its
   **existing** 30-day session with a `plan` attribute.
4. Entitlement is **re-checked**, not trusted for 30 days: a nightly pull of
   active scholar plans, or a Systema-side revocation webhook. A cancelled
   membership must not keep a live session for a month.

`user_ref` is an opaque per-integration identifier, never Systema's `users.id`
and never an email — the same reasoning as the H1926 C4 note in `identity.py`
about not echoing internal primary keys.

**This also solves the mailer gap for the population that matters.** Paying
members never touch the email-challenge path; they arrive already
authenticated by Systema. Fixing Samudra's mail delivery stays needed for
*anonymous* verified accounts (candidate 1's alerts for non-members) but is not
on the critical path for the scholar tier.

### 5.3 What must be built (none of it exists)

| # | Work | Repo |
|---|---|---|
| 1 | `tier`/`plan` column on `club_memberships` + a scholar plan | Systema |
| 2 | Grant-token mint + redirect from the cabinet | Systema |
| 3 | Grant-token verify + nonce ledger + `plan` on the session | Samudra |
| 4 | Entitlement re-check (nightly pull or revocation webhook) | both |
| 5 | `api_keys` table + issuance UI, keyed to a session with a plan | Samudra |
| 6 | **Auth + hard quota on `/api/ai/*`** — the §0.3 liability | Samudra |
| 7 | Saved-search storage + a delivery channel (Telegram first) | Samudra |
| 8 | Raised export cap for key holders; **free stays at 5 000** | Samudra |

Item **6 is not optional and not sequenced last.** It is the one item that must
land *before* the OpenRouter key is ever funded, whether or not the tier ships.

---

## 6. What a free user still gets — the additive-only audit trail

This section exists so the rule in §1 is checkable after the fact. Every line
below describes the surface **as it stands on 14-08-2026**, and none of it moves.

| Free surface | Today | After the scholar tier |
|---|---|---|
| Corpus search (`/`, `/search/…`, `/s/…`) | unauthenticated, **no cap**, 235 sources, corpus `2026.08` | **identical** |
| Result export html/json/csv | up to **5 000 rows**, no account | **identical — the 5 000 does not move** |
| Morphology, compare, reader, chronology, sources, popular terms | free | **identical** |
| Corrections intake | anonymous, 10/hr cap | **identical** |
| Offline / PWA, corpus sync | free | **identical** |
| AI explain / compare | **HTTP 503 — nobody has it** | still nothing for free users; **nothing was taken** |
| Licence | Apache-2.0, self-hostable | **identical** |

**The audit test.** If a future session proposes moving any row in the left
column behind the paywall, that proposal is a violation of §1 regardless of the
revenue argument attached to it. The correct response is the one H2640 states:
lower the price, not the free tier.

**The one row worth watching** is free search's uncapped-ness. §3 candidate 3
already tried to monetise it and was rejected. If an abuse cap is ever added, it
must be sized as abuse protection and justified on its own ticket — and this
table is the record showing that the free tier's uncapped search predates the
paid tier and was never the paid tier's to sell.

---

## 7. Residual — what this does not close

- **The Устный корпус product** —
  [H2641](https://github.com/gasyoun/Uprava/blob/main/handoffs/H2641-Opus_Uprava_ustny-korpus-redaction-programme-scoping_13.08.26.md).
  Nothing here depends on it, which is the point of building the additive half first.
- **Whether the tier belongs in the membership at all.** §4.4 answers it
  *provisionally*: parallel add-on, not a membership rung. H2567 §5.2b flagged
  this as open; §4.3's audience-mismatch argument is the first evidence brought
  to it, and the final call is a human's.
- **The OpenRouter key.** Dark (403) and deliberately left dark. Funding it
  before §5.3 item 6 lands converts a dead endpoint into an open wallet.
- **Telegram as the alert channel** is named, not specified.
- **The ₽108 000 autumn shortfall** (H2567 §6) is untouched. §4.4's ~₽17 880/mo
  arrives in 2027, not this autumn.

_Dr. Mārcis Gasūns_
