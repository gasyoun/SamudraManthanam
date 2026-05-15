import asyncio
import httpx
import json
from app.settings import settings
from typing import List, Dict, Any

async def explain_with_ai(query: str, context_lines: List[str]) -> Dict[str, Any]:
    """
    Sends search results to an LLM provider to generate an explanation.
    Follows the target architecture of being provider-agnostic.
    """
    if not settings.AI_BASE_URL:
        return {"error": "AI service (AI_BASE_URL) not configured"}
        
    system_prompt = """Вы — экспертный помощник по санскритской литературе и проекту «Пахтанье океана». 
Объясните смысл приведенных строк в контексте запроса.

ТРЕБОВАНИЯ:
1. Используйте ТОЛЬКО предоставленный контекст.
2. Цитаты из текста должны быть основой вашего ответа.
3. Указывайте ссылки на конкретные строки или источники.
4. Ответ должен быть на русском языке, академичным и ясным.
5. Если предоставленного контекста недостаточно для точного ответа, укажите это.
"""

    context_str = "\n".join(context_lines)
    user_prompt = f"Запрос пользователя: {query}\n\nКонтекст (строки из корпуса):\n{context_str}\n\nПроанализируй и объясни."

    payload = {
        "model": settings.AI_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.2
    }

    headers = {
        "Content-Type": "application/json"
    }
    if settings.AI_API_KEY:
        headers["Authorization"] = f"Bearer {settings.AI_API_KEY}"

    async with httpx.AsyncClient() as client:
        try:
            # Note: We append /chat/completions for OpenAI-compatible providers
            url = f"{settings.AI_BASE_URL.rstrip('/')}/chat/completions"
            response = await client.post(
                url,
                json=payload,
                headers=headers,
                timeout=45.0
            )
            response.raise_for_status()
            data = response.json()
            return {
                "explanation": data["choices"][0]["message"]["content"],
                "model": data.get("model"),
                "usage": data.get("usage")
            }
        except asyncio.CancelledError:
            raise
        except Exception as e:
            return {"error": f"AI provider error: {str(e)}"}
