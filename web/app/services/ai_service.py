import asyncio
import httpx
import json
import logging
import re
import time
from app.services.ai_cache import cache_get, cache_put, hash_request
from app.services.ai_policy import evaluate_call
from app.settings import settings
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

# Strip simple HTML tags so AI prompts never carry markup. Cheap; intentional
# replacement for a full HTML parser since corpus line_html is well-formed
# and we don't need anything beyond tag elision for prompt context.
_STRIP_TAGS = re.compile(r"<[^>]+>")


def _plain(text: str) -> str:
    """Quick HTML-tag strip + whitespace collapse for AI prompt context."""
    if not text:
        return ""
    return re.sub(r"\s+", " ", _STRIP_TAGS.sub("", text)).strip()


async def _openai_chat(
    system_prompt: str,
    user_prompt: str,
    *,
    temperature: float = 0.2,
    timeout: float = 60.0,
    task: str = "generic",
) -> Dict[str, Any]:
    """Shared OpenAI-compatible /chat/completions call with response cache.

    Returns either `{'content', 'model', 'usage'}` on success or
    `{'error'}` on failure. Successful responses are written to the
    ai_cache table keyed by SHA-256(system + user + model) — repeat
    callers get an instant cached return with `'cached': True` set so
    operators can distinguish hits in logs.

    All AI service functions converge here so the error-handling,
    headers, URL-building, AND caching stay in one place.
    Provider-agnostic: works with any base_url that exposes the OpenAI
    chat/completions schema (OpenAI, Ollama-with-openai-shim, vLLM,
    LM Studio, etc.).

    Spend policy (H2866) is evaluated FIRST — before the configuration
    check and before the cache lookup — so that a disabled or
    misconfigured service is uniformly inert: no provider call, and no
    cached answer served from a service an operator believes is off. The
    verdict costs zero HTTP requests, and the bound it returns is the
    `max_tokens` actually sent, so the ceiling that was checked is the
    ceiling that applies.
    """
    policy = evaluate_call(system_prompt, user_prompt, model=settings.AI_MODEL)
    if not policy.allowed:
        logger.warning(
            "ai_policy rejected task=%s code=%s: %s", task, policy.code, policy.reason
        )
        return {"error": policy.error_message, "policy_code": policy.code}

    if not settings.AI_BASE_URL:
        return {"error": "AI service (AI_BASE_URL) not configured"}

    request_hash = hash_request(system_prompt, user_prompt, settings.AI_MODEL)
    cached = await cache_get(request_hash)
    if cached is not None:
        # Mark as cache hit so callers / operators can distinguish without
        # tracking it separately at every callsite.
        cached["cached"] = True
        return cached

    payload = {
        "model": settings.AI_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": temperature,
        # The exact bound the cost ceiling was computed against. Sending a
        # different (or no) value would make the pre-call estimate a lie.
        "max_tokens": policy.max_tokens,
    }
    headers = {"Content-Type": "application/json"}
    if settings.AI_API_KEY:
        headers["Authorization"] = f"Bearer {settings.AI_API_KEY}"

    url = f"{settings.AI_BASE_URL.rstrip('/')}/chat/completions"
    start_ts = time.monotonic()
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=payload, headers=headers, timeout=timeout)
            response.raise_for_status()
            data = response.json()
            result = {
                "content": data["choices"][0]["message"]["content"],
                "model": data.get("model"),
                "usage": data.get("usage"),
            }
            latency_ms = int((time.monotonic() - start_ts) * 1000)
            # Cache write is fail-soft — if state.db is unavailable we
            # still return the live response to the caller.
            await cache_put(
                request_hash=request_hash,
                task=task,
                response=result,
                model=result.get("model"),
                latency_ms=latency_ms,
            )
            return result
        except asyncio.CancelledError:
            raise
        except Exception as e:
            return {"error": f"AI provider error: {str(e)}"}

