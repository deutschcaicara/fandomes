# ===========================================================
# Arquivo: utils/followup.py
# (Implementação das funções de acompanhamento de pagamento)
# ===========================================================
from datetime import datetime, timezone
from pymongo import MongoClient, ReturnDocument
from pymongo.errors import ConnectionFailure
# Ajuste o import se config.py estiver em um diretório diferente
from app.config import MONGO_URI
# Importa a função de agendamento para ser chamada após o pagamento
# Ajuste o import se agenda.py estiver em um diretório diferente
from app.utils.agenda import agendar_consulta, formatar_horario_local
import logging

# Configuração básica de logging
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Conexão com MongoDB ---
mongo_followup = None
db_followup = None
pagamentos_db = None # Coleção para rastrear status de pagamento

try:
    # Estabelece conexão com MongoDB
    if MONGO_URI:
        mongo_followup = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        mongo_followup.server_info() # Testa a conexão
        db_followup = mongo_followup["famdomes"] # Nome do banco de dados
        pagamentos_db = db_followup["pagamentos"] # Coleção para pagamentos
        # Cria índices se não existirem
        pagamentos_db.create_index("telefone")
        pagamentos_db.create_index("id_sessao_stripe", sparse=True, unique=True) # ID da sessão deve ser único
        pagamentos_db.create_index("status")
        pagamentos_db.create_index("criado_em")
        logging.info("FOLLOWUP: Conexão com MongoDB estabelecida para Pagamentos.")
    else:
        logging.error("FOLLOWUP: ❌ MONGO_URI não definido. Não foi possível conectar ao MongoDB.")
except ConnectionFailure as e:
     logging.error(f"FOLLOWUP: ❌ Falha na conexão com MongoDB: {e}")
except Exception as e:
    logging.error(f"FOLLOWUP: ❌ ERRO ao conectar com MongoDB ou criar índices: {e}")
    mongo_followup = None
    db_followup = None
    pagamentos_db = None

# --- Funções de Follow-up ---

def iniciar_sessao(telefone: str, nome: str, id_sessao_stripe: str | None = None):
    """
    Registra o início de uma tentativa de pagamento no banco de dados.
    Chamado quando o link de pagamento é gerado. Usa update_one com upsert=True
    para criar ou atualizar o registro baseado no id_sessao_stripe, se fornecido.

    Args:
        telefone (str): Telefone do usuário.
        nome (str): Nome do usuário.
        id_sessao_stripe (str | None): ID da sessão de checkout do Stripe.
    """
    if pagamentos_db is None:
        logging.error("FOLLOWUP: ❌ Falha ao iniciar sessão: DB indisponível.")
        return

    try:
        agora = datetime.now(timezone.utc)
        # Filtro: usa id_sessao_stripe se disponível, senão cria um novo (ou atualiza baseado em telefone?)
        # É mais seguro basear no id_sessao_stripe para evitar sobrescrever sessões ativas
        filtro = {"id_sessao_stripe": id_sessao_stripe} if id_sessao_stripe else {"telefone": telefone, "status": "link_gerado"} # Se sem ID, atualiza último link gerado

        update_data = {
            "$set": {
                "telefone": telefone,
                "nome": nome,
                "status": "link_gerado", # Garante o status correto
                "ultima_atualizacao": agora
            },
            "$setOnInsert": { # Define apenas na criação
                 "id_sessao_stripe": id_sessao_stripe, # Só define ID na criação se filtro não o usou
                 "criado_em": agora
            }
        }
        # Se o filtro usou id_sessao_stripe, garante que ele seja definido no $set também
        if id_sessao_stripe:
            update_data["$set"]["id_sessao_stripe"] = id_sessao_stripe


        result = pagamentos_db.update_one(filtro, update_data, upsert=True)

        if result.upserted_id:
            logging.info(f"FOLLOWUP: 📍 Nova sessão de pagamento iniciada para {telefone} ({nome}). Sessão: {id_sessao_stripe or 'N/A'}.")
        elif result.modified_count > 0:
             logging.info(f"FOLLOWUP: 📍 Sessão de pagamento atualizada para {telefone} ({nome}). Sessão: {id_sessao_stripe or 'N/A'}.")
        else:
             logging.info(f"FOLLOWUP: 📍 Sessão de pagamento para {telefone} ({nome}) não modificada (Sessão: {id_sessao_stripe or 'N/A'}).")

    except Exception as e:
        logging.exception(f"FOLLOWUP: ❌ ERRO ao iniciar/atualizar sessão de pagamento para {telefone}:")

