import logging
from dataclasses import dataclass

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


@dataclass
class LLMStatus:
    configured: bool
    provider: str
    model: str


def is_llm_configured() -> bool:
    provider = settings.llm_provider.lower()
    if provider == "openai":
        return bool(settings.openai_api_key.strip())
    if provider == "gemini":
        return bool(settings.gemini_api_key.strip())
    return False


def get_llm_status() -> LLMStatus:
    provider = settings.llm_provider.lower()
    if provider == "openai":
        return LLMStatus(
            configured=bool(settings.openai_api_key.strip()),
            provider="openai",
            model=settings.openai_model,
        )
    return LLMStatus(
        configured=bool(settings.gemini_api_key.strip()),
        provider="gemini",
        model=settings.gemini_model,
    )


def llm_fallback_hint() -> str:
    status = get_llm_status()
    if not status.configured:
        if status.provider == "openai":
            return "LLM API 키가 설정되지 않았습니다. backend/.env에 OPENAI_API_KEY를 추가하세요."
        return "LLM API 키가 설정되지 않았습니다. backend/.env에 GEMINI_API_KEY를 추가하세요."
    return (
        f"LLM 호출에 실패했습니다 ({status.provider}/{status.model}). "
        "API 키·할당량·모델명을 확인한 뒤 백엔드를 재시작하세요."
    )


def chat(system: str, user: str, temperature: float = 0.3) -> str | None:
    if not is_llm_configured():
        return None

    provider = settings.llm_provider.lower()
    try:
        if provider == "openai":
            return _chat_openai(system, user, temperature)
        if provider == "gemini":
            return _chat_gemini(system, user, temperature)
        logger.warning("Unknown LLM_PROVIDER=%s", provider)
        return None
    except Exception:
        logger.warning("LLM chat failed (provider=%s)", provider, exc_info=True)
        return None


def _chat_openai(system: str, user: str, temperature: float) -> str | None:
    from openai import OpenAI

    client = OpenAI(api_key=settings.openai_api_key)
    response = client.chat.completions.create(
        model=settings.openai_model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=temperature,
    )
    content = response.choices[0].message.content
    return content.strip() if content else None


def _chat_gemini(system: str, user: str, temperature: float) -> str | None:
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=settings.gemini_api_key)
    response = client.models.generate_content(
        model=settings.gemini_model,
        contents=user,
        config=types.GenerateContentConfig(
            system_instruction=system,
            temperature=temperature,
        ),
    )
    text = response.text
    return text.strip() if text else None
