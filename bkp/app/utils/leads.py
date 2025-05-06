from pymongo import MongoClient
from app.config import MONGO_URI
from datetime import datetime

mongo = MongoClient(MONGO_URI)
leads = mongo["famdomes"]["leads"]

def salvar_lead(paciente_id: str, canal: str, mensagem: str, intent: str, entidades: dict, risco: bool, tipo: str = "desconhecido"):
    leads.update_one(
        {"paciente_id": paciente_id},
        {
            "$set": {
                "mensagem_original": mensagem,
                "intent": intent,
                "entidades": entidades,
                "risco": risco,
                "canal": canal,
                "tipo": tipo,
                "ultima_interacao": datetime.utcnow()
            },
            "$setOnInsert": {
                "paciente_id": paciente_id,
                "criado_em": datetime.utcnow()
            }
        },
        upsert=True
    )
