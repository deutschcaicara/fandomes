# ===========================================================
# Arquivo: routes/whatsapp.py
# Webhook Cloud API → MCPOrquestrador
# ===========================================================
from __future__ import annotations

import json
import logging
from fastapi import APIRouter, BackgroundTasks, Request, Response, status, HTTPException
from pydantic import BaseModel, constr
from app.config import WHATSAPP_VERIFY_TOKEN
from app.core.mcp_orquestrador import MCPOrquestrador
from app.utils.mensageria import enviar_mensagem
from app.utils.contexto import limpar_contexto

logger = logging.getLogger("famdomes.whatsapp")

router = APIRouter(prefix="/chat/webhook/whatsapp", tags=["WhatsApp"])

# ----------------------------------------------------------------------
# 1 · Verificação inicial da Meta
@router.get("/", summary="Verifica webhook do WhatsApp")
async def verificar_webhook(request: Request) -> Response:
    args = request.query_params
    if (
        args.get("hub.mode") == "subscribe"
        and args.get("hub.verify_token") == WHATSAPP_VERIFY_TOKEN
    ):
        logger.info("Webhook WhatsApp verificado com sucesso.")
        return Response(content=args.get("hub.challenge"), media_type="text/plain")
    logger.warning("Falha na verificação do webhook – token incorreto.")
    raise HTTPException(status_code=403, detail="Token inválido")

# ----------------------------------------------------------------------
# 2 · Modelo interno para facilitar debug (não exposto na API)
class _WhatsappMsg(BaseModel):
    telefone: constr(strip_whitespace=True, min_length=8)
    texto: constr(strip_whitespace=True, min_length=1)

# ----------------------------------------------------------------------
# 3 · Recepção de mensagens
@router.post("/", status_code=status.HTTP_200_OK, summary="Webhook WhatsApp (POST)")
async def receber_mensagem(
    request: Request,
    background_tasks: BackgroundTasks,
) -> Response:
    """
    Recebe payload da Cloud API, extrai texto e delega ao MCP
    em task de background (latência mínima p/ Meta).
    """
    data = await request.json()
    try:
        entry = data["entry"][0]
        changes = entry["changes"][0]
        value = changes["value"]
    except (KeyError, IndexError, TypeError):
        # payload diferente (status, etc.) ⇒ apenas 200
        return Response(status_code=200)

    # Eventos de status não contêm 'messages'
    messages = value.get("messages", [])
    if not messages:
        return Response(status_code=200)

    msg = messages[0]
    if "text" not in msg or "body" not in msg["text"]:
        return Response(status_code=200)  # apenas mídia, voice, etc.

    texto = msg["text"]["body"].strip()
    telefone = msg["from"]

    # Comando de reset (não vai ao MCP)
    gatilho_reset = texto.lower().replace("\u200b", "").strip()  # remove zero‑width
    if gatilho_reset.startswith("melancia") and "vermelha" in gatilho_reset:
        background_tasks.add_task(_resetar_conversa, telefone)
        return Response(status_code=200)

    # Normal: delega ao MCP em background
    background_tasks.add_task(_processar_mcp, telefone, texto)
    return Response(status_code=200)

# ----------------------------------------------------------------------
# 4 · Task: reset
async def _resetar_conversa(telefone: str) -> None:
    limpar_contexto(telefone)        # ignoramos retorno: sempre zera
    await enviar_mensagem(
        telefone,
        "🔄 Sua conversa foi reiniciada. Pode começar de novo!",
    )
    logger.info("Reset concluído para %s", telefone)


# ----------------------------------------------------------------------
# 5 · Task: encaminhar para MCP
async def _processar_mcp(telefone: str, texto: str) -> None:
    try:
        await MCPOrquestrador().processar_mensagem(telefone, texto)
    except Exception as exc:  # pragma: no cover
        logger.exception("MCP erro para %s: %s", telefone, exc)
        await enviar_mensagem(
            telefone,
            "⚠️ Desculpe, houve um erro interno. Tente novamente em instantes.",
        )
