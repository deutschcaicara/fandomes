"""
Persistência de logs de decisão e telemetria.
"""
from datetime import datetime, timezone
from pymongo import MongoClient
from app.config import MONGO_URI
import logging

mongo = MongoClient(MONGO_URI)
col_eventos = mongo["famdomes"]["eventos"]

logger = logging.getLogger("famdomes.trace")

def registrar_evento(telefone: str, *, etapa: str, dados: dict) -> None:
    doc = {
        "telefone": telefone,
        "etapa": etapa,
        "dados": dados,
        "timestamp": datetime.now(timezone.utc),
    }
    try:
        col_eventos.insert_one(doc)
    except Exception as exc:  # pragma: no cover
        logger.warning("Falha ao gravar evento em MongoDB: %s", exc)
