# Metadoc — SPEC_SAMUDRA_SCHOLAR_TIER_PAID_CAPABILITY_2026.md

_Created: 14-08-2026 · Last updated: 14-08-2026_

Companion record for
[SPEC_SAMUDRA_SCHOLAR_TIER_PAID_CAPABILITY_2026.md](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/SPEC_SAMUDRA_SCHOLAR_TIER_PAID_CAPABILITY_2026.md).

## Purpose

Decide **what the rebuilt ₽5 000 membership top level actually sells**, after MG
ruled D8 = «rebuilt» on 13-08-2026. It answers three things the parent ladder
spec deferred: which additive capabilities are buildable against Samudra's real
surface, what the metered one costs to run, and how membership status crosses
two applications on one host.

## Audience

Whoever prices or builds the scholar tier — and, more urgently, whoever is about
to fund the OpenRouter key. §0.3 and issue
[#307](https://github.com/gasyoun/SamudraManthanam/issues/307) are the reason
that person should read this first.

## Provenance

| | |
|---|---|
| Handoff | [H2640](https://github.com/gasyoun/Uprava/blob/main/handoffs/H2640-Opus_SamudraManthanam_scholar-tier-paid-capability-membership-top_13.08.26.md) — Scholar tier: the paid corpus capability the rebuilt ₽5 000 membership level sells |
| Model | **Opus 5** (`claude-opus-5`) |
| Parent | [H2567](https://github.com/gasyoun/Uprava/blob/main/handoffs/archive/H2567-Opus_Uprava_membership-ladder-4-levels-sept-2026_10.08.26.md) §5.2b → [SPEC_SAMSKRTE_MEMBERSHIP_LADDER_FOUR_LEVELS_2026.md](https://github.com/gasyoun/Uprava/blob/main/docs/SPEC_SAMSKRTE_MEMBERSHIP_LADDER_FOUR_LEVELS_2026.md) |
| Sibling residual | [H2641](https://github.com/gasyoun/Uprava/blob/main/handoffs/H2641-Opus_Uprava_ustny-korpus-redaction-programme-scoping_13.08.26.md) — Устный корпус redaction |
| Measurement data | [H2640_AI_QUERY_COST_MEASUREMENT.json](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/H2640_AI_QUERY_COST_MEASUREMENT.json) |
| Reproducer | [web/tools/measure_ai_query_cost.py](https://github.com/gasyoun/SamudraManthanam/blob/main/web/tools/measure_ai_query_cost.py) |

## What this doc overturned, and why that matters for re-reading it

Three of H2640's own premises did not survive contact with the running system.
A future session re-reading the handoff **without** this spec will inherit all
three:

1. «Candidate 5 decides the price, because it has real marginal cost» — it costs
   ₽0.088/call. It sizes the **quota**, not the price.
2. «Raised rate / result-cap tier — clean, free cap stays where it is» — there is
   no free cap anywhere to stay where it is. Rejected as a withdrawal in disguise.
3. «Bulk result-set export — clean, additive» — free export already returns 5 000
   rows, so the paid version has almost nothing to add.

## Ranked improvement backlog

1. **Re-measure the cost when a provider is actually chosen and funded.** The
   figure is anchored to `deepseek/deepseek-chat` because that is what
   `/opt/samudra/.env` names, not because it was selected on merit. §2.3's
   sensitivity band (₽5–18/100) is the guard against that anchoring, but a real
   choice deserves a real re-run.
2. **Validate the 660-token completion assumption against live responses.** It
   is derived from the compare prompt's own «200–400 слов» bound, and completion
   is the larger half of the bill. One funded day of real `usage` payloads
   replaces the assumption outright — `ai_service` already returns provider
   `usage`, and `ai_cache` stores it.
3. **Size the scholar audience directly.** §4.4's «single digits to ~15» is the
   weakest number in the doc: it is reasoned from audience mismatch (§4.3), not
   measured. A short survey of the 88 proven recording-buyers, or of the
   `/api/identity/lead` list, would replace it with evidence.
4. **Specify the Telegram alert channel** (candidate 1 is unshippable without a
   delivery channel, and Samudra has no mailer).
5. **Re-examine the parallel-vs-stacked ruling** once the club has run a quarter
   and real overlap between club members and API-key users is observable.

## Limitations — stated so they are not mistaken for findings

- **Completion tokens are assumed, not observed** (backlog 2). Every ₽ figure
  inherits that assumption; prompt tokens are measured exactly.
- **8 queries, one corpus version.** Prompt size is bounded by the 25-line
  context cap, so the spread is genuinely narrow (1 360–1 608), but the sample is
  small and Russian-heavy.
- **The revenue estimate is judgement, not measurement** (backlog 3).
- **FX is a single-day CBR rate.** A 20 % RUB move changes every ₽ figure
  proportionally and none of the conclusions.
- **Systema-side work is scoped from models and migrations, not from running
  code.** `ClubMembership` was read at `origin/main`; no Systema deploy was
  inspected.

## Revision history

| Date | Change | Model |
|---|---|---|
| 14-08-2026 | Created with the spec, under H2640 | Opus 5 (`claude-opus-5`) |

_Dr. Mārcis Gasūns_
