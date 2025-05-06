from fastapi import APIRouter, Request
from app.utils.offnlp import processar_mensagem  
from app.utils.leads import salvar_lead
from datetime import datetime

router = APIRouter()

@router.post("/chat/nlp")
async def chat_nlp(request: Request):
    dados = await request.json()
    mensagem = dados.get("mensagem")
    paciente_id = dados.get("paciente_id")
    canal = dados.get("canal")

    if not mensagem or not paciente_id:
        return {"erro": "Dados incompletos"}

    resultado = await processar_mensagem(mensagem, paciente_id, canal)

    salvar_lead(
        paciente_id=paciente_id,
        canal=canal,
        mensagem=mensagem,
        intent=resultado["intent"],
        entidades=resultado["entidades"],
        risco=resultado["risco"]
    )

    return resultado
