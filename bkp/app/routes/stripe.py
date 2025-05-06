# ===========================================================
# Arquivo: routes/stripe.py
# (Implementação do webhook do Stripe)
# ===========================================================
from fastapi import APIRouter, Request, Header, HTTPException, BackgroundTasks
import stripe # Importa a biblioteca do Stripe
import logging

# Ajuste os imports conforme a estrutura do seu projeto
from app.config import STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET
# Importa funções de followup e agenda
from app.utils.followup import marcar_pagamento
from app.utils.agenda import formatar_horario_local
# Importa função para salvar contexto e enviar mensagem
from app.utils.contexto import salvar_contexto
from app.utils.mensageria import enviar_mensagem

# Configuração básica de logging
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Cria um roteador FastAPI para este módulo
router = APIRouter(prefix="/webhook", tags=["Stripe"]) # Adiciona prefixo e tag

# Define a chave secreta do Stripe (carregada da configuração)
if STRIPE_SECRET_KEY:
    stripe.api_key = STRIPE_SECRET_KEY
    logging.info("STRIPE Route: Chave secreta do Stripe configurada.")
else:
    logging.error("STRIPE Route: ❌ Chave secreta do Stripe (STRIPE_SECRET_KEY) não configurada. Webhook não funcionará.")
    # A aplicação pode iniciar, mas o webhook falhará

@router.post("/stripe/", summary="Recebe eventos do webhook do Stripe")
async def stripe_webhook(request: Request, background_tasks: BackgroundTasks, stripe_signature: str = Header(None)):
    """
    Endpoint para receber eventos do Stripe via webhook.
    Verifica a assinatura e processa eventos relevantes (ex: checkout.session.completed).
    Processa a lógica principal em background.
    """
    # Verifica se a chave do webhook está configurada
    if not STRIPE_WEBHOOK_SECRET:
        logging.error("STRIPE Route: ❌ Chave secreta do webhook Stripe (STRIPE_WEBHOOK_SECRET) não configurada.")
        raise HTTPException(status_code=500, detail="Configuração de webhook incompleta no servidor.")

    # Obtém o corpo bruto da requisição
    payload = await request.body()

    # Verifica a assinatura do webhook para garantir que veio do Stripe
    try:
        event = stripe.Webhook.construct_event(
            payload, stripe_signature, STRIPE_WEBHOOK_SECRET
        )
        logging.info(f"STRIPE Route: Evento recebido tipo: {event['type']} (ID: {event['id']})")
    except ValueError as e:
        # Payload inválido
        logging.error(f"STRIPE Route: ❌ Erro ao decodificar payload do webhook: {e}")
        raise HTTPException(status_code=400, detail="Payload inválido.")
    except stripe.error.SignatureVerificationError as e:
        # Assinatura inválida
        logging.error(f"STRIPE Route: ❌ Erro na verificação da assinatura do webhook: {e}")
        raise HTTPException(status_code=400, detail="Assinatura inválida.")
    except Exception as e:
        logging.exception("STRIPE Route: ❌ Erro inesperado ao construir evento do webhook:")
        raise HTTPException(status_code=500, detail="Erro interno ao processar webhook.")

    # --- Processamento do Evento (em Background) ---
    # Adiciona a tarefa de processar o evento em background
    background_tasks.add_task(processar_evento_stripe, event)

    # Retorna 200 OK imediatamente para o Stripe
    return {"status": "recebido"}

