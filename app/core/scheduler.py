# ===========================================================
# Arquivo: core/scheduler.py
# Scheduler assíncrono (apscheduler) para tarefas recorrentes.
# - Implementa follow-up para qualificação parada.
# - Implementa follow-up para pagamento pendente.
# - Usa flags no contexto para evitar envios repetidos.
# ===========================================================
import asyncio
import logging
from datetime import datetime, timedelta, timezone
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from pymongo import MongoClient

# Imports de configuração e agentes/orquestrador
from app.config import MONGO_URI, settings # Usar settings para robustez
from app.agents.domo_followup import DomoFollowUp
# from app.core.mcp_orquestrador import MCPOrquestrador # Descomentar se usar orquestrador

logger = logging.getLogger("famdomes.scheduler")

# --- Configurações do Scheduler ---
# Usar fuso horário local relevante (ex: 'America/Sao_Paulo')
TIMEZONE_SCHEDULER = getattr(settings, "TIMEZONE_SCHEDULER", "America/Sao_Paulo")
try:
    sched = AsyncIOScheduler(timezone=TIMEZONE_SCHEDULER)
except Exception as e:
    logger.error(f"SCHEDULER: Erro ao inicializar com timezone '{TIMEZONE_SCHEDULER}': {e}. Usando UTC.")
    sched = AsyncIOScheduler(timezone="UTC")


# Intervalos de verificação e follow-up (em horas)
INTERVALO_CHECK_JOB_HORAS = getattr(settings, "SCHEDULER_CHECK_INTERVAL_HOURS", 1)
INTERVALO_FOLLOWUP_QUALIFICACAO_HORAS = getattr(settings, "SCHEDULER_FOLLOWUP_QUAL_HOURS", 4)
INTERVALO_FOLLOWUP_PAGAMENTO_HORAS = getattr(settings, "SCHEDULER_FOLLOWUP_PAY_HOURS", 24)

# Intents a serem usadas para o follow-up (devem existir nos JSONs)
INTENT_FOLLOWUP_QUALIFICACAO = "FOLLOW_UP_QUALIFICACAO"
INTENT_FOLLOWUP_PAGAMENTO = "FOLLOW_UP_24H" # Ou outra intent específica

# Estados que indicam qualificação/pitch em andamento
ESTADOS_QUALIFICACAO_ATIVOS = [
    "MICRO_COMPROMISSO", # Durante as perguntas
    "PITCH_PLANO1",      # Após apresentar plano 1
    "PITCH_PLANO3",      # Após apresentar plano 3
    "COMERCIAL_DETALHES_PLANO" # Após dar detalhes
]
# Estado que indica link de pagamento enviado
ESTADO_AGUARDANDO_PAGAMENTO = "AGUARDANDO_PAGAMENTO" # Ou "CALL_TO_ACTION" se for o último antes do link

