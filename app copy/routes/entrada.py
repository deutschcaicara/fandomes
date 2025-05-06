
"""
Webhook de entrada para mensagens (WhatsApp ou futuro canal).
Encaminha para o MCP Orquestrador.
"""
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, constr
from app.core.mcp_orquestrador import MCPOrquestrador

router = APIRouter(tags=["Entrada"])

class MensagemIn(BaseModel):
    telefone: constr(strip_whitespace=True, min_length=8)
    texto:    constr(strip_whitespace=True, min_length=1)

@router.post("/", status_code=status.HTTP_202_ACCEPTED)
async def receber_mensagem(msg: MensagemIn):
    try:
        await MCPOrquestrador().processar_mensagem(msg.telefone, msg.texto)
    except Exception as exc:  # pragma: no cover
        raise HTTPException(500, "Erro interno ao processar mensagem") from exc
    return {"status": "aceito"}
