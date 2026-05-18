import asyncio
import httpx
import json
import re
from app.settings import settings
from typing import List, Dict, Any

# Strip simple HTML tags so AI prompts never carry markup. Cheap; intentional
# replacement for a full HTML parser since corpus line_html is well-formed
# and we don't need anything beyond tag elision for prompt context.
_STRIP_TAGS = re.compile(r"<[^>]+>")


def _plain(text: str) -> str:
    """Quick HTML-tag strip + whitespace collapse for AI prompt context."""
    if not text:
        return ""
    return re.sub(r"\s+", " ", _STRIP_TAGS.sub("", text)).strip()


async def _openai_chat(system_prompt: str, user_prompt: str, *, temperature: float = 0.2, timeout: float = 60.0) -> Dict[str, Any]:
    """Shared OpenAI-compatible /chat/completions call. Returns either
    `{'content', 'model', 'usage'}` on success or `{'error'}` on failure.

    All AI service functions converge here so the error-handling, headers,
    and URL-building stay in one place. Provider-agnostic: works with any
    base_url that exposes the OpenAI chat/completions schema (OpenAI,
    Ollama-with-openai-shim, vLLM, LM Studio, etc.).
    """
    if not settings.AI_BASE_URL:
        return {"error": "AI service (AI_BASE_URL) not configured"}

    payload = {
        "model": settings.AI_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": temperature,
    }
    headers = {"Content-Type": "application/json"}
    if settings.AI_API_KEY:
        headers["Authorization"] = f"Bearer {settings.AI_API_KEY}"

    url = f"{settings.AI_BASE_URL.rstrip('/')}/chat/completions"
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=payload, headers=headers, timeout=timeout)
            response.raise_for_status()
            data = response.json()
            return {
                "content": data["choices"][0]["message"]["content"],
                "model": data.get("model"),
                "usage": data.get("usage"),
            }
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

    result = await _openai_chat(system_prompt, user_prompt, temperature=0.2, timeout=45.0)
    if "error" in result:
        return result
    return {
        "explanation": result["content"],
        "model": result.get("model"),
        "usage": result.get("usage"),
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

    result = await _openai_chat(system_prompt, user_prompt, temperature=0.2, timeout=60.0)
    if "error" in result:
        return result
    return {
        "synthesis": result["content"],
        "model": result.get("model"),
        "usage": result.get("usage"),
    }
