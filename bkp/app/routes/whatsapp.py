# ===========================================================
# Arquivo: routes/whatsapp.py
# (Recebe webhooks do WhatsApp e chama nlp.py)
# ===========================================================
from fastapi import APIRouter, Request, Response, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
import logging

# Ajuste os imports conforme a estrutura do seu projeto
# Assume que estão em app/
from app.config import WHATSAPP_VERIFY_TOKEN
from app.utils.mensageria import enviar_mensagem
from app.utils.offnlp import processar_mensagem # Função principal de processamento
from app.utils.contexto import limpar_contexto # Para o comando de reset

# Configuração básica de logging
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Cria um roteador FastAPI para este módulo
router = APIRouter(prefix="/chat", tags=["WhatsApp"]) # Adiciona prefixo e tag

@router.get("/webhook/whatsapp/", summary="Verifica o webhook do WhatsApp")
async def verificar_webhook(request: Request):
    """
    Endpoint GET para verificar o webhook do WhatsApp durante a configuração na plataforma Meta.
    Responde ao desafio 'hub.challenge'.
    """
    args = request.query_params
    mode = args.get("hub.mode")
    token = args.get("hub.verify_token")
    challenge = args.get("hub.challenge")

    # Verifica se o modo e o token de verificação correspondem ao esperado
    if mode == "subscribe" and token == WHATSAPP_VERIFY_TOKEN:
        logging.info("WHATSAPP Route: ✅ Webhook verificado com sucesso!")
        # Retorna o desafio para confirmar a verificação
        return Response(content=challenge, media_type="text/plain", status_code=200)
    else:
        # Se a verificação falhar, retorna um erro 403 (Proibido)
        logging.warning("WHATSAPP Route: ⚠️ Falha na verificação do webhook. Token inválido ou modo incorreto.")
        return Response(content="Falha na verificação", status_code=403)

@router.post("/webhook/whatsapp/", summary="Recebe mensagens do WhatsApp")
async def receber_mensagem_whatsapp(request: Request, background_tasks: BackgroundTasks):
    """
    Endpoint POST para receber notificações de mensagens do WhatsApp via webhook.
    Processa a mensagem em background para responder rapidamente à Meta.
    """
    try:
        # Obtém o corpo JSON da requisição de forma assíncrona
        data = await request.json()
        # logging.debug(f"WHATSAPP Route: Webhook recebido: {json.dumps(data, indent=2)}") # Log detalhado opcional

        # Extrai as informações relevantes da estrutura do webhook
        # Adapte essa extração se a estrutura do payload do webhook mudar
        entry = data.get("entry", [])
        if not entry:
            logging.info("WHATSAPP Route: Webhook recebido sem 'entry'. Ignorando.")
            return Response(status_code=200) # Responde OK para Meta

        changes = entry[0].get("changes", [])
        if not changes:
            logging.info("WHATSAPP Route: Webhook recebido sem 'changes'. Ignorando.")
            return Response(status_code=200)

        value = changes[0].get("value", {})
        messages = value.get("messages", [])
        contacts = value.get("contacts", [])
        statuses = value.get("statuses", []) # Captura eventos de status

        # Prioriza o processamento de mensagens de texto
        if messages and "text" in messages[0] and contacts:
            # Extrai os dados da mensagem e do contato
            mensagem_atual = messages[0]["text"]["body"]
            telefone_usuario = messages[0]["from"]
            # Tenta pegar o nome do perfil, se não existir usa o telefone
            nome_usuario = contacts[0].get("profile", {}).get("name", telefone_usuario)

            logging.info(f"WHATSAPP Route: Recebida mensagem de {nome_usuario} ({telefone_usuario})")
            logging.debug(f"WHATSAPP Route: Mensagem: {mensagem_atual}") # Debug para ver a msg

            # Adiciona o processamento da mensagem à fila de background tasks
            # Isso permite retornar 200 OK rapidamente para a Meta
            background_tasks.add_task(processar_e_responder, telefone_usuario, nome_usuario, mensagem_atual)

            # Retorna 200 OK imediatamente
            return Response(status_code=200)

        # Loga eventos de status (entrega, leitura) - opcional
        elif statuses:
            for status_info in statuses:
                status_type = status_info.get("status")
                recipient_id = status_info.get("recipient_id")
                message_id = status_info.get("id")
                timestamp = status_info.get("timestamp")
                logging.debug(f"WHATSAPP Route: Status recebido para {recipient_id} (Msg ID: {message_id}): {status_type} @ {timestamp}")
            return Response(status_code=200)

        else:
            # Se não for mensagem de texto ou status conhecido, ignora
            logging.info("WHATSAPP Route: 📭 Evento ignorado – sem mensagem de texto válida ou status conhecido.")
            return Response(status_code=200)

    # Tratamento de exceções gerais durante o processamento inicial do webhook
    except json.JSONDecodeError:
        logging.error("WHATSAPP Route: ❌ Erro ao decodificar JSON do webhook.")
        # Retorna 400 Bad Request se o JSON for inválido
        return Response(content="JSON inválido", status_code=400)
    except Exception as e:
        # Loga o erro detalhado que causou a falha
        logging.exception(f"WHATSAPP Route: ❌ ERRO CRÍTICO inicial no webhook:")
        # Retorna um erro 500 (Internal Server Error) para a API do WhatsApp
        # Isso pode fazer com que a Meta tente reenviar o webhook
        return Response(content="Erro interno no servidor", status_code=500)


