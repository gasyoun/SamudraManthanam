"""Deny-by-default spend policy for every paid AI provider call (H2866).

Why this exists
---------------
H2772 shipped the *route* half of AI safety: a session is required and a
hard 1,000-call monthly quota is consumed per user before any provider
call. That bounds **how many** calls a funded key can make. It bounds
nothing about **how expensive one call is**, and it does not stop the
service being live at all: the moment `AI_API_KEY` is funded, both routes
start billing.

This module is the preventive half. Every uncached provider request goes
through :func:`evaluate_call` first, and the verdict is computed entirely
from configuration plus the prompt text — **no HTTP is issued to decide**.
A rejection therefore costs exactly zero provider calls, which is the
property the H2866 test-suite asserts on every rejection path.

Deny-by-default, in order
-------------------------
1. ``AI_ENABLED`` is false            → ``ai_disabled`` (the kill switch)
2. ``AI_MAX_OUTPUT_TOKENS`` invalid   → ``invalid_output_bound``
3. ``AI_MAX_COST_PER_CALL`` invalid   → ``invalid_cost_ceiling``
4. model name empty                   → ``unknown_model``
5. ``AI_MODEL_PRICES`` unset/broken   → ``pricing_not_configured`` / ``pricing_invalid``
6. price currency ≠ ceiling currency  → ``currency_mismatch``
7. model absent from the price map    → ``unknown_model_price``
8. worst-case cost > ceiling          → ``cost_ceiling_exceeded``
9. otherwise                          → allow, carrying a bounded ``max_tokens``

There is deliberately **no built-in price table**. A stale hard-coded price
under-states cost and silently widens the ceiling, so pricing must be
configured explicitly per deployment; an unpriced model fails closed. This
means enabling paid AI is a *two-step* operator action — configure
``AI_MODEL_PRICES``, then set ``AI_ENABLED=true`` — and either step alone
leaves the service safely refusing.

Token estimation
----------------
Worst-case input tokens are estimated from prompt characters at
:data:`CHARS_PER_TOKEN`, deliberately set low (2.0) because the live
prompts are Russian: Cyrillic costs roughly 2–3 characters per token under
cl100k/o200k, versus ~4 for English. Under-counting tokens would
under-count cost and let an over-budget call through, so the estimate errs
high on purpose. Output tokens are not estimated at all — the policy
charges the full configured ``max_tokens``, because that is exactly the
bound sent to the provider.

Fences (H2866): this module never reads, writes, funds or rotates a
provider key, and never touches quota state.
"""
import json
import logging
import math
from dataclasses import dataclass, field
from typing import Any, Dict

from app.settings import settings

logger = logging.getLogger(__name__)

#: Conservative characters-per-token divisor for worst-case input sizing.
#: Lower = more tokens estimated = higher estimated cost = safer.
CHARS_PER_TOKEN = 2.0

#: Absolute ceiling on the configurable output bound. A deployment may set
#: ``AI_MAX_OUTPUT_TOKENS`` anywhere in ``1..HARD_MAX_OUTPUT_TOKENS``;
#: anything outside that range is a configuration error and fails closed
#: rather than being silently clamped (a silent clamp hides a typo that was
#: meant to be caught).
HARD_MAX_OUTPUT_TOKENS = 4096

#: Absolute ceiling on the configurable per-call cost limit, in
#: ``AI_COST_CURRENCY`` units. Guards against a fat-fingered ceiling
#: (``5000`` instead of ``0.05``) re-opening unbounded spend.
HARD_MAX_COST_PER_CALL = 1.0


@dataclass(frozen=True)
class PolicyDecision:
    """Verdict for one prospective provider call.

    ``allowed`` is the only field a caller must branch on. ``code`` is a
    stable machine-readable reason suitable for logs, metrics and tests;
    ``reason`` is human prose. ``max_tokens`` is meaningful only when
    allowed, and is the value the caller MUST put in the provider payload.
    """

    allowed: bool
    code: str
    reason: str
    max_tokens: int = 0
    estimated_cost: float = 0.0
    currency: str = ""
    details: Dict[str, Any] = field(default_factory=dict)

    @property
    def error_message(self) -> str:
        """Operator-facing one-liner for the ``{'error': ...}`` envelope."""
        return f"AI policy denied ({self.code}): {self.reason}"


