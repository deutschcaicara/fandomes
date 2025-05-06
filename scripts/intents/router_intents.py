from fastapi import APIRouter, Request
from app.intents.intent_executor import IntentExecutor

router = APIRouter()

@router.post("/mensagem")
async def receber_mensagem(payload: dict):
    telefone = payload.get("telefone")
    mensagem = payload.get("mensagem")
    nome = payload.get("nome", "Paciente")
    if not telefone or not mensagem:
        return {"erro": "Campos obrigatórios faltando"}
    executor = IntentExecutor(telefone=telefone, mensagem=mensagem, nome=nome)
    resultado = await executor.executar()
    return {"status": "ok", "intent": resultado["intent"], "resposta": resultado["resposta"], "risco": resultado["risco"]}
