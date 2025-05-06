# ===========================================================
# Arquivo: core/ia_analisador.py
# ===========================================================
from __future__ import annotations

import httpx, json, logging
from typing import Dict
from app.config import settings

logger = logging.getLogger("famdomes.ia")


async def _chamar_ollama(prompt: str) -> str | None:
    url = f"{str(settings.OLLAMA_API_URL).rstrip('/')}/api/generate"
    body = {"model": settings.OLLAMA_MODEL, "prompt": prompt, "stream": False}

    try:
        async with httpx.AsyncClient(timeout=settings.MCP_TIMEOUT_S) as cli:
            resp = await cli.post(url, json=body)
        resp.raise_for_status()
        return resp.json().get("response")
    except Exception as exc:  # pragma: no cover
        logger.warning("OLLAMA: ❌ %s", exc)
        return None


async def detectar_intencao(texto: str) -> str:
    sistema = (
        "Você é um classificador. Responda SOMENTE com uma "
        "das opções: ESCALONAR_HUMANO, TRIAGEM_INICIAL, PRESENCA_VIVA, ACOLHIMENTO."
    )
    resp = await _chamar_ollama(f"{sistema}\n\nUsuário: {texto}\nIntenção:")
    intent = (resp or "").strip().split()[0].upper()
    return intent if intent in {"ESCALONAR_HUMANO", "TRIAGEM_INICIAL", "PRESENCA_VIVA"} else "ACOLHIMENTO"


async def analisar_sentimento(texto: str) -> Dict[str, float]:
    prompt = (
        "Avalie o sentimento do texto em JSON no formato "
        "{'positivo':0‑1,'negativo':0‑1,'neutro':0‑1}:\n" + texto
    )
    resp = await _chamar_ollama(prompt)
    try:
        dados = json.loads(resp) if resp else {}
        if all(k in dados for k in ("positivo", "negativo", "neutro")):
            return dados
    except Exception:
        pass
    logger.warning("Sentimento inválido – usando fallback neutro.")
    return {"positivo": 0.33, "negativo": 0.33, "neutro": 0.34}