def _deny(code: str, reason: str, **details: Any) -> PolicyDecision:
    return PolicyDecision(
        allowed=False,
        code=code,
        reason=reason,
        currency=str(getattr(settings, "AI_COST_CURRENCY", "") or ""),
        details=details,
    )


def estimate_prompt_tokens(*texts: str) -> int:
    """Conservative worst-case input-token count for the given prompt parts."""
    chars = sum(len(t or "") for t in texts)
    return int(math.ceil(chars / CHARS_PER_TOKEN))


def load_price_table() -> tuple[Dict[str, Any] | None, str]:
    """Parse ``AI_MODEL_PRICES`` into ``(table, error_code)``.

    Returns ``(table, "")`` on success or ``(None, code)`` on any problem.
    The accepted shape is strict — one shape only, because "guess which
    shape the operator meant" is exactly how a price map ends up silently
    empty::

        {"currency": "USD",
         "models": {"gpt-4o-mini": {"input_per_1m": 0.15,
                                    "output_per_1m": 0.60}}}

    Prices are per 1,000,000 tokens, in ``currency``.
    """
    raw = (getattr(settings, "AI_MODEL_PRICES", "") or "").strip()
    if not raw:
        return None, "pricing_not_configured"
    try:
        parsed = json.loads(raw)
    except Exception:
        return None, "pricing_invalid"
    if not isinstance(parsed, dict):
        return None, "pricing_invalid"
    currency = parsed.get("currency")
    models = parsed.get("models")
    if not isinstance(currency, str) or not currency.strip():
        return None, "pricing_invalid"
    if not isinstance(models, dict):
        return None, "pricing_invalid"
    return {"currency": currency.strip(), "models": models}, ""


def _model_price(models: Dict[str, Any], model: str) -> tuple[float, float] | None:
    """Return ``(input_per_1m, output_per_1m)`` or ``None`` if unusable."""
    entry = models.get(model)
    if not isinstance(entry, dict):
        return None
    try:
        inp = float(entry["input_per_1m"])
        out = float(entry["output_per_1m"])
    except Exception:
        return None
    if not math.isfinite(inp) or not math.isfinite(out) or inp < 0 or out < 0:
        return None
    return inp, out


