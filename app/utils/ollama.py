# ===========================================================
# Arquivo: utils/ollama.py
# ===========================================================
import httpx
import logging
import json
import re
# Ajuste o import se config.py estiver em um diretório diferente
from app.config import OLLAMA_API_URL, OLLAMA_MODEL

# Configuração básica de logging
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def chamar_ollama(prompt: str, telefone: str) -> tuple[str | None, dict | None, list | None]:
    """
    Chama a API do Ollama com o prompt fornecido.
    Tenta extrair um JSON do final da resposta.

    Args:
        prompt (str): O prompt completo a ser enviado para a IA.
        telefone (str): O número de telefone do usuário (para logging).

    Returns:
        tuple[str | None, dict | None, list | None]:
            - resposta_textual (str | None): A parte textual da resposta da IA.
            - json_extraido (dict | None): O dicionário JSON extraído do final, ou None.
            - tokens (list | None): Informações sobre tokens (se a API retornar, atualmente None).
    """
    # Validação inicial
    if not OLLAMA_API_URL or not OLLAMA_MODEL:
        logging.error("❌ OLLAMA: Configurações (OLLAMA_API_URL ou OLLAMA_MODEL) ausentes.")
        return "⚠️ Desculpe, estou com problemas técnicos para acessar minha inteligência. Tente novamente mais tarde.", None, None

    # Payload para a API do Ollama
    payload = {
        "model": OLLAMA_MODEL, # Modelo configurado
        "prompt": prompt,
        "stream": False, # Não usar streaming para facilitar extração do JSON
        # "options": {"temperature": 0.7} # Exemplo de opções de geração
        # Tenta forçar JSON se o prompt explicitamente pedir (pode ser ajustado)
        "format": "json" if "json" in prompt.lower()[-150:] else None # Verifica só o final do prompt por "json"
    }
    # Remove format se for None para não enviar chave vazia
    if payload["format"] is None:
        del payload["format"]

    headers = {"Content-Type": "application/json"}
    resposta_textual = None
    json_extraido = None
    tokens = None # Placeholder para informações de tokens

    try:
        # Usar httpx para chamadas HTTP assíncronas
        # Timeout aumentado para 45 segundos para dar tempo à IA
        async with httpx.AsyncClient(timeout=45.0) as client:
            logging.info(f"OLLAMA: Enviando prompt (modelo: {OLLAMA_MODEL}) para {telefone}...")
            # Faz a requisição POST para a API do Ollama
            response = await client.post(f"{OLLAMA_API_URL}/api/generate", json=payload, headers=headers)
            # Levanta uma exceção para respostas com erro (status 4xx ou 5xx)
            response.raise_for_status()

            dados = response.json()
            logging.info(f"OLLAMA: ✅ Resposta recebida da IA para {telefone}.")
            # logging.debug(f"OLLAMA: Resposta completa: {dados}") # Log detalhado opcional

            # Extrai a resposta principal do JSON retornado pela API
            resposta_bruta = dados.get("response", "").strip()
            # TODO: Extrair informações de tokens se disponíveis em 'dados' (ex: dados.get("eval_count"), etc.)
            # tokens = {"eval_count": dados.get("eval_count"), ...}

            # Verifica se a resposta não está vazia
            if not resposta_bruta:
                logging.warning(f"OLLAMA: ⚠️ Resposta vazia para {telefone}.")
                return None, None, tokens

            # Tenta extrair JSON do final da resposta bruta
            # Primeiro tenta com ```json ... ``` (com ou sem espaço antes do {)
            match = re.search(r"```json\s*(\{[\s\S]*?\})\s*```$", resposta_bruta, re.IGNORECASE | re.DOTALL)
            if not match: # Se não encontrar, tenta apenas com { ... } no final
                 match = re.search(r"(\{[\s\S]*?\})$", resposta_bruta, re.DOTALL)

            if match:
                # Se encontrou um padrão JSON, extrai o conteúdo
                json_str = match.group(1)
                try:
                    # Tenta converter a string JSON em um dicionário Python
                    json_extraido = json.loads(json_str)
                    # Remove a parte JSON (e os ``` se presentes) da resposta textual
                    resposta_textual = resposta_bruta[:match.start()].strip()
                    logging.info(f"OLLAMA: JSON extraído com sucesso para {telefone}.")
                except json.JSONDecodeError as json_err:
                    # Se o JSON for inválido, loga um aviso e trata a resposta inteira como texto
                    logging.warning(f"OLLAMA: ⚠️ JSON inválido no final da resposta para {telefone}: {json_err}. Retornando resposta bruta como textual.")
                    resposta_textual = resposta_bruta
                    json_extraido = None
            else:
                # Se não encontrou JSON no final, toda a resposta é considerada textual
                logging.info(f"OLLAMA: Nenhum JSON encontrado no final da resposta para {telefone}.")
                resposta_textual = resposta_bruta
                json_extraido = None

            # Garante que a resposta textual não seja vazia se o JSON foi extraído com sucesso
            if not resposta_textual and json_extraido is not None:
                 resposta_textual = "Ok." # Retorna um texto mínimo

            return resposta_textual, json_extraido, tokens

    # Tratamento de exceções específicas do httpx e genéricas
    except httpx.TimeoutException as e:
        logging.error(f"OLLAMA: ❌ Erro: Timeout ao chamar para {telefone} ({str(e)})")
        # Retorna uma mensagem de erro amigável para o usuário
        return "⚠️ Desculpe, demorei muito para pensar. Poderia tentar de novo?", None, None
    except httpx.HTTPStatusError as e:
        # Loga o erro HTTP e retorna mensagem de erro
        logging.error(f"OLLAMA: ❌ Erro HTTP {e.response.status_code} para {telefone}: {e.response.text}")
        return f"⚠️ Ocorreu um erro de comunicação com a inteligência artificial ({e.response.status_code}). Por favor, tente mais tarde.", None, None
    except Exception as e:
        # Loga qualquer outro erro inesperado
        logging.exception(f"OLLAMA: ❌ Erro desconhecido ao chamar para {telefone}:")
        return "⚠️ Ocorreu um erro inesperado ao processar sua solicitação. Tente novamente mais tarde.", None, None

