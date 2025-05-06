# ===========================================================
# Gera resposta alternativa curta via Ollama local
# ===========================================================
from __future__ import annotations
import httpx, logging
from app.config import settings

logger = logging.getLogger("famdomes.ia-fallback")

async def gerar_resposta_ia(contexto: dict) -> str:
    prompt = (
        "Você é um vendedor empático. Responda em até 140 caracteres, "
        "sem jargões técnicos, incentivando o próximo passo.\n\n"
        f"{contexto}\nResposta:"
    )
    body = {"model": settings.OLLAMA_MODEL, "prompt": prompt, "stream": False}

    try:
        async with httpx.AsyncClient(timeout=20, follow_redirects=True) as cli:
            r = await cli.post(f"{settings.OLLAMA_API_URL.rstrip('/')}/api/generate", json=body)
            r.raise_for_status()
            return r.json().get("response", "").strip()
    except Exception as exc:
        logger.warning("IA-fallback falhou: %s", exc)
        return "Entendo! Quer mais detalhes ou ajuda humana?"