async def _job_verificar_followups():
    """
    Job executado periodicamente para verificar usuários que precisam de follow-up.
    """
    logger.info("SCHEDULER: Iniciando verificação de follow-ups...")
    try:
        mongo = MongoClient(MONGO_URI)
        db = mongo["famdomes"] # Usar nome do DB de settings se disponível
        col_contextos = db["contextos"]
    except Exception as e:
        logger.exception(f"SCHEDULER: Erro ao conectar ao MongoDB: {e}")
        return # Aborta a job se não conectar ao DB

    agora_utc = datetime.now(timezone.utc)
    # orquestrador = MCPOrquestrador() # Instanciar se for chamar via orquestrador

    # --- 1. Follow-up para Qualificação Incompleta ---
    try:
        limite_qualificacao = agora_utc - timedelta(hours=INTERVALO_FOLLOWUP_QUALIFICACAO_HORAS)
        filtro_qualificacao = {
            "estado": {"$in": ESTADOS_QUALIFICACAO_ATIVOS},
            "ts": {"$lt": limite_qualificacao}, # Última interação foi há muito tempo
            # Verifica se o follow-up específico JÁ foi enviado
            "meta_conversa.followup_qualificacao_enviado": {"$ne": True}
        }
        # Busca apenas o telefone para evitar carregar dados desnecessários
        usuarios_qualificacao = list(col_contextos.find(filtro_qualificacao, {"tel": 1, "_id": 0}))
        logger.info(f"SCHEDULER: {len(usuarios_qualificacao)} usuários encontrados para follow-up de qualificação.")

        for user_data in usuarios_qualificacao:
            tel = user_data.get("tel")
            if not tel: continue

            logger.info(f"SCHEDULER: Enviando follow-up de qualificação para {tel}")
            try:
                # --- Execução do Agente de Follow-up ---
                # Opção 1: Chamar diretamente o agente (mais simples)
                agente_followup = DomoFollowUp(intent=INTENT_FOLLOWUP_QUALIFICACAO, sentimento={}) # Sentimento vazio para msg de sistema
                await agente_followup.executar(telefone=tel, mensagem_original="") # Mensagem original vazia

                # Opção 2: Chamar via Orquestrador (garante fluxo completo, mais complexo)
                # await orquestrador.processar_mensagem(tel, f"trigger:{INTENT_FOLLOWUP_QUALIFICACAO}")

                # --- Marcar Follow-up como Enviado ---
                # Atualiza a flag DENTRO da meta_conversa para evitar poluir o doc principal
                col_contextos.update_one(
                    {"tel": tel},
                    {"$set": {"meta_conversa.followup_qualificacao_enviado": True}}
                )
                await asyncio.sleep(0.1) # Pequena pausa para não sobrecarregar

            except Exception as e:
                logger.error(f"SCHEDULER: Erro ao processar follow-up de qualificação para {tel}: {e}")

    except Exception as e:
        logger.exception(f"SCHEDULER: Erro geral ao buscar usuários para follow-up de qualificação: {e}")


    # --- 2. Follow-up para Pagamento Pendente ---
    try:
        limite_pagamento = agora_utc - timedelta(hours=INTERVALO_FOLLOWUP_PAGAMENTO_HORAS)
        filtro_pagamento = {
            "estado": ESTADO_AGUARDANDO_PAGAMENTO,
            "ts": {"$lt": limite_pagamento},
            "meta_conversa.followup_pagamento_enviado": {"$ne": True}
        }
        usuarios_pagamento = list(col_contextos.find(filtro_pagamento, {"tel": 1, "_id": 0}))
        logger.info(f"SCHEDULER: {len(usuarios_pagamento)} usuários encontrados para follow-up de pagamento.")

        for user_data in usuarios_pagamento:
            tel = user_data.get("tel")
            if not tel: continue

            logger.info(f"SCHEDULER: Enviando follow-up de pagamento para {tel}")
            try:
                # --- Execução do Agente de Follow-up ---
                agente_followup = DomoFollowUp(intent=INTENT_FOLLOWUP_PAGAMENTO, sentimento={})
                await agente_followup.executar(telefone=tel, mensagem_original="")

                # --- Marcar Follow-up como Enviado ---
                col_contextos.update_one(
                    {"tel": tel},
                    {"$set": {"meta_conversa.followup_pagamento_enviado": True}}
                )
                await asyncio.sleep(0.1)

            except Exception as e:
                logger.error(f"SCHEDULER: Erro ao processar follow-up de pagamento para {tel}: {e}")

    except Exception as e:
        logger.exception(f"SCHEDULER: Erro geral ao buscar usuários para follow-up de pagamento: {e}")

    # --- Limpeza de Flags Antigas (Opcional) ---
    # Para permitir novos follow-ups após um tempo, pode-se remover as flags
    # Ex: Remover flags de follow-up de qualificação após 3 dias
    # limite_limpeza = agora_utc - timedelta(days=3)
    # col_contextos.update_many(
    #     {"meta_conversa.followup_qualificacao_enviado": True, "ts": {"$lt": limite_limpeza}},
    #     {"$unset": {"meta_conversa.followup_qualificacao_enviado": ""}}
    # )

    logger.info("SCHEDULER: Verificação de follow-ups concluída.")


def iniciar():
    """Adiciona a job ao scheduler e o inicia, se ainda não estiver rodando."""
    if not sched.running:
        try:
            # Adiciona a job para rodar a cada X horas
            sched.add_job(
                _job_verificar_followups,
                "interval",
                hours=INTERVALO_CHECK_JOB_HORAS,
                id="verificar_followups_diarios", # ID único para a job
                replace_existing=True, # Substitui se já existir com mesmo ID
                next_run_time=datetime.now(pytz.timezone(TIMEZONE_SCHEDULER)) + timedelta(seconds=15) # Roda logo após iniciar
            )
            sched.start()
            logger.info(f"SCHEDULER: Agendador iniciado no timezone '{TIMEZONE_SCHEDULER}'. Verificações a cada {INTERVALO_CHECK_JOB_HORAS} hora(s).")
        except Exception as e:
             logger.exception(f"SCHEDULER: Falha ao iniciar o agendador: {e}")
    else:
        logger.info("SCHEDULER: Agendador já está em execução.")

def parar():
    """Para o scheduler de forma graciosa."""
    if sched.running:
        try:
            sched.shutdown()
            logger.info("SCHEDULER: Agendador parado.")
        except Exception as e:
            logger.exception(f"SCHEDULER: Erro ao parar o agendador: {e}")

# Importar pytz para lidar com timezones corretamente na inicialização da job
try:
    import pytz
except ImportError:
    logger.error("SCHEDULER: Biblioteca 'pytz' não instalada. Timezones podem não funcionar corretamente. Execute: pip install pytz")
    pytz = None # Define como None para evitar erros posteriores se não conseguir importar

# Certifique-se de chamar iniciar() no startup da sua aplicação FastAPI (main.py)
# e parar() no shutdown.

