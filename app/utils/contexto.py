# ===========================================================
# Arquivo: utils/contexto.py
# Persiste contexto de conversa + histórico da IA no MongoDB
# - CORRIGIDO: Verificação de conexão com DB/Coleção usando 'is not None'.
# - CORRIGIDO: Tratamento específico para erro de conflito de nome de índice (Code 85).
# - Adicionado salvamento de intent detectada.
# - Adicionado salvamento de texto do usuário.
# - Adicionado salvamento de texto do bot.
# - Funções para obter e limpar contexto mantidas.
# - Salvar flags de follow-up dentro de meta_conversa.
# ===========================================================
from __future__ import annotations

import logging
from datetime import datetime, timezone
from pymongo import MongoClient, ASCENDING, IndexModel
from pymongo.errors import ConnectionFailure, OperationFailure # Import OperationFailure
from typing import Dict, Any, Optional

# Importar configurações de forma segura
try:
    from app.config import MONGO_URI
except ImportError:
    import os
    MONGO_URI = os.getenv("MONGO_URI")
    if not MONGO_URI:
        logging.critical("CONTEXTO: Falha ao importar MONGO_URI de app.config e variável de ambiente MONGO_URI não definida.")
        MONGO_URI = None

logger = logging.getLogger("famdomes.contexto")

# --- Conexão e Configuração do Banco de Dados ---
mongo_client: Optional[MongoClient] = None
db: Optional[Any] = None # Tipo genérico para Database
contextos_db: Optional[Any] = None # Tipo genérico para Collection
respostas_ia_db: Optional[Any] = None # Tipo genérico para Collection

def conectar_db():
    """Estabelece conexão com o MongoDB e configura coleções e índices."""
    global mongo_client, db, contextos_db, respostas_ia_db

    # CORREÇÃO: Verifica todos os objetos comparando com None
    if mongo_client is not None and db is not None and contextos_db is not None and respostas_ia_db is not None:
        logger.debug("CONTEXTO: Conexão com MongoDB já estabelecida.")
        return

    if MONGO_URI is None:
        logger.error("CONTEXTO: ❌ MONGO_URI não definido. Não é possível conectar ao MongoDB.")
        return

    try:
        logger.info(f"CONTEXTO: Tentando conectar ao MongoDB em {MONGO_URI[:20]}...")
        mongo_client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000, connectTimeoutMS=5000, socketTimeoutMS=10000)
        mongo_client.server_info()
        db = mongo_client["famdomes"] # Ajuste o nome do DB se necessário
        contextos_db = db["contextos"]
        respostas_ia_db = db["respostas_ia"]

        # --- Criação de Índices ---
        indexes_contextos = [
            IndexModel([("tel", ASCENDING)], name="tel_unique_idx", unique=True),
            IndexModel([("ts", ASCENDING)], name="ts_idx"),
            IndexModel([("estado", ASCENDING)], name="estado_idx")
        ]
        indexes_respostas = [
            IndexModel([("telefone", ASCENDING)], name="telefone_idx"),
            IndexModel([("criado_em", ASCENDING)], name="criado_em_idx")
        ]

        # Tenta criar os índices para 'contextos'
        try:
            contextos_db.create_indexes(indexes_contextos)
            logger.info("CONTEXTO: Índices da coleção 'contextos' verificados/criados.")
        except OperationFailure as e:
            if e.code == 85:
                logger.info("CONTEXTO: Índices para 'contextos' já existem (possivelmente com nomes diferentes).")
            else:
                logger.warning(f"CONTEXTO: Aviso durante criação de índices para 'contextos': {e}")
        except Exception as e:
             logger.warning(f"CONTEXTO: Erro inesperado ao criar índices para 'contextos': {e}")

        # Tenta criar os índices para 'respostas_ia'
        try:
            respostas_ia_db.create_indexes(indexes_respostas)
            logger.info("CONTEXTO: Índices da coleção 'respostas_ia' verificados/criados.")
        except OperationFailure as e:
            if e.code == 85:
                logger.info("CONTEXTO: Índices para 'respostas_ia' já existem (possivelmente com nomes diferentes).")
            else:
                logger.warning(f"CONTEXTO: Aviso durante criação de índices para 'respostas_ia': {e}")
        except Exception as e:
             logger.warning(f"CONTEXTO: Erro inesperado ao criar índices para 'respostas_ia': {e}")

        logger.info("CONTEXTO: ✅ Conexão com MongoDB estabelecida e configuração de índices concluída.")

    except ConnectionFailure as e:
        logger.error(f"CONTEXTO: ❌ Falha na conexão com MongoDB: {e}")
        mongo_client = db = contextos_db = respostas_ia_db = None
    except Exception as e:
        logger.exception(f"CONTEXTO: ❌ ERRO inesperado ao conectar/configurar MongoDB: {e}")
        mongo_client = db = contextos_db = respostas_ia_db = None

