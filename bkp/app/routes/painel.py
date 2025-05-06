from fastapi import APIRouter
from pymongo import MongoClient
from app.config import MONGO_URI

router = APIRouter()

mongo = MongoClient(MONGO_URI)
colecao = mongo["famdomes"]["respostas_ia"]

@router.get("/consulta/{token}")
async def status_consulta(token: str):
    return {
        "token": token,
        "status": "confirmado",
        "mensagem": "Sua sessão está confirmada com um profissional."
    }

@router.get("/historico/{telefone}")
async def historico_respostas(telefone: str):
    resultados = colecao.find({"telefone": telefone}).sort("criado_em", -1)
    historico = []
    for doc in resultados:
        historico.append({
            "mensagem": doc.get("mensagem"),
            "resposta": doc.get("resposta"),
            "intent": doc.get("intent"),
            "risco": doc.get("risco"),
            "criado_em": doc.get("criado_em").isoformat()
        })
    return {"historico": historico}