async def processar_evento_stripe(event: dict):
    """
    Função executada em background para processar o evento do Stripe.
    """
    event_type = event["type"]
    session = event["data"]["object"] # O objeto da sessão de checkout

    logging.info(f"STRIPE BG Task: Processando evento tipo: {event_type} (Sessão ID: {session.get('id', 'N/A')})")

    # --- Evento: Checkout Concluído com Sucesso ---
    if event_type == "checkout.session.completed":
        # Extrai metadados e informações do cliente da sessão Stripe
        metadata = session.get("metadata", {})
        telefone_cliente = metadata.get("telefone")
        nome_cliente_meta = metadata.get("nome") # Nome dos metadados (pode ser mais confiável)

        customer_details = session.get("customer_details", {})
        email_cliente = customer_details.get("email")
        nome_cliente_stripe = customer_details.get("name") # Nome direto do Stripe

        # Usa o nome dos metadados como prioridade, senão o do Stripe
        nome_final = nome_cliente_meta or nome_cliente_stripe or "Cliente"

        id_sessao_stripe = session.get("id")

        # Verifica se temos o telefone (essencial para continuar)
        if not telefone_cliente:
            logging.error(f"STRIPE BG Task: ❌ Evento {event_type} (Sessão: {id_sessao_stripe}) sem 'telefone' nos metadados. Não é possível prosseguir.")
            return # Aborta o processamento

        logging.info(f"STRIPE BG Task: Checkout concluído para {nome_final} ({telefone_cliente}). Sessão: {id_sessao_stripe}")

        # Tenta marcar o pagamento e agendar a consulta
        horario_agendado_utc, nome_agendado = await asyncio.to_thread(
             marcar_pagamento, # Executa a função síncrona em uma thread separada
             telefone=telefone_cliente,
             id_sessao_stripe=id_sessao_stripe,
             email_cliente=email_cliente,
             nome_cliente=nome_final
        )
        # horario_agendado_utc, nome_agendado = marcar_pagamento( # Se marcar_pagamento fosse async
        #     telefone=telefone_cliente,
        #     id_sessao_stripe=id_sessao_stripe,
        #     email_cliente=email_cliente,
        #     nome_cliente=nome_final
        # )


        if horario_agendado_utc:
            # Agendamento bem-sucedido!
            horario_formatado = formatar_horario_local(horario_agendado_utc)
            # Monta mensagem de confirmação para o paciente
            msg_paciente = (
                f"✅ Olá {nome_agendado}, pagamento confirmado!\n\n"
                f"Sua consulta inicial está agendada para:\n"
                f"🗓️ **{horario_formatado}** (Horário de Brasília).\n\n"
                f"O profissional entrará em contato com você por aqui neste horário. Até lá!"
            )
            # Envia a confirmação para o paciente
            await enviar_mensagem(telefone_cliente, msg_paciente)

            # Monta notificação para o médico/equipe (opcional)
            # TODO: Definir número/canal do médico em config.py
            numero_medico = os.getenv("WHATSAPP_MEDICO_AVISO")
            if numero_medico:
                msg_medico = f"👨‍⚕️ Novo agendamento confirmado:\n\nPaciente: {nome_agendado}\nTelefone: {telefone_cliente}\nHorário: {horario_formatado}"
                await enviar_mensagem(numero_medico, msg_medico)

            # --- ATUALIZA O ESTADO DA CONVERSA ---
            # Muda o estado para iniciar o questionário na próxima interação
            logging.info(f"STRIPE BG Task: Atualizando estado para CONFIRMANDO_AGENDAMENTO para {telefone_cliente}")
            salvar_contexto(telefone_cliente, {
                "estado": "CONFIRMANDO_AGENDAMENTO",
                "nome": nome_agendado, # Salva/Atualiza o nome no contexto
                "meta_conversa": {"email_cliente": email_cliente} # Salva email na meta
            })

        else:
            # Falha no agendamento após pagamento
            logging.error(f"STRIPE BG Task: ❌ Pagamento confirmado para {telefone_cliente}, mas FALHA AO AGENDAR consulta.")
            # Envia mensagem de erro para o paciente
            msg_erro_agendamento = (
                f"⚠️ Olá {nome_agendado}, seu pagamento foi confirmado, mas houve um problema ao agendar automaticamente sua consulta.\n\n"
                f"Não se preocupe, nossa equipe já foi notificada e entrará em contato em breve para finalizar o agendamento manualmente. Obrigado pela compreensão."
            )
            await enviar_mensagem(telefone_cliente, msg_erro_agendamento)
            # TODO: Notificar equipe interna sobre a falha no agendamento automático

    # --- Outros Eventos (Opcional) ---
    # elif event_type == "checkout.session.async_payment_failed":
    #     logging.warning(f"STRIPE BG Task: Pagamento assíncrono falhou para sessão {session.get('id')}")
    #     # Lógica para lidar com falha (ex: notificar usuário)
    # elif event_type == "checkout.session.expired":
    #      logging.info(f"STRIPE BG Task: Sessão de checkout expirada: {session.get('id')}")
         # Lógica para lidar com expiração (ex: marcar no DB)

    else:
        # Evento não tratado
        logging.info(f"STRIPE BG Task: Evento tipo '{event_type}' não tratado.")

    logging.info(f"STRIPE BG Task: Processamento do evento concluído.")

# Importar asyncio e json se não estiverem importados
import asyncio
import json
import os # Para getenv