async def explain_with_ai(query: str, context_lines: List[str]) -> Dict[str, Any]:
    """Send search-result context to the LLM and ask for an explanation.

    Returns either `{'explanation', 'model', 'usage'}` (callers convert to
    JSON) or `{'error': str}` for the route to translate to a clean 503.
    """
    system_prompt = (
        "Вы — экспертный помощник по санскритской литературе и проекту "
        "«Пахтанье океана». Объясните смысл приведенных строк в контексте запроса.\n\n"
        "ТРЕБОВАНИЯ:\n"
        "1. Используйте ТОЛЬКО предоставленный контекст.\n"
        "2. Цитаты из текста должны быть основой вашего ответа.\n"
        "3. Указывайте ссылки на конкретные строки или источники.\n"
        "4. Ответ должен быть на русском языке, академичным и ясным.\n"
        "5. Если предоставленного контекста недостаточно для точного ответа, "
        "укажите это."
    )
    context_str = "\n".join(context_lines)
    user_prompt = (
        f"Запрос пользователя: {query}\n\n"
        f"Контекст (строки из корпуса):\n{context_str}\n\nПроанализируй и объясни."
    )

    result = await _openai_chat(
        system_prompt, user_prompt, temperature=0.2, timeout=45.0, task="explain",
    )
    if "error" in result:
        return result
    return {
        "explanation": result["content"],
        "model": result.get("model"),
        "usage": result.get("usage"),
        "cached": bool(result.get("cached")),
    }


def build_compare_prompt(
    *,
    work_title: str,
    work_title_iast: str,
    chapter: int,
    verse: int,
    iast: str,
    translations: List[Dict[str, str]],
) -> str:
    """Build the user-prompt body for the translation-comparison task.

    Extracted so tests can validate the prompt shape independently of any
    AI provider call. The prompt asks for a structured comparison: key
    Sanskrit terms, divergences across translations, commentary readings
    (when present), and the verse's broader significance.

    `translations` is a list of `{label, role, text}` dicts. The `role`
    field comes from `compare_config` (`translation`/`anthology`/
    `commentary`/`context`) and we surface it to the model so it can
    weigh commentaries differently from translations.
    """
    lines = [
        f"Стих: {work_title} ({work_title_iast}) {chapter}.{verse}",
    ]
    if iast.strip():
        lines.append(f"Санскрит (IAST): {iast.strip()}")
    lines.append("")
    lines.append("Переводы и комментарии:")
    for i, t in enumerate(translations, 1):
        label = t.get("label", "").strip()
        role = t.get("role", "").strip()
        text = _plain(t.get("text", ""))
        role_marker = f" [{role}]" if role and role != "translation" else ""
        lines.append(f"{i}. {label}{role_marker}: {text}")
    lines.append("")
    lines.append(
        "Задачи:\n"
        "1. Определи ключевые санскритские термины этого стиха и предложи их трактовки.\n"
        "2. Сравни как переводчики передают эти термины — где они согласны, где расходятся.\n"
        "3. Отметь существенные расхождения между переводами с пояснением, какому толкованию каждый переводчик следует.\n"
        "4. Если в выборке есть комментарии (Рамануджа, Абхинавагупта и т. д.), кратко передай их интерпретацию.\n"
        "5. В одном-двух предложениях скажи, почему этот стих важен в контексте всего произведения.\n\n"
        "Формат: 200–400 слов на русском, академический стиль, со ссылками на номера переводов в выборке."
    )
    return "\n".join(lines)


async def compare_translations(
    *,
    work_title: str,
    work_title_iast: str,
    chapter: int,
    verse: int,
    iast: str,
    translations: List[Dict[str, str]],
) -> Dict[str, Any]:
    """Ask the LLM to synthesize across multiple translations of one verse.

    Returns either `{'synthesis', 'model', 'usage'}` or `{'error'}`.
    """
    system_prompt = (
        "Вы — экспертный филолог-санскритолог. Перед вами один и тот же стих "
        "санскритского произведения в нескольких русских переводах, иногда "
        "сопровождаемых комментариями средневековых индийских ачарьев и "
        "контекстом из основного произведения. Ваша задача — провести "
        "сравнительный филологический разбор: показать ключевые санскритские "
        "термины, сравнить трактовки переводчиков, отметить расхождения, "
        "коротко передать интерпретации комментаторов.\n\n"
        "ТРЕБОВАНИЯ:\n"
        "• Опирайтесь только на предоставленные тексты.\n"
        "• Не приписывайте переводчикам того, чего нет в их вариантах.\n"
        "• Если различий мало или их нет — так и скажите.\n"
        "• Академический регистр, ясный русский язык, ссылки на номера в выборке."
    )
    user_prompt = build_compare_prompt(
        work_title=work_title,
        work_title_iast=work_title_iast,
        chapter=chapter,
        verse=verse,
        iast=iast,
        translations=translations,
    )

    result = await _openai_chat(
        system_prompt, user_prompt, temperature=0.2, timeout=60.0,
        task="compare_translations",
    )
    if "error" in result:
        return result
    return {
        "synthesis": result["content"],
        "model": result.get("model"),
        "usage": result.get("usage"),
        "cached": bool(result.get("cached")),
    }
