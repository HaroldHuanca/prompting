"""
Cliente de la API oficial de OpenAI para inferencia experimental con ChatGPT-4o.
"""
import time
from typing import Dict, Any, Optional

from openai import AsyncOpenAI

from backend.config import (
    MAX_COMPLETION_TOKENS,
    OPENAI_API_KEY,
    TARGET_MODEL,
    TEMPERATURE,
)


class OpenAIService:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or OPENAI_API_KEY
        self.model = TARGET_MODEL
        self.temperature = TEMPERATURE
        self.client = (
            AsyncOpenAI(api_key=self.api_key, max_retries=0, timeout=120.0)
            if self.api_key
            else None
        )

    async def generate_solution(
        self,
        prompt: str,
        problema: Optional[Dict[str, Any]] = None,
        tecnica_codigo: str = "ZERO_SHOT",
    ) -> Dict[str, Any]:
        """Realiza una llamada real y devuelve respuesta, uso y metadatos de la API."""
        if self.client is None:
            raise RuntimeError("OPENAI_API_KEY no está configurada; no se ejecutó una inferencia real.")

        start_time = time.perf_counter()
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                temperature=self.temperature,
                max_completion_tokens=MAX_COMPLETION_TOKENS,
                messages=[{"role": "user", "content": prompt}],
            )
        except Exception as exc:
            raise RuntimeError(f"Error al invocar OpenAI API: {exc}") from exc

        duration_ms = round((time.perf_counter() - start_time) * 1000.0, 3)
        choice = response.choices[0]
        usage = response.usage
        return {
            "exitoso": True,
            "modo": "openai_api_oficial",
            "modelo": response.model,
            "duracion_ms": duration_ms,
            "respuesta_completa": choice.message.content or "",
            "motivo_finalizacion": choice.finish_reason,
            "parametros": {
                "model": self.model,
                "temperature": self.temperature,
                "max_completion_tokens": MAX_COMPLETION_TOKENS,
            },
            "uso_tokens": {
                "prompt_tokens": usage.prompt_tokens if usage else None,
                "completion_tokens": usage.completion_tokens if usage else None,
                "total_tokens": usage.total_tokens if usage else None,
            },
        }
