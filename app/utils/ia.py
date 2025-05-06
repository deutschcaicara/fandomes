"""
Wrapper para gerar sugestão de próximo passo usando Ollama (Gemma‑3b)
"""

from __future__ import annotations

import httpx
from typing import Dict, Any

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "gemma:3b"

async def gerar_sugestao_proximo_passo(contexto: Dict[str, Any]) -> str:
    """
    Envia o último bloco de mensagens da conversa para o modelo
    e retorna uma sugestão curta de ação clínica.
    """
    historico = contexto.get("historico", [])[-15:]  # últimas 15 entradas
    prompt = (
        "Você é um agente clínico. Dada a conversa abaixo, "
        "resuma em no máximo 2 linhas o próximo passo recomendado "
        "para o profissional humano.\n\n"
        f"{historico}\n\nSUGESTÃO:"
    )

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            OLLAMA_URL,
            json={"model": MODEL, "prompt": prompt, "stream": False},
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("response", "").strip()
