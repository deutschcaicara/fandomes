from fastapi import APIRouter, Request
import httpx
from app.config import WHATSAPP_API_URL, WHATSAPP_TOKEN, MONGO_URI
from pymongo import MongoClient
from datetime import datetime

router = APIRouter()

mongo = MongoClient(MONGO_URI)
acompanhamentos = mongo["famdomes"]["acompanhamentos"]

@router.post("/webhook/rocketchat/")
async def receber_rocketchat(request: Request):
    body = await request.json()
    mensagem = body.get("message", {}).get("msg")
    telefone = body.get("message", {}).get("metadata", {}).get("phone")

    if not mensagem or not telefone:
        return {"erro": "mensagem ou telefone ausente"}

    # 1. Marcar como acompanhado, se ainda não tiver sido
    existente = acompanhamentos.find_one({"telefone": telefone})
    if not existente:
        acompanhamentos.insert_one({
            "telefone": telefone,
            "mensagem_inicial": mensagem,
            "assumido_em": datetime.utcnow()
        })

    # 2. Enviar ao WhatsApp
    payload = {
        "messaging_product": "whatsapp",
        "to": telefone,
        "type": "text",
        "text": {
            "body": mensagem
        }
    }

    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}"
    }

    async with httpx.AsyncClient() as client:
        r = await client.post(WHATSAPP_API_URL, json=payload, headers=headers)

    return {
        "status": "enviado",
        "whatsapp_code": r.status_code,
        "acompanhamento_registrado": not existente
    }
