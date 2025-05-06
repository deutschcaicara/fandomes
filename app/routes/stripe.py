# ===========================================================
# Arquivo: routes/stripe.py
# Webhook do Stripe para processar eventos de pagamento.
# - Atualiza o estado do contexto para iniciar a triagem após pagamento.
# - Chama marcar_pagamento que agora também tenta agendar.
# - Envia mensagens de confirmação/erro ao usuário.
# ===========================================================
from fastapi import APIRouter, Request, Header, HTTPException, BackgroundTasks
import stripe # Importa a biblioteca do Stripe
import logging
import asyncio # Para rodar marcar_pagamento em thread se for síncrona
import os # Para variáveis de ambiente opcionais

# Imports da aplicação
from app.config import settings # Usar settings para acesso seguro às configs
from app.utils.followup import marcar_pagamento # Função que marca pago E agenda
from app.utils.agenda import formatar_horario_local # Para formatar horário na msg
from app.utils.contexto import salvar_contexto # Para mudar o estado do usuário
from app.utils.mensageria import enviar_mensagem # Para notificar usuário

logger = logging.getLogger("famdomes.stripe_webhook")

# Cria um roteador FastAPI para este módulo
router = APIRouter(prefix="/webhook", tags=["Stripe"]) # Adiciona prefixo e tag

# --- Configuração do Stripe ---
STRIPE_SECRET_KEY = getattr(settings, "STRIPE_SECRET_KEY", None)
STRIPE_WEBHOOK_SECRET = getattr(settings, "STRIPE_WEBHOOK_SECRET", None)
WHATSAPP_MEDICO_AVISO = getattr(settings, "WHATSAPP_MEDICO_AVISO", None) # Número para notificar médico

if STRIPE_SECRET_KEY:
    stripe.api_key = STRIPE_SECRET_KEY
    logger.info("STRIPE Route: Chave secreta do Stripe configurada.")
else:
    logger.error("STRIPE Route: ❌ Chave secreta do Stripe (STRIPE_SECRET_KEY) não configurada. Webhook NÃO FUNCIONARÁ.")

if not STRIPE_WEBHOOK_SECRET:
     logger.error("STRIPE Route: ❌ Chave secreta do webhook Stripe (STRIPE_WEBHOOK_SECRET) não configurada. Verificação de assinatura FALHARÁ.")


@router.post("/stripe/", summary="Recebe eventos do webhook do Stripe")
async def stripe_webhook(request: Request, background_tasks: BackgroundTasks, stripe_signature: str = Header(None)):
    """
    Endpoint para receber eventos do Stripe via webhook.
    Verifica a assinatura e processa eventos relevantes (ex: checkout.session.completed).
    Delega o processamento pesado para uma task em background.
    """
    # Verifica se a chave do webhook está configurada (essencial para segurança)
    if not STRIPE_WEBHOOK_SECRET:
        logger.critical("STRIPE Route: ❌ Processamento abortado - STRIPE_WEBHOOK_SECRET não configurado no servidor.")
        raise HTTPException(status_code=500, detail="Configuração de webhook incompleta no servidor.")

    # Obtém o corpo bruto da requisição
    payload = await request.body()
    logger.debug(f"STRIPE Route: Payload recebido: {payload[:200]}...") # Log inicial do payload

    # Verifica a assinatura do webhook para garantir que veio do Stripe
    try:
        event = stripe.Webhook.construct_event(
            payload, stripe_signature, STRIPE_WEBHOOK_SECRET
        )
        logger.info(f"STRIPE Route: Evento verificado tipo: {event['type']} (ID: {event['id']})")
    except ValueError as e:
        # Payload inválido
        logger.error(f"STRIPE Route: ❌ Erro ao decodificar payload do webhook (ValueError): {e}")
        raise HTTPException(status_code=400, detail="Payload inválido.")
    except stripe.error.SignatureVerificationError as e:
        # Assinatura inválida
        logger.error(f"STRIPE Route: ❌ Erro na verificação da assinatura do webhook: {e}")
        raise HTTPException(status_code=400, detail="Assinatura inválida.")
    except Exception as e:
        logger.exception("STRIPE Route: ❌ Erro inesperado ao construir evento do webhook:")
        raise HTTPException(status_code=500, detail="Erro interno ao processar webhook.")

    # --- Processamento do Evento (em Background) ---
    # Adiciona a tarefa de processar o evento em background para liberar a resposta rapidamente
    background_tasks.add_task(processar_evento_stripe, event)
    logger.debug(f"STRIPE Route: Tarefa em background adicionada para evento {event['id']}")

    # Retorna 200 OK imediatamente para o Stripe confirmar recebimento
    return {"status": "recebido"}

