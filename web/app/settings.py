from pydantic_settings import BaseSettings
from pydantic import ConfigDict

class Settings(BaseSettings):
    APP_ENV: str = "development"
    DB_PATH: str = "corpus.db"
    STATE_DB_PATH: str = ""
    CORPUS_PATH: str = ""
    PUBLIC_BASE_URL: str = ""
    ALLOWED_ORIGINS: str = ""

    # Funnel / marketing
    SYSTEMA_SANSCRITICUM_URL: str = ""
    SITE_DESCRIPTION: str = "Поисковая система по санскрито-русскому параллельному корпусу: «Бхагавадгита», «Махабхарата», упанишады и другие тексты."

    # Offline search packs (built by scripts/build_offline_pack.py)
    OFFLINE_PACKS_DIR: str = "offline-packs"

    # Admin
    ADMIN_SECRET_KEY: str = ""

    # AI Settings
    AI_PROVIDER: str = "openai-compatible"
    AI_BASE_URL: str = ""
    AI_API_KEY: str = ""
    AI_MODEL: str = "gpt-3.5-turbo" # or local model name

    # AI spend policy (H2866) — deny by default. Enforced in
    # app/services/ai_policy.py before ANY provider HTTP request; see that
    # module's docstring for the full rejection order and rationale.
    #
    # AI_ENABLED is the global kill switch. False means the two paid routes
    # answer 503 and no provider call is ever dispatched, regardless of how
    # well-funded AI_API_KEY is. Flipping it to true is not enough on its
    # own: AI_MODEL_PRICES must also price AI_MODEL, or every call still
    # fails closed as `unknown_model_price`.
    AI_ENABLED: bool = False

    # Hard output bound sent as `max_tokens` in every provider payload.
    # Must be 1..4096 (ai_policy.HARD_MAX_OUTPUT_TOKENS); outside that range
    # is a configuration error and fails closed rather than being clamped.
    AI_MAX_OUTPUT_TOKENS: int = 1024

    # Preventive worst-case ceiling for ONE call, in AI_COST_CURRENCY units.
    # Must be in (0, 1.0]. Worst-case = conservative input-token estimate at
    # the configured input price + the full AI_MAX_OUTPUT_TOKENS at the
    # output price. Over the ceiling → rejected before HTTP.
    AI_MAX_COST_PER_CALL: float = 0.05
    AI_COST_CURRENCY: str = "USD"

    # JSON price map. Empty by default ON PURPOSE: a hard-coded price table
    # goes stale silently and a stale price under-states cost, which widens
    # the ceiling without anyone noticing. Shape (prices per 1M tokens):
    #   {"currency": "USD",
    #    "models": {"gpt-4o-mini": {"input_per_1m": 0.15,
    #                               "output_per_1m": 0.60}}}
    # Verify the numbers against the provider's current price list before
    # setting this — nothing in the app can check them for you.
    AI_MODEL_PRICES: str = ""

    # AI response cache — avoids re-billing the provider for identical
    # (system_prompt + user_prompt + model) requests. Backed by state.db's
    # ai_cache table; falls back to a no-op when STATE_DB_PATH is unset.
    AI_CACHE_ENABLED: bool = True
    AI_CACHE_TTL_DAYS: int = 30

    model_config = ConfigDict(
        env_file=".env",
        extra="allow"
    )

settings = Settings()