# Tenta conectar na inicialização do módulo
conectar_db()

# ----------------------------------------------------------------------
def salvar_contexto(
    telefone: str,
    *,
    texto_usuario: Optional[str] = None,
    estado: Optional[str] = None,
    meta_conversa: Optional[Dict[str, Any]] = None,
    intent_detectada: Optional[str] = None,
    ultimo_texto_bot: Optional[str] = None,
    incrementar_interacoes: bool = True
) -> bool:
    """
    Atualiza (ou cria) o documento de contexto para um telefone no MongoDB.
    Retorna True se a operação foi bem-sucedida.
    """
    # Verifica se a coleção está disponível
    if contextos_db is None:
        logger.error(f"CONTEXTO: Falha ao salvar contexto para {telefone}. Coleção 'contextos' indisponível.")
        conectar_db() # Tenta reconectar
        if contextos_db is None: return False

    set_fields: Dict[str, Any] = {"ts": datetime.now(timezone.utc)}
    if texto_usuario is not None: set_fields["ultimo_texto_usuario"] = texto_usuario
    if estado is not None: set_fields["estado"] = estado
    if meta_conversa is not None: set_fields["meta_conversa"] = meta_conversa
    if intent_detectada is not None: set_fields["ultima_intent_detectada"] = intent_detectada
    if ultimo_texto_bot is not None: set_fields["ultimo_texto_bot"] = ultimo_texto_bot

    update_operation: Dict[str, Any] = {}
    if set_fields: update_operation["$set"] = set_fields
    if incrementar_interacoes: update_operation["$inc"] = {"interacoes": 1}

    agora = datetime.now(timezone.utc)
    set_on_insert_data = {
        "tel": telefone,
        "criado_em": agora,
        "estado": "INICIAL", # Define um padrão inicial
        "interacoes": 0 # Define um padrão inicial
    }
    # Sobrescreve padrões se valores forem fornecidos na primeira vez
    if estado is not None: set_on_insert_data["estado"] = estado
    if incrementar_interacoes: set_on_insert_data["interacoes"] = 1

    # Remove campos do $setOnInsert se eles já estiverem sendo definidos em $set ou $inc
    if "$set" in update_operation and "estado" in update_operation["$set"]:
         if "estado" in set_on_insert_data: del set_on_insert_data["estado"]
    if "$inc" in update_operation and "interacoes" in update_operation["$inc"]:
         if "interacoes" in set_on_insert_data: del set_on_insert_data["interacoes"]

    if set_on_insert_data:
        update_operation["$setOnInsert"] = set_on_insert_data

    if not update_operation.get("$set") and not update_operation.get("$inc") and not update_operation.get("$setOnInsert"):
         logger.debug(f"CONTEXTO: Nenhuma operação de atualização para salvar contexto de {telefone}.")
         return True

    try:
        result = contextos_db.update_one({"tel": telefone}, update_operation, upsert=True)
        logger.debug(f"CONTEXTO: Resultado do update para {telefone}: matched={result.matched_count}, modified={result.modified_count}, upserted_id={result.upserted_id}")
        if result.modified_count > 0 or result.upserted_id is not None:
             log_estado = estado if estado is not None else '(estado inalterado)'
             logger.info(f"CONTEXTO: Contexto salvo/atualizado para {telefone}. Estado: {log_estado}")
             return True
        else:
             logger.info(f"CONTEXTO: Contexto para {telefone} não modificado.")
             return True
    except Exception as e:
        logger.exception(f"CONTEXTO: ❌ ERRO ao salvar contexto para {telefone}: {e}")
        return False

# ----------------------------------------------------------------------
def obter_contexto(telefone: str) -> Dict[str, Any]:
    """
    Recupera o documento de contexto atual para um telefone do MongoDB.
    Retorna um dicionário com valores padrão se não encontrado ou erro.
    """
    # Verifica se a coleção está disponível
    if contextos_db is None:
        logger.error(f"CONTEXTO: Falha ao obter contexto para {telefone}. Coleção 'contextos' indisponível.")
        conectar_db() # Tenta reconectar
        if contextos_db is None: return {"estado": "INICIAL", "meta_conversa": {}, "interacoes": 0, "tel": telefone}

    try:
        doc = contextos_db.find_one({"tel": telefone}, {"_id": 0})
        if doc:
            logger.debug(f"CONTEXTO: Contexto encontrado para {telefone}. Estado: {doc.get('estado')}")
            doc.setdefault("estado", "INICIAL")
            doc.setdefault("meta_conversa", {})
            doc.setdefault("interacoes", 0)
            doc.setdefault("tel", telefone)
            return doc
        else:
            logger.info(f"CONTEXTO: Nenhum contexto encontrado para {telefone}. Retornando padrão.")
            return {"estado": "INICIAL", "meta_conversa": {}, "interacoes": 0, "tel": telefone}
    except Exception as e:
        logger.exception(f"CONTEXTO: ❌ ERRO ao obter contexto para {telefone}: {e}")
        return {"estado": "INICIAL", "meta_conversa": {}, "interacoes": 0, "tel": telefone}

