# ===========================================================
# Arquivo: utils/mensageria.py
# ===========================================================
import httpx
# Ajuste o import se config.py estiver em um diretório diferente
from app.config import WHATSAPP_API_URL, WHATSAPP_TOKEN
import logging

# Configuração básica de logging
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def enviar_mensagem(telefone: str, mensagem: str) -> dict:
    """
    Envia uma mensagem de texto simples via WhatsApp Cloud API.

    Args:
        telefone (str): Número de telefone do destinatário (formato internacional, ex: 55119XXXXXXXX).
        mensagem (str): O texto da mensagem a ser enviada.

    Returns:
        dict: Um dicionário com o status do envio ('enviado', 'erro_api', etc.) e detalhes.
    """
    # Verifica se as configurações essenciais da API estão presentes
    if not WHATSAPP_API_URL or not WHATSAPP_TOKEN:
        logging.error("❌ ERRO MENSAGERIA: Configurações da API do WhatsApp ausentes (URL ou Token).")
        return {"status": "erro_config", "erro": "Configuração da API do WhatsApp incompleta."}
    # Verifica se telefone e mensagem não estão vazios
    if not telefone or not mensagem:
        logging.warning("⚠️ MENSAGERIA: Tentativa de enviar mensagem vazia ou sem destinatário.")
        return {"status": "erro_input", "erro": "Telefone ou mensagem ausente."}

    # Payload da requisição para a API do WhatsApp
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": telefone, # Número do destinatário
        "type": "text",
        "text": {
            "preview_url": False, # Desabilita preview de links (geralmente bom para bots)
            "body": mensagem # O conteúdo da mensagem
        }
    }
    # Cabeçalhos da requisição, incluindo o token de autorização
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }

    # Define um timeout razoável para a chamada da API externa
    timeout = httpx.Timeout(20.0, connect=5.0) # Timeout aumentado ligeiramente

    try:
        # Usa httpx para fazer a chamada POST assíncrona
        async with httpx.AsyncClient(timeout=timeout) as client:
            logging.info(f"Enviando mensagem para {telefone}...")
            response = await client.post(WHATSAPP_API_URL, json=payload, headers=headers)
            # Levanta uma exceção para respostas com erro (status 4xx ou 5xx)
            response.raise_for_status()

            # Log de sucesso
            logging.info(f"✅ Mensagem enviada para {telefone}. Status: {response.status_code}")
            # logging.debug(f"Resposta da API WhatsApp: {response.text}") # Log detalhado opcional
            # Retorna status de sucesso e detalhes da resposta da API
            return {"status": "enviado", "code": response.status_code, "retorno": response.json()} # Retorna JSON

    # Tratamento de exceções específicas do httpx
    except httpx.HTTPStatusError as e:
        # Erro retornado pela API do WhatsApp (ex: número inválido, token expirado)
        logging.error(f"❌ ERRO HTTP MENSAGERIA para {telefone}: Status {e.response.status_code}, Resposta: {e.response.text}")
        return {"status": "erro_api", "code": e.response.status_code, "erro": e.response.text}
    except httpx.TimeoutException as e:
        # Erro de timeout ao tentar conectar ou receber resposta da API
        logging.error(f"❌ ERRO MENSAGERIA: Timeout ao enviar mensagem para {telefone}: {str(e)}")
        return {"status": "erro_timeout", "erro": str(e)}
    except httpx.RequestError as e:
        # Erro de conexão (ex: DNS, rede)
        logging.error(f"❌ ERRO MENSAGERIA: Erro de Conexão ao enviar mensagem para {telefone}: {str(e)}")
        return {"status": "erro_conexao", "erro": str(e)}
    # Tratamento de qualquer outra exceção inesperada
    except Exception as e:
        logging.exception(f"❌ ERRO MENSAGERIA: Erro inesperado ao enviar mensagem para {telefone}:")
        return {"status": "erro_desconhecido", "erro": str(e)}