def evaluate_call(
    system_prompt: str,
    user_prompt: str,
    *,
    model: str | None = None,
) -> PolicyDecision:
    """Decide whether one provider call may be dispatched. Issues no HTTP.

    `model` defaults to ``settings.AI_MODEL``. The returned decision's
    ``max_tokens`` is the bound the caller must send to the provider — the
    cost calculation is only honest if that exact value is used.
    """
    if not bool(getattr(settings, "AI_ENABLED", False)):
        return _deny(
            "ai_disabled",
            "paid AI is switched off (AI_ENABLED=false); no provider call is permitted",
        )

    try:
        max_output_tokens = int(getattr(settings, "AI_MAX_OUTPUT_TOKENS", 0))
    except Exception:
        max_output_tokens = 0
    if max_output_tokens <= 0 or max_output_tokens > HARD_MAX_OUTPUT_TOKENS:
        return _deny(
            "invalid_output_bound",
            f"AI_MAX_OUTPUT_TOKENS must be an integer in 1..{HARD_MAX_OUTPUT_TOKENS}, "
            f"got {getattr(settings, 'AI_MAX_OUTPUT_TOKENS', None)!r}",
            hard_cap=HARD_MAX_OUTPUT_TOKENS,
        )

    try:
        ceiling = float(getattr(settings, "AI_MAX_COST_PER_CALL", 0.0))
    except Exception:
        ceiling = 0.0
    if not math.isfinite(ceiling) or ceiling <= 0 or ceiling > HARD_MAX_COST_PER_CALL:
        return _deny(
            "invalid_cost_ceiling",
            f"AI_MAX_COST_PER_CALL must be a number in (0, {HARD_MAX_COST_PER_CALL}], "
            f"got {getattr(settings, 'AI_MAX_COST_PER_CALL', None)!r}",
            hard_cap=HARD_MAX_COST_PER_CALL,
        )

    resolved_model = (model if model is not None else getattr(settings, "AI_MODEL", "")) or ""
    resolved_model = resolved_model.strip()
    if not resolved_model:
        return _deny("unknown_model", "AI_MODEL is empty; a call cannot be priced")

    table, err = load_price_table()
    if table is None:
        return _deny(
            err,
            "AI_MODEL_PRICES is unset or malformed; per-call cost cannot be bounded",
        )

    ceiling_currency = str(getattr(settings, "AI_COST_CURRENCY", "") or "").strip()
    if not ceiling_currency or table["currency"].upper() != ceiling_currency.upper():
        return _deny(
            "currency_mismatch",
            f"AI_MODEL_PRICES currency {table['currency']!r} does not match "
            f"AI_COST_CURRENCY {ceiling_currency!r}",
        )

    price = _model_price(table["models"], resolved_model)
    if price is None:
        return _deny(
            "unknown_model_price",
            f"no usable price for model {resolved_model!r} in AI_MODEL_PRICES",
            model=resolved_model,
        )

    input_per_1m, output_per_1m = price
    input_tokens = estimate_prompt_tokens(system_prompt, user_prompt)
    estimated_cost = (
        input_tokens / 1_000_000.0 * input_per_1m
        + max_output_tokens / 1_000_000.0 * output_per_1m
    )

    if estimated_cost > ceiling:
        return _deny(
            "cost_ceiling_exceeded",
            f"worst-case cost {estimated_cost:.6f} {ceiling_currency} exceeds "
            f"AI_MAX_COST_PER_CALL {ceiling:.6f} {ceiling_currency}",
            model=resolved_model,
            input_tokens=input_tokens,
            max_output_tokens=max_output_tokens,
            estimated_cost=estimated_cost,
        )

    return PolicyDecision(
        allowed=True,
        code="allowed",
        reason="within configured per-call spend ceiling",
        max_tokens=max_output_tokens,
        estimated_cost=estimated_cost,
        currency=ceiling_currency,
        details={
            "model": resolved_model,
            "input_tokens": input_tokens,
            "input_per_1m": input_per_1m,
            "output_per_1m": output_per_1m,
        },
    )


def policy_config_report() -> Dict[str, Any]:
    """Configuration snapshot for startup logging and operator diagnostics.

    Never includes a key, a token or any prompt text. ``problems`` is empty
    only when a call could in principle be allowed; a disabled service is
    reported as such but is not a "problem" — disabled is the safe default.
    """
    problems: list[str] = []
    enabled = bool(getattr(settings, "AI_ENABLED", False))

    probe = evaluate_call("", "", model=getattr(settings, "AI_MODEL", ""))
    if enabled and not probe.allowed:
        problems.append(probe.code)

    table, err = load_price_table()
    priced_models = sorted(table["models"].keys()) if table else []

    return {
        "enabled": enabled,
        "model": getattr(settings, "AI_MODEL", ""),
        "max_output_tokens": getattr(settings, "AI_MAX_OUTPUT_TOKENS", None),
        "max_cost_per_call": getattr(settings, "AI_MAX_COST_PER_CALL", None),
        "currency": getattr(settings, "AI_COST_CURRENCY", ""),
        "priced_models": priced_models,
        "pricing_error": err,
        "problems": problems,
    }


def log_policy_config() -> Dict[str, Any]:
    """Emit one startup line describing the paid-AI posture. Never raises."""
    try:
        report = policy_config_report()
    except Exception:  # pragma: no cover - defensive; startup must not crash
        logger.exception("ai_policy: configuration report failed")
        return {}
    if not report["enabled"]:
        logger.info(
            "ai_policy: paid AI DISABLED (AI_ENABLED=false) — zero provider calls possible"
        )
    elif report["problems"]:
        logger.error(
            "ai_policy: paid AI enabled but misconfigured (%s) — every call will "
            "fail closed until fixed",
            ", ".join(report["problems"]),
        )
    else:
        logger.warning(
            "ai_policy: paid AI ENABLED — model=%s max_tokens=%s ceiling=%s %s",
            report["model"],
            report["max_output_tokens"],
            report["max_cost_per_call"],
            report["currency"],
        )
    return report