async def processar_e_responder(telefone: str, nome: str, mensagem: str):
    """
    Função executada em background para processar a mensagem e enviar a resposta.
    """
    try:
        logging.info(f"WHATSAPP BG Task: Iniciando processamento para {telefone}...")
        # --- Tratamento de Comando Especial (Reset) ---
        if mensagem.strip().lower() == "melancia vermelha":
            logging.info(f"WHATSAPP BG Task: Comando de reset 'melancia vermelha' recebido de {telefone}. Limpando contexto...")
            sucesso_limpeza = limpar_contexto(telefone)
            if sucesso_limpeza:
                # Envia confirmação de reset (opcional)
                await enviar_mensagem(telefone, "🔄 Sua conversa foi reiniciada. Pode começar de novo quando quiser.")
            else:
                # Envia mensagem de erro se a limpeza falhar (opcional)
                await enviar_mensagem(telefone, "⚠️ Ocorreu um erro ao tentar reiniciar a conversa. Por favor, tente novamente.")
            logging.info(f"WHATSAPP BG Task: Reset concluído para {telefone}.")
            return # Finaliza a task de background

        # --- Processamento Normal da Mensagem ---
        # Chama a função principal em nlp.py para processar a mensagem
        resultado_processamento = await processar_mensagem(
            mensagem=mensagem,
            telefone=telefone,
            canal="whatsapp" # Define o canal
        )

        # Obtém a resposta a ser enviada ao usuário
        resposta_para_usuario = resultado_processamento.get("resposta")

        # Envia a resposta de volta ao usuário via WhatsApp
        if resposta_para_usuario:
            logging.info(f"WHATSAPP BG Task: Enviando resposta para {telefone}...")
            await enviar_mensagem(telefone, resposta_para_usuario)
        else:
            # Se nlp.py não retornar uma resposta (o que não deveria acontecer)
            logging.warning(f"WHATSAPP BG Task: Função processar_mensagem não retornou 'resposta' para {telefone}. Enviando erro padrão.")
            await enviar_mensagem(telefone, "Desculpe, não consegui processar sua solicitação no momento.")

        logging.info(f"WHATSAPP BG Task: Processamento e resposta concluídos para {telefone}.")

    except Exception as e:
        # Loga qualquer erro que ocorra durante o processamento em background
        logging.exception(f"WHATSAPP BG Task: ❌ ERRO durante processamento para {telefone}:")
        # Considerar enviar uma mensagem de erro para o usuário aqui também?
        # await enviar_mensagem(telefone, "Desculpe, ocorreu um erro interno ao processar sua mensagem.")

# Importar json se não estiver importado
import json