def marcar_pagamento(
    telefone: str | None = None,
    id_sessao_stripe: str | None = None,
    email_cliente: str | None = None,
    nome_cliente: str | None = None
) -> tuple[datetime | None, str | None]:
    """
    Marca um pagamento como concluído no banco de dados e tenta agendar a consulta.
    Chamado pelo webhook do Stripe após 'checkout.session.completed'.

    Args:
        telefone (str | None): Telefone do usuário (vindo dos metadados do Stripe).
        id_sessao_stripe (str | None): ID da sessão de checkout do Stripe.
        email_cliente (str | None): Email do cliente (vindo da sessão Stripe).
        nome_cliente (str | None): Nome do cliente (vindo da sessão Stripe ou metadados).

    Returns:
        tuple[datetime | None, str | None]:
            - horario_agendado_utc: O horário UTC da consulta agendada, ou None se falhar.
            - nome_final: O nome usado para o agendamento.
    """
    if pagamentos_db is None:
        logging.error("FOLLOWUP: ❌ Falha ao marcar pagamento: DB indisponível.")
        return None, None

    # Precisa do id_sessao para garantir que estamos atualizando o pagamento correto
    if not id_sessao_stripe:
        logging.error("FOLLOWUP: ❌ Falha ao marcar pagamento: ID da sessão Stripe ausente.")
        # Poderia tentar buscar por telefone, mas é arriscado se houver links antigos
        return None, None

    # Monta o filtro para encontrar o registro da sessão de pagamento pelo ID
    filtro = {"id_sessao_stripe": id_sessao_stripe}

    try:
        agora_utc = datetime.now(timezone.utc)
        # Dados para atualizar o registro
        update_data = {
            "$set": {
                "status": "pago", # Marca como pago
                "pago_em": agora_utc,
                "ultima_atualizacao": agora_utc,
                "email_stripe": email_cliente,
                # Atualiza telefone e nome se vieram do Stripe (podem ter sido preenchidos lá)
                "telefone": telefone if telefone else "$telefone", # Mantém o original se não veio
                "nome": nome_cliente if nome_cliente else "$nome" # Mantém o original se não veio
            }
        }

        # Encontra e atualiza o registro do pagamento
        # Retorna o documento APÓS a atualização para pegar os dados mais recentes
        pagamento_atualizado = pagamentos_db.find_one_and_update(
            filtro,
            update_data,
            return_document=ReturnDocument.AFTER # Pega o documento atualizado
        )

        if pagamento_atualizado:
            logging.info(f"FOLLOWUP: 💰 Pagamento confirmado para sessão {id_sessao_stripe} (Telefone: {pagamento_atualizado.get('telefone')}).")
            # Usa os dados atualizados para agendar
            tel_para_agendar = pagamento_atualizado.get('telefone')
            nome_para_agendar = pagamento_atualizado.get('nome', 'Cliente')
            email_para_agendar = pagamento_atualizado.get('email_stripe') # Usa o email do Stripe

            # Verifica se temos telefone para agendar
            if not tel_para_agendar:
                 logging.error(f"FOLLOWUP: ❌ Telefone ausente no registro de pagamento {id_sessao_stripe} após atualização. Não é possível agendar.")
                 return None, nome_para_agendar # Retorna nome para possível notificação

            # --- Tenta Agendar a Consulta ---
            logging.info(f"FOLLOWUP: Tentando agendar consulta para {nome_para_agendar} ({tel_para_agendar})...")
            horario_agendado_utc = agendar_consulta(
                telefone=tel_para_agendar,
                nome=nome_para_agendar,
                email=email_para_agendar
            )

            if horario_agendado_utc:
                logging.info(f"FOLLOWUP: ✅ Consulta agendada com sucesso para {tel_para_agendar} em {formatar_horario_local(horario_agendado_utc)}.")
                # Salva o horário agendado no registro de pagamento
                pagamentos_db.update_one(
                    {"_id": pagamento_atualizado["_id"]},
                    {"$set": {"horario_consulta_agendada_utc": horario_agendado_utc, "status": "agendado"}} # Atualiza status final
                )
                return horario_agendado_utc, nome_para_agendar
            else:
                logging.error(f"FOLLOWUP: ❌ Falha ao agendar consulta para {tel_para_agendar} após pagamento.")
                # O pagamento foi marcado, mas o agendamento falhou. Requer atenção manual.
                pagamentos_db.update_one(
                     {"_id": pagamento_atualizado["_id"]},
                     {"$set": {"status": "pago_erro_agendamento"}} # Marca status especial
                )
                return None, nome_para_agendar # Retorna None para horário, mas nome para possível notificação
        else:
            logging.warning(f"FOLLOWUP: ⚠️ Nenhum registro de pagamento encontrado para ID Sessão Stripe: {id_sessao_stripe}. Pagamento pode já ter sido processado ou ID inválido.")
            return None, None

    except Exception as e:
        logging.exception(f"FOLLOWUP: ❌ ERRO CRÍTICO ao marcar pagamento/agendar para ID Sessão {id_sessao_stripe}:")
        return None, None

# TODO: Adicionar função para checar follow-ups (ex: pagamentos com link_gerado > X horas) se necessário.
# async def checar_followups(): ...

