# ===========================================================
# Arquivo: utils/contexto.py
# Persiste contexto de conversa + histórico da IA no MongoDB
# ===========================================================
from __future__ import annotations

import logging
from datetime import datetime, timezone
from pymongo import MongoClient, ASCENDING
from app.config import MONGO_URI

logger = logging.getLogger("famdomes.contexto")

# ----------------------------------------------------------------------
# Conexão e índices
mongo = MongoClient(MONGO_URI)
db = mongo["famdomes"]
contextos_db = db["contextos"]          # estado por telefone
respostas_ia_db = db["respostas_ia"]    # log IA

try:
    contextos_db.create_index("tel", unique=True, background=True)
    respostas_ia_db.create_index("telefone", background=True)
    respostas_ia_db.create_index([("criado_em", ASCENDING)], background=True)
except Exception:
    pass  # índices já existem

# ----------------------------------------------------------------------
def salvar_contexto(
    telefone: str,
    texto: str | None = None,
    novo_estado: str | None = None,
    meta_conversa: dict | None = None,
    trilha_cursor: dict | None = None,
    ultimo_texto_bot: str | None = None,
) -> None:
    """
    Atualiza (ou cria) o documento de contexto do telefone.
    Campos são opcionais; somente os passados são alterados.
    """
    set_fields: dict = {"ts": datetime.now(timezone.utc)}

    if texto is not None:
        set_fields["ultimo_texto"] = texto
    if novo_estado is not None:
        set_fields["estado"] = novo_estado
    if meta_conversa is not None:
        set_fields["meta_conversa"] = meta_conversa
    if trilha_cursor is not None:
        set_fields["trilha_cursor"] = trilha_cursor
    if ultimo_texto_bot is not None:
        set_fields["ultimo_texto_bot"] = ultimo_texto_bot

    contextos_db.update_one(
        {"tel": telefone},
        {"$set": set_fields, "$inc": {"interacoes": 1}},
        upsert=True,
    )
    logger.debug("Contexto salvo %s – %s", telefone, novo_estado or "(estado inalterado)")

# ----------------------------------------------------------------------
def obter_contexto(telefone: str) -> dict:
    """
    Recupera o contexto atual. Garante chaves mínimas.
    """
    doc = contextos_db.find_one({"tel": telefone}, {"_id": 0}) or {}
    doc.setdefault("estado", "INICIAL")
    doc.setdefault("meta_conversa", {})
    return doc

# ----------------------------------------------------------------------
def salvar_resposta_ia(
    telefone: str,
    canal: str,
    mensagem_usuario: str,
    resposta_gerada: str,
    intent: str,
    entidades: dict,
    risco: bool,
    sentimento: str | None = None,
) -> None:
    """
    Grava no histórico cada interação envolvendo IA.
    """
    try:
        respostas_ia_db.insert_one(
            {
                "telefone": telefone,
                "canal": canal,
                "mensagem_usuario": mensagem_usuario,
                "resposta_gerada": resposta_gerada,
                "intent": intent,
                "entidades": entidades or {},
                "risco": bool(risco),
                "sentimento_detectado": sentimento,
                "criado_em": datetime.utcnow(),
            }
        )
    except Exception as exc:
        logger.exception("Falha ao salvar resposta IA para %s: %s", telefone, exc)

# ----------------------------------------------------------------------
def limpar_contexto(telefone: str) -> bool:
    """
    Remove contexto e histórico IA de um telefone.
    Retorna True se algo foi apagado.
    """
    ctx_del = contextos_db.delete_one({"tel": telefone}).deleted_count
    hist_del = respostas_ia_db.delete_many({"telefone": telefone}).deleted_count
    return bool(ctx_del or hist_del)
