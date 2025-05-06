# ===========================================================
# Arquivo: utils/mensageria.py
# Envio robusto de mensagens via WhatsApp Cloud API
# ===========================================================
from __future__ import annotations

import httpx
import logging
from typing import Any, Dict
from app.config import WHATSAPP_API_URL, WHATSAPP_TOKEN

logger = logging.getLogger("famdomes.mensageria")

HEADERS = {
    "Authorization": f"Bearer {WHATSAPP_TOKEN}",
    "Content-Type": "application/json",
}
TIMEOUT = httpx.Timeout(timeout=20.0, connect=5.0)


async def enviar_mensagem(telefone: str, mensagem: str) -> Dict[str, Any]:
    if not WHATSAPP_API_URL or not WHATSAPP_TOKEN:
        logger.error("❌ MENSAGERIA: API URL ou Token não configurados.")
        return {"status": "erro_config", "erro": "WhatsApp API não configurada"}

    if not telefone or not mensagem:
        logger.warning("⚠️ MENSAGERIA: Telefone ou mensagem vazios.")
        return {"status": "erro_input", "erro": "Telefone ou mensagem ausente"}

    payload: Dict[str, Any] = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": telefone,
        "type": "text",
        "text": {"preview_url": False, "body": mensagem},
    }

    try:
        url = str(WHATSAPP_API_URL)  # 🔧 cast definitivo
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            resp = await client.post(url, json=payload, headers=HEADERS)
            resp.raise_for_status()

        logger.info("✅ Mensagem enviada a %s (HTTP %s)", telefone, resp.status_code)
        return {"status": "enviado", "code": resp.status_code, "retorno": resp.json()}

    except httpx.HTTPStatusError as exc:
        logger.error("❌ WHATSAPP %s – %s", exc.response.status_code, exc.response.text)
        return {"status": "erro_api", "code": exc.response.status_code, "erro": exc.response.text}
    except httpx.TimeoutException as exc:
        logger.error("⏰ Timeout WhatsApp: %s", exc)
        return {"status": "erro_timeout", "erro": str(exc)}
    except httpx.RequestError as exc:
        logger.error("🌐 Erro de conexão WhatsApp: %s", exc)
        return {"status": "erro_conexao", "erro": str(exc)}
    except Exception as exc:  # pragma: no cover
        logger.exception("💥 Erro inesperado WhatsApp: %s", exc)
        return {"status": "erro_desconhecido", "erro": str(exc)}