# ----------------------------------------------------------------------
def salvar_resposta_ia(
    telefone: str,
    canal: str,
    mensagem_usuario: str,
    resposta_gerada: str,
    intent: str,
    entidades: Optional[Dict[str, Any]] = None,
    risco_detectado: bool = False,
    sentimento_detectado: Optional[Dict[str, float]] = None,
    nome_agente: Optional[str] = None,
    enviado_por_humano: bool = False # Novo campo para diferenciar msg humana
) -> bool:
    """
    Grava um registro da interação na coleção de histórico `respostas_ia`.
    Retorna True se a inserção foi bem-sucedida.
    """
    # Verifica se a coleção está disponível
    if respostas_ia_db is None:
        logger.error(f"CONTEXTO: Falha ao salvar resposta IA para {telefone}. Coleção 'respostas_ia' indisponível.")
        conectar_db() # Tenta reconectar
        if respostas_ia_db is None: return False

    entidades_validas = entidades if isinstance(entidades, dict) else {}
    sentimento_valido = sentimento_detectado if isinstance(sentimento_detectado, dict) else None

    documento = {
        "telefone": telefone,
        "canal": canal,
        "mensagem_usuario": mensagem_usuario,
        "resposta_gerada": resposta_gerada,
        "intent_detectada": intent,
        "entidades_extraidas": entidades_validas,
        "risco_detectado": bool(risco_detectado),
        "sentimento_detectado": sentimento_valido,
        "nome_agente": nome_agente,
        "enviado_por_humano": enviado_por_humano, # Salva o novo campo
        "criado_em": datetime.now(timezone.utc),
    }

    try:
        result = respostas_ia_db.insert_one(documento)
        if result.inserted_id:
            logger.debug(f"CONTEXTO: Resposta IA salva no histórico para {telefone} (Intent: {intent}, Humano: {enviado_por_humano}).")
            return True
        else:
            logger.error(f"CONTEXTO: ❌ Falha desconhecida ao inserir resposta IA no histórico para {telefone} (inserted_id nulo).")
            return False
    except Exception as e:
        logger.exception(f"CONTEXTO: ❌ ERRO ao salvar resposta IA no histórico para {telefone}: {e}")
        return False

# ----------------------------------------------------------------------
def limpar_contexto(telefone: str) -> bool:
    """
    Remove o documento de contexto e todos os registros de histórico
    associados a um telefone específico do MongoDB.
    Retorna True se algo foi apagado.
    """
    # Verifica se as coleções estão disponíveis
    if contextos_db is None or respostas_ia_db is None:
        logger.error(f"CONTEXTO: Falha ao limpar contexto para {telefone}. Coleções indisponíveis.")
        conectar_db() # Tenta reconectar
        if contextos_db is None or respostas_ia_db is None: return False

    contexto_apagado = False
    historico_apagado = False
    sucesso_geral = True

    try:
        logger.debug(f"CONTEXTO: Tentando remover contexto para {telefone}...")
        result_ctx = contextos_db.delete_one({"tel": telefone})
        if result_ctx.deleted_count > 0:
            contexto_apagado = True
            logger.info(f"CONTEXTO: Documento de contexto removido para {telefone}.")
        else:
            logger.info(f"CONTEXTO: Nenhum documento de contexto encontrado para remover para {telefone}.")
    except Exception as e:
        logger.exception(f"CONTEXTO: ❌ ERRO ao remover contexto para {telefone}: {e}")
        sucesso_geral = False

    try:
        logger.debug(f"CONTEXTO: Tentando remover histórico para {telefone}...")
        result_hist = respostas_ia_db.delete_many({"telefone": telefone})
        if result_hist.deleted_count > 0:
            historico_apagado = True
            logger.info(f"CONTEXTO: {result_hist.deleted_count} registro(s) de histórico removido(s) para {telefone}.")
        else:
             logger.info(f"CONTEXTO: Nenhum registro de histórico encontrado para remover para {telefone}.")
    except Exception as e:
        logger.exception(f"CONTEXTO: ❌ ERRO ao remover histórico para {telefone}: {e}")
        sucesso_geral = False

    return sucesso_geral and (contexto_apagado or historico_apagado)