async def processar_evento_stripe(event: dict):
    """
    Função executada em background para processar o evento do Stripe.
    Foca no evento 'checkout.session.completed'.
    """
    event_type = event["type"]
    try:
        session = event["data"]["object"] # O objeto da sessão de checkout
        session_id = session.get("id", "N/A")
        logger.info(f"STRIPE BG Task: Iniciando processamento para evento tipo: {event_type} (Sessão ID: {session_id})")
    except Exception as e:
        logger.exception(f"STRIPE BG Task: Erro ao acessar dados do evento: {e}")
        return # Não pode continuar sem os dados da sessão

    # --- Evento: Checkout Concluído com Sucesso ---
    if event_type == "checkout.session.completed":
        # Extrai metadados e informações do cliente da sessão Stripe
        metadata = session.get("metadata", {})
        telefone_cliente = metadata.get("telefone")
        nome_cliente_meta = metadata.get("nome") # Nome dos metadados (enviado na criação da sessão)

        customer_details = session.get("customer_details", {})
        email_cliente = customer_details.get("email")
        # O nome pode vir do customer_details se o cliente já existir no Stripe
        nome_cliente_stripe = customer_details.get("name")

        # Define o nome final a ser usado, priorizando metadados
        nome_final = nome_cliente_meta or nome_cliente_stripe or "Cliente" # Fallback

        # Verifica se temos o telefone (essencial para continuar)
        if not telefone_cliente:
            logger.error(f"STRIPE BG Task: ❌ Evento {event_type} (Sessão: {session_id}) SEM 'telefone' nos metadados. Impossível continuar.")
            # Considerar notificar admin sobre pagamento órfão
            return # Aborta o processamento

        logger.info(f"STRIPE BG Task: Checkout concluído para {nome_final} ({telefone_cliente}). Sessão: {session_id}")

        # --- Marca Pagamento e Tenta Agendar ---
        try:
            # Chama a função que atualiza o DB de pagamentos e tenta agendar a consulta
            # ATENÇÃO: Se marcar_pagamento for SÍNCRONA, use asyncio.to_thread
            # horario_agendado_utc, nome_agendado = await asyncio.to_thread(
            #      marcar_pagamento, # Executa a função síncrona em uma thread separada
            #      telefone=telefone_cliente,
            #      id_sessao_stripe=session_id,
            #      email_cliente=email_cliente,
            #      nome_cliente=nome_final
            # )
            # Se marcar_pagamento for ASSÍNCRONA:
            horario_agendado_utc, nome_agendado = await marcar_pagamento(
                telefone=telefone_cliente,
                id_sessao_stripe=session_id,
                email_cliente=email_cliente,
                nome_cliente=nome_final
            )

            # --- Processa Resultado do Agendamento ---
            if horario_agendado_utc:
                # Agendamento bem-sucedido!
                horario_formatado = formatar_horario_local(horario_agendado_utc)
                logger.info(f"STRIPE BG Task: ✅ Agendamento realizado para {telefone_cliente} em {horario_formatado}.")

                # Monta mensagem de confirmação para o paciente
                msg_paciente = (
                    f"✅ Olá {nome_agendado}, pagamento confirmado!\n\n"
                    f"Sua consulta inicial está agendada para:\n"
                    f"🗓️ **{horario_formatado}** (Horário de Brasília).\n\n"
                    f"O profissional entrará em contato com você por aqui neste horário. Até lá!"
                )
                # Envia a confirmação para o paciente
                await enviar_mensagem(telefone_cliente, msg_paciente)

                # Notifica o médico/equipe (opcional)
                if WHATSAPP_MEDICO_AVISO:
                    try:
                        msg_medico = f"👨‍⚕️ Novo agendamento confirmado:\nPaciente: {nome_agendado}\nTelefone: {telefone_cliente}\nHorário: {horario_formatado}"
                        await enviar_mensagem(WHATSAPP_MEDICO_AVISO, msg_medico)
                        logger.info(f"STRIPE BG Task: Notificação de agendamento enviada para {WHATSAPP_MEDICO_AVISO}.")
                    except Exception as notify_err:
                        logger.error(f"STRIPE BG Task: Falha ao enviar notificação para médico ({WHATSAPP_MEDICO_AVISO}): {notify_err}")

                # --- ATUALIZA O ESTADO DA CONVERSA (MUITO IMPORTANTE) ---
                # Muda o estado para que o Orquestrador saiba que a próxima interação
                # deve iniciar o questionário de triagem.
                logger.info(f"STRIPE BG Task: Atualizando estado para 'TRIAGEM_INICIAL' para {telefone_cliente}")
                sucesso_save = salvar_contexto(
                    telefone=telefone_cliente,
                    estado="TRIAGEM_INICIAL", # Estado que o Orquestrador usará para chamar DomoTriagem
                    meta_conversa={"email_cliente": email_cliente, "nome_cliente": nome_agendado} # Atualiza meta com dados do pagamento
                )
                if not sucesso_save:
                     logger.error(f"STRIPE BG Task: ❌ FALHA CRÍTICA ao atualizar estado para TRIAGEM_INICIAL para {telefone_cliente} após pagamento.")
                     # Considerar notificar admin

            else:
                # Falha no agendamento após pagamento (marcar_pagamento retornou None para horário)
                logger.error(f"STRIPE BG Task: ❌ Pagamento confirmado para {telefone_cliente}, mas FALHA AO AGENDAR consulta (marcar_pagamento falhou).")
                # Envia mensagem de erro para o paciente
                msg_erro_agendamento = (
                    f"⚠️ Olá {nome_agendado or nome_final}, seu pagamento foi confirmado, mas houve um problema ao agendar automaticamente sua consulta.\n\n"
                    f"Não se preocupe, nossa equipe já foi notificada e entrará em contato em breve para finalizar o agendamento manualmente. Obrigado pela compreensão."
                )
                await enviar_mensagem(telefone_cliente, msg_erro_agendamento)
                # TODO: Implementar notificação para equipe interna sobre a falha no agendamento automático

        except Exception as proc_err:
            logger.exception(f"STRIPE BG Task: ❌ Erro inesperado ao processar pagamento/agendamento para sessão {session_id} (Telefone: {telefone_cliente}): {proc_err}")
            # Enviar mensagem de erro genérica, se possível
            try:
                 await enviar_mensagem(telefone_cliente, "Desculpe, tivemos um problema interno ao processar seu pagamento e agendamento. Nossa equipe verificará.")
            except Exception:
                 logger.error(f"STRIPE BG Task: Falha ao enviar mensagem de erro genérica para {telefone_cliente} após erro de processamento.")

    # --- Outros Eventos (Opcional) ---
    # elif event_type == "checkout.session.async_payment_failed":
    #     logger.warning(f"STRIPE BG Task: Pagamento assíncrono falhou para sessão {session_id}")
    #     # Lógica para lidar com falha (ex: notificar usuário)
    # elif event_type == "checkout.session.expired":
    #      logger.info(f"STRIPE BG Task: Sessão de checkout expirada: {session_id}")
         # Lógica para lidar com expiração (ex: marcar no DB, talvez enviar follow-up)

    else:
        # Evento não tratado explicitamente
        logger.info(f"STRIPE BG Task: Evento tipo '{event_type}' (Sessão: {session_id}) recebido, mas não tratado.")

    logger.info(f"STRIPE BG Task: Processamento do evento {event_type} (Sessão: {session_id}) concluído.")

