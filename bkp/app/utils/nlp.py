# ===========================================================
# Arquivo: utils/nlp.py
# (v7 - Implementada a nova estratégia de fluxo inicial)
# ===========================================================
import logging
import json
import re
import os # Importado para carregar prompt
from datetime import datetime

# Ajuste os imports conforme a estrutura do seu projeto
from app.utils.ollama import chamar_ollama
# Acesso direto às variáveis globais de contexto.py para DB
from app.utils.contexto import (
    obter_contexto, salvar_contexto, salvar_resposta_ia,
    respostas_ia_db # Acesso à coleção do histórico
)
from app.utils.faq_respostas import FAQ_RESPOSTAS
from app.utils.risco import analisar_risco
from app.routes.ia import processar_comando # Para ações como agendar
from app.config import (
    WHATSAPP_FAMILIAR, BASE_DIR, # Importa o número para notificação e diretório base
    ROCKETCHAT_URL, ROCKETCHAT_TOKEN, ROCKETCHAT_USER_ID, # Configs para RocketChat
    OLLAMA_API_URL # Necessário para checar se Ollama está configurado
)
from app.utils.mensageria import enviar_mensagem # Para enviar notificações
from app.utils.questionario_pos_pagamento import QUESTIONARIO_COMPLETO_POS_PAGAMENTO # Importa a lista correta
import httpx # Para notificação RocketChat

# Configuração básica de logging
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Constantes e Textos Padrão ---
# MENSAGEM_INICIAL = '''🧠 Olá! Eu sou a Domo, da FAMDOMES. Estou aqui para escutar e ajudar. Como posso te auxiliar hoje?''' # Nova versão da estratégia
MENSAGEM_INICIAL = '''🧠 Olá! Eu sou a Domo, da FAMDOMES. Estou aqui para escutar e ajudar. Como posso te auxiliar hoje?''' # Mantendo a original por enquanto, ajustar se necessário
# Mensagem combinada (Validação + Emocional + Qualificação) - A validação será adicionada dinamicamente
PERGUNTA_COMBINADA_TEMPLATE = "Como você está se sentindo com toda essa situação neste momento? E só para eu direcionar melhor, a ajuda que você busca é para você mesmo ou para outra pessoa (ex: filho, esposa, irmão)?"
RESPOSTA_EXPLICACAO_CONSULTA = '''👨‍⚕️ A consulta médica do FAMDOMES é online, com um profissional que entende profundamente casos de dependência química e sofrimento familiar.

📌 Ela serve para avaliar a situação, oferecer um laudo se necessário, orientar o melhor caminho e — se for o caso — encaminhar para uma clínica parceira com segurança e sigilo.

💳 O valor é R$100 e pode ser pago online de forma rápida.

Posso te enviar o link para agendar agora?'''
MENSAGEM_AGRADECIMENTO_ONBOARDING = "Obrigado por compartilhar essas informações, elas são muito importantes para a consulta."
MENSAGEM_ERRO_PADRAO = "🤖 Desculpe, não consegui processar sua mensagem agora. Poderia tentar novamente ou reformular?"
MENSAGEM_ERRO_IA = "🤖 Oi! Houve um erro aqui ao pensar. Tenta de novo por favor?"
MENSAGEM_RISCO_DIRECIONAMENTO = "Percebi que você pode estar passando por um momento muito difícil. Se precisar de ajuda urgente, ligue para o CVV (188) ou SAMU (192). Não hesite em buscar apoio."
MENSAGEM_PEDIDO_HUMANO_CONFIRMACAO = "Entendido. Já notifiquei nossa equipe. Alguém entrará em contato com você por aqui assim que possível."

RESPOSTAS_AFIRMATIVAS = ["sim", "claro", "quero", "vamos", "ok", "pode ser", "tá bom", "aceito", "sim por favor", "sim quero", "com certeza", "tô dentro", "pode sim", "por favor", "gostaria", "desejo"]
RESPOSTAS_NEGATIVAS = ["não", "nao", "agora não", "talvez depois", "ainda não", "obrigado não", "não quero", "nao quero"]
PALAVRAS_CHAVE_HUMANO = ["humano", "atendente", "pessoa", "falar com alguem", "alguém", "falar com um especialista", "falar com vc", "falar contigo"]
# ----------------------------------

# --- Funções Auxiliares Implementadas ---

async def analisar_sentimento(texto: str, telefone: str) -> str | None:
    """
    [Trilha Emocional] Analisa o sentimento do texto usando Ollama.
    Retorna 'positivo', 'negativo', 'neutro' ou None em caso de erro.
    """
    if not OLLAMA_API_URL:
        logging.warning("NLP: Análise de sentimento pulada - OLLAMA_API_URL não configurado.")
        return "neutro"

    logging.info(f"NLP: [Trilha Emocional] Analisando sentimento para {telefone}: '{texto[:30]}...'")
    prompt_sentimento = f"""
    Analise o sentimento predominante na seguinte mensagem do usuário.
    Responda APENAS com uma das seguintes palavras: 'positivo', 'negativo', 'neutro'.

    Mensagem: "{texto}"

    Sentimento:"""
    try:
        resposta_txt, _, _ = await chamar_ollama(prompt_sentimento, telefone)
        if resposta_txt:
            sentimento_retornado = resposta_txt.strip().lower().replace(".", "")
            if sentimento_retornado in ["positivo", "negativo", "neutro"]:
                logging.info(f"NLP: Sentimento detectado pela IA para {telefone}: {sentimento_retornado}")
                return sentimento_retornado
            else:
                logging.warning(f"NLP: Sentimento retornado pela IA não reconhecido ('{sentimento_retornado}'). Usando 'neutro'.")
                return "neutro"
        else:
            logging.warning(f"NLP: IA não retornou resposta para análise de sentimento de {telefone}. Usando 'neutro'.")
            return "neutro"
    except Exception as e:
        logging.error(f"NLP: Erro ao chamar IA para análise de sentimento de {telefone}: {e}")
        return None

async def buscar_historico_formatado(telefone: str, limite: int = 5) -> str:
     """ Busca e formata o histórico recente do MongoDB para o prompt da IA. """
     if respostas_ia_db is None:
         logging.warning(f"NLP: Histórico indisponível para {telefone} (DB não conectado).")
         return "Histórico indisponível (DB não conectado)."
     logging.debug(f"NLP: Buscando histórico para {telefone} (limite: {limite})")
     try:
         historico_cursor = respostas_ia_db.find(
             {"telefone": telefone},
             {"mensagem_usuario": 1, "resposta_gerada": 1, "_id": 0}
         ).sort("criado_em", -1).limit(limite)
         historico_lista = list(historico_cursor)
         historico_lista.reverse()
         if not historico_lista:
             return "Nenhuma conversa anterior registrada."
         historico_formatado = ""
         for item in historico_lista:
             if msg_usr := item.get("mensagem_usuario"):
                 historico_formatado += f"Usuário: {msg_usr}\n"
             if msg_bot := item.get("resposta_gerada"):
                 if len(msg_bot) > 150:
                      msg_bot = msg_bot[:150] + "..."
                 historico_formatado += f"Assistente: {msg_bot}\n"
         return historico_formatado.strip()
     except Exception as e:
         logging.error(f"NLP: Erro ao buscar histórico para {telefone}: {e}")
         return "Erro ao carregar histórico."

async def construir_prompt_para_ia(telefone: str, pergunta_atual: str, estado: str, meta_conversa: dict) -> str:
     """
     Constrói o prompt para o Ollama, incorporando estado, histórico e contexto emocional.
     Carrega o prompt mestre do arquivo PROMPT_MESTRE.txt.
     """
     historico_recente_formatado = await buscar_historico_formatado(telefone)
     sentimento_anterior = meta_conversa.get("ultimo_sentimento_detectado", None)
     prompt_mestre_path = os.path.join(BASE_DIR, "PROMPT_MESTRE.txt")
     try:
         with open(prompt_mestre_path, "r", encoding="utf-8") as f:
             PROMPT_MESTRE = f.read().strip()
     except Exception as e:
         logging.error(f"NLP: Erro ao carregar prompt mestre de {prompt_mestre_path}: {e}. Usando prompt padrão.")
         PROMPT_MESTRE = """Você é Domo, um assistente virtual empático da FAMDOMES. Responda com clareza e empatia."""

     meta_filtrada = {
         k: v for k, v in meta_conversa.items()
         if k not in ['questionario_completo', 'historico_recente_formatado'] and not k.startswith('sentimento_q')
     }

     prompt_final = f"""{PROMPT_MESTRE}

     ---
     Contexto da Conversa Atual:
     Telefone: {telefone}
     Estado da Conversa: {estado}
     Sentimento Percebido na Última Interação: {sentimento_anterior or 'N/A'}
     Dados Conhecidos (meta_conversa): {json.dumps(meta_filtrada, indent=2, ensure_ascii=False, default=str)}
     ---
     Histórico Recente da Conversa:
     {historico_recente_formatado}
     ---
     Nova Mensagem do Usuário:
     {pergunta_atual.strip()}
     ---
     Instruções para sua Resposta OBRIGATÓRIAS:
     1. Analise a 'Nova Mensagem do Usuário' considerando o 'Contexto da Conversa Atual'.
     2. Responda em português brasileiro, de forma EMPÁTICA e ACOLHEDORA, especialmente se o sentimento detectado for negativo.
     3. Mantenha o foco nos serviços da FAMDOMES (consulta, tratamento de dependência química).
     4. Siga o fluxo indicado pelo 'Estado da Conversa'. Se for 'SUPORTE_FAQ', responda a dúvida. Se for 'AGUARDANDO_RESPOSTA_QUALIFICACAO', processe a resposta e siga para explicar a consulta ou responder dúvidas. Se for outro estado, guie o usuário para o próximo passo lógico.
     5. Use no máximo 400 caracteres na sua resposta textual.
     6. AO FINAL DA SUA RESPOSTA DE TEXTO, inclua OBRIGATORIAMENTE um JSON VÁLIDO contendo:
        - "intent": A intenção principal que você identificou na mensagem do usuário (ex: "duvida_preco", "confirmou_agendamento", "relato_sentimento", "pergunta_tratamento", "resposta_qualificacao", "desconhecida").
        - "sentimento_detectado": O sentimento predominante na mensagem do usuário (ex: "positivo", "negativo", "neutro", "ansioso", "esperançoso", "frustrado", "confuso").
        - "entidades": Um dicionário com quaisquer entidades relevantes extraídas (ex: {{"nome_paciente": "Carlos", "substancia": "álcool", "para_quem": "filho"}}). Se não houver, use {{}}.
     Exemplo de JSON OBRIGATÓRIO no final:
     ```json
     {{"intent": "duvida_preco", "sentimento_detectado": "ansioso", "entidades": {{}} }}
     ```
     Outro Exemplo:
     ```json
     {{"intent": "resposta_qualificacao", "sentimento_detectado": "negativo", "entidades": {{"para_quem": "filho"}} }}
     ```
     ---
     Assistente (responda aqui e adicione o JSON obrigatório no final):"""
     logging.info(f"NLP: Prompt construído para {telefone} (Estado: {estado}). Tamanho: {len(prompt_final)} chars.")
     return prompt_final

async def notificar_risco(telefone: str, mensagem: str, analise: dict):
    """ Envia notificação de risco para o número configurado. """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    alerta = f"⚠️ ALERTA DE RISCO ({timestamp}) ⚠️\n\nTelefone: {telefone}\nMensagem: \"{mensagem}\"\nAnálise: {analise}\n\nRevisão humana URGENTE necessária."
    logging.warning(f"NLP: Enviando alerta de risco para {WHATSAPP_FAMILIAR}...")
    if WHATSAPP_FAMILIAR:
        try:
            resultado_envio = await enviar_mensagem(WHATSAPP_FAMILIAR, alerta)
            if resultado_envio.get("status") == "enviado" or resultado_envio.get("code") == 200:
                 logging.info(f"NLP: ✅ Alerta de risco enviado com sucesso para {WHATSAPP_FAMILIAR}.")
            else:
                 logging.error(f"NLP: ❌ Falha ao enviar alerta de risco para {WHATSAPP_FAMILIAR}: {resultado_envio.get('erro', resultado_envio)}")
        except Exception as e:
            logging.error(f"NLP: ❌ Exceção ao tentar enviar alerta de risco: {e}")
    else:
        logging.warning("NLP: WHATSAPP_FAMILIAR não configurado. Não foi possível enviar alerta de risco.")

async def notificar_escalacao_humana(telefone: str, contexto: dict):
    """ Envia notificação para a equipe sobre pedido de atendente humano via RocketChat. """
    if not ROCKETCHAT_URL or not ROCKETCHAT_TOKEN or not ROCKETCHAT_USER_ID:
        logging.error("NLP: ❌ Configurações do RocketChat incompletas. Não é possível notificar a equipe.")
        return

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    estado_anterior = contexto.get("estado", "N/A")
    nome_contato = contexto.get("meta_conversa", {}).get("nome_paciente", contexto.get("nome", "Desconhecido"))
    respostas_recentes = {k: v for k, v in contexto.get('meta_conversa', {}).items() if k.startswith('resposta_q')}
    contexto_resumido = json.dumps(respostas_recentes, indent=2, ensure_ascii=False, default=str)
    if len(contexto_resumido) > 1000:
        contexto_resumido = contexto_resumido[:1000] + "\n... (truncado)"

    mensagem_notificacao = (
        f"🙋 **Pedido de Atendimento Humano** ({timestamp}) 🙋\n\n"
        f"**Telefone:** {telefone}\n"
        f"**Nome Contato:** {nome_contato}\n"
        f"**Estado Anterior:** {estado_anterior}\n\n"
        f"**Últimas Respostas (Questionário/Meta):**\n"
        f"```json\n{contexto_resumido}\n```\n\n"
        f"Por favor, assumir a conversa."
    )
    logging.warning(f"NLP: 🙋 PEDIDO HUMANO ({timestamp}) - Telefone: {telefone} | Notificando equipe via RocketChat...")

    headers = {
        "X-Auth-Token": ROCKETCHAT_TOKEN,
        "X-User-Id": ROCKETCHAT_USER_ID,
        "Content-Type": "application/json"
    }
    room_id_destino = os.getenv("ROCKETCHAT_ROOM_ID_SUPORTE", "GENERAL")
    payload = {"message": {"rid": room_id_destino, "msg": mensagem_notificacao}}
    post_message_url = f"{ROCKETCHAT_URL}/api/v1/chat.postMessage"

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(post_message_url, headers=headers, json=payload)
            response.raise_for_status()
            resposta_api = response.json()
            if resposta_api.get("success"):
                logging.info(f"NLP: ✅ Notificação de escalação enviada com sucesso para RocketChat (Sala: {room_id_destino}).")
            else:
                logging.error(f"NLP: ❌ Falha ao enviar notificação para RocketChat (Sala: {room_id_destino}). Resposta API: {resposta_api}")
    except httpx.HTTPStatusError as e:
        logging.error(f"NLP: ❌ Erro HTTP {e.response.status_code} ao enviar para RocketChat: {e.response.text}")
    except httpx.RequestError as e:
        logging.error(f"NLP: ❌ Erro de conexão ao enviar para RocketChat: {e}")
    except Exception as e:
        logging.exception("NLP: ❌ Erro inesperado ao enviar notificação para RocketChat:")


# --- Função Principal de Processamento ---

async def processar_mensagem(mensagem: str, telefone: str, canal: str) -> dict:
    """
    Processa a mensagem do usuário com base no estado atual da conversa,
    realiza análise de sentimento/risco, atualiza o estado e retorna a resposta.
    """
    global meta_conversa
    logging.info(f"NLP: 🔄 Processando mensagem de {telefone}...")
    contexto = obter_contexto(telefone)
    estado_atual = contexto.get("estado", "INICIAL")
    meta_conversa = contexto.get("meta_conversa", {})
    texto_mensagem = mensagem.strip()
    texto_lower = texto_mensagem.lower()

    if not isinstance(meta_conversa, dict):
        logging.warning(f"NLP: Meta conversa para {telefone} não era um dicionário. Resetando para {{}}.")
        meta_conversa = {}

    logging.info(f"NLP: 📞 Telefone: {telefone} | Estado Atual: {estado_atual} | Mensagem: '{texto_mensagem[:50]}...'")

    # --- 1. Análise de Risco ---
    analise_risco_resultado = analisar_risco(texto_mensagem)
    risco_detectado = analise_risco_resultado.get("risco_vida") or analise_risco_resultado.get("urgencia_medica")

    if risco_detectado:
        logging.warning(f"NLP: 🚨 RISCO DETECTADO para {telefone}! Análise: {analise_risco_resultado}")
        novo_estado = "RISCO_DETECTADO"
        resposta_final = MENSAGEM_RISCO_DIRECIONAMENTO
        meta_conversa["ultimo_risco"] = datetime.utcnow().isoformat()
        salvar_contexto(telefone, {"estado": novo_estado, "meta_conversa": meta_conversa})
        salvar_resposta_ia(telefone, canal, texto_mensagem, resposta_final, "risco_detectado", meta_conversa, True, None)
        await notificar_risco(telefone, texto_mensagem, analise_risco_resultado)
        return {"resposta": resposta_final, "estado": novo_estado}

    # --- 2. Verificação de Comandos Especiais ---
    if texto_lower == "melancia vermelha":
        logging.info(f"NLP: Comando 'melancia vermelha' recebido de {telefone}. Resetando contexto.")
        limpar_contexto(telefone)
        resposta_final = MENSAGEM_INICIAL # Envia apenas a saudação inicial após reset
        novo_estado = "IDENTIFICANDO_NECESSIDADE" # Espera a primeira resposta do usuário
        intent = "reset_comando_e_inicio"
        meta_conversa = {}
        salvar_contexto(telefone, {"estado": novo_estado, "meta_conversa": {}})
        salvar_resposta_ia(telefone, canal, texto_mensagem, resposta_final, intent, {}, False, None)
        return {"resposta": resposta_final, "estado": novo_estado}

    if any(palavra in texto_lower for palavra in PALAVRAS_CHAVE_HUMANO):
         logging.info(f"NLP: Pedido de atendente humano detectado para {telefone}.")
         estado_antes_pedido = estado_atual
         novo_estado = "AGUARDANDO_ATENDENTE"
         resposta_final = MENSAGEM_PEDIDO_HUMANO_CONFIRMACAO
         contexto_para_notificacao = contexto.copy()
         contexto_para_notificacao["estado"] = estado_antes_pedido
         salvar_contexto(telefone, {"estado": novo_estado, "meta_conversa": meta_conversa})
         salvar_resposta_ia(telefone, canal, texto_mensagem, resposta_final, "pedido_humano", meta_conversa, False, None)
         await notificar_escalacao_humana(telefone, contexto_para_notificacao)
         return {"resposta": resposta_final, "estado": novo_estado}

    # --- 3. Lógica Baseada no Estado Atual ---
    resposta_final = MENSAGEM_ERRO_PADRAO
    novo_estado = estado_atual
    intent = "desconhecida"
    entidades = {}
    sentimento = await analisar_sentimento(texto_mensagem, telefone)
    if meta_conversa is not None:
        meta_conversa["ultimo_sentimento_detectado"] = sentimento
    else:
        meta_conversa = {"ultimo_sentimento_detectado": sentimento}

    try:
        # Lógica para estado INICIAL (Bot acabou de enviar a saudação)
        # Não deveria receber mensagem do usuário neste estado, mas por segurança:
        if estado_atual == "INICIAL":
            logging.warning(f"NLP: Mensagem recebida no estado INICIAL de {telefone}. Tratando como IDENTIFICANDO_NECESSIDADE.")
            estado_atual = "IDENTIFICANDO_NECESSIDADE" # Força a transição

        # Lógica para IDENTIFICANDO_NECESSIDADE (Usuário respondeu à saudação inicial)
        if estado_atual == "IDENTIFICANDO_NECESSIDADE":
            # Validação simples (pode ser melhorada com IA se necessário)
            validacao = "Entendi. " # Validação genérica inicial
            if sentimento == "negativo":
                validacao = "Sinto muito que esteja se sentindo assim. "
            elif sentimento == "positivo":
                 validacao = "Que bom ouvir isso. "

            # Constrói a pergunta combinada
            resposta_final = validacao + PERGUNTA_COMBINADA_TEMPLATE
            novo_estado = "AGUARDANDO_RESPOSTA_QUALIFICACAO"
            intent = "primeira_resposta_usuario" # Intent da mensagem recebida (pode ser refinado)

        # Lógica para AGUARDANDO_RESPOSTA_QUALIFICACAO (Usuário respondeu à pergunta combinada)
        elif estado_atual == "AGUARDANDO_RESPOSTA_QUALIFICACAO":
            logging.info(f"NLP: Processando resposta de qualificação de {telefone}.")
            meta_conversa["sentimento_resposta_qualificacao"] = sentimento
            # Tenta extrair para quem é a ajuda usando IA ou regras simples
            # Exemplo com regras simples (melhorar com IA/extração de entidades no prompt)
            para_quem = "desconhecido"
            if "filho" in texto_lower or "filha" in texto_lower:
                para_quem = "filho(a)"
            elif "esposo" in texto_lower or "marido" in texto_lower:
                para_quem = "esposo"
            elif "esposa" in texto_lower or "mulher" in texto_lower:
                 para_quem = "esposa"
            elif "irmão" in texto_lower or "irma" in texto_lower:
                 para_quem = "irmao(a)"
            elif "amigo" in texto_lower or "amiga" in texto_lower:
                 para_quem = "amigo(a)"
            elif "para mim" in texto_lower or "eu mesmo" in texto_lower or "pra mim" in texto_lower:
                 para_quem = "proprio_usuario"
            meta_conversa["para_quem"] = para_quem
            entidades["para_quem"] = para_quem # Salva entidade específica desta interação

            # Validação da resposta emocional
            agradecimento = "Obrigado por compartilhar." if sentimento != "negativo" else "Agradeço a confiança em compartilhar."

            # Decide o próximo passo
            # Se perguntou preço especificamente, responde primeiro
            if "preço" in texto_lower or "valor" in texto_lower or "custo" in texto_lower:
                 resposta_final = f"{agradecimento} A consulta inicial online tem o valor de R$100. Ela é importante para avaliar o caso e definir o melhor caminho. Gostaria que eu explicasse mais sobre como ela funciona?"
                 novo_estado = "SUPORTE_FAQ" # Fica em suporte após responder preço
                 intent = "resposta_qualificacao_com_preco"
            else:
                 # Se não pediu preço, explica a consulta
                 if para_quem != "desconhecido" and para_quem != "proprio_usuario":
                      resposta_final = f"{agradecimento} Entendi que a busca é para {para_quem}. Para esses casos, o primeiro passo recomendado é a nossa consulta inicial online.\n\n" + RESPOSTA_EXPLICACAO_CONSULTA
                 else: # Se for para o próprio usuário ou desconhecido
                      resposta_final = f"{agradecimento} Sabendo que a ajuda é para você (ou se ainda não tiver certeza, a consulta ajuda a definir), o caminho inicial que oferecemos é a consulta de avaliação online.\n\n" + RESPOSTA_EXPLICACAO_CONSULTA
                 novo_estado = "EXPLICANDO_CONSULTA"
                 intent = "resposta_qualificacao_segue_fluxo"


        # Lógica para EXPLICANDO_CONSULTA (Usuário respondeu à explicação da consulta)
        elif estado_atual == "EXPLICANDO_CONSULTA":
             if texto_lower in RESPOSTAS_AFIRMATIVAS:
                 logging.info(f"NLP: Usuário {telefone} confirmou interesse em agendar.")
                 meta_conversa["sentimento_confirmacao_agendamento"] = sentimento
                 try:
                     nome_cliente = contexto.get("nome", meta_conversa.get("nome_paciente", "Cliente"))
                     resultado_comando = await processar_comando({
                         "telefone": telefone,
                         "nome": nome_cliente,
                         "comando": "quero agendar"
                     })
                     resposta_final = resultado_comando.get("mensagem", "Link para pagamento enviado!")
                     if resultado_comando.get("status") == "link_gerado":
                          novo_estado = "AGUARDANDO_PAGAMENTO"
                          intent = "confirmou_agendamento"
                     else:
                          resposta_final = resultado_comando.get("mensagem", MENSAGEM_ERRO_PADRAO)
                          novo_estado = "EXPLICANDO_CONSULTA"
                          intent = "erro_gerar_link"
                 except Exception as e:
                     logging.error(f"NLP: Erro ao processar comando 'quero agendar' para {telefone}: {e}")
                     resposta_final = MENSAGEM_ERRO_PADRAO
                     novo_estado = "EXPLICANDO_CONSULTA"
                     intent = "erro_processar_comando"

             elif texto_lower in RESPOSTAS_NEGATIVAS:
                 logging.info(f"NLP: Usuário {telefone} recusou o agendamento por enquanto.")
                 meta_conversa["sentimento_recusa_agendamento"] = sentimento
                 resposta_final = "Entendido. Sem problemas. Se mudar de ideia ou tiver mais alguma dúvida, estou à disposição!"
                 novo_estado = "SUPORTE_FAQ"
                 intent = "recusou_agendamento"
             else:
                 logging.info(f"NLP: Resposta não conclusiva em EXPLICANDO_CONSULTA para {telefone}. Usando IA.")
                 novo_estado = "SUPORTE_FAQ"
                 # IA será chamada no fallback

        # Lógica para AGUARDANDO_PAGAMENTO
        elif estado_atual == "AGUARDANDO_PAGAMENTO":
             logging.info(f"NLP: Mensagem recebida de {telefone} enquanto aguarda pagamento. Encaminhando para IA.")
             resposta_final = "Recebi sua mensagem enquanto aguardo a confirmação do pagamento. Se tiver alguma dúvida sobre o processo ou outra questão, pode perguntar."
             novo_estado = "SUPORTE_FAQ"
             # IA será chamada no fallback

        # Lógica para CONFIRMANDO_AGENDAMENTO
        elif estado_atual == "CONFIRMANDO_AGENDAMENTO":
             logging.info(f"NLP: Iniciando questionário pós-pagamento para {telefone}")
             meta_conversa["questionario_completo"] = QUESTIONARIO_COMPLETO_POS_PAGAMENTO
             meta_conversa["num_pergunta_atual"] = 0
             if QUESTIONARIO_COMPLETO_POS_PAGAMENTO:
                 proxima_pergunta = QUESTIONARIO_COMPLETO_POS_PAGAMENTO[0]
                 resposta_final = proxima_pergunta
                 novo_estado = "COLETANDO_RESPOSTA_QUESTIONARIO"
                 intent = "iniciou_questionario"
                 salvar_contexto(telefone, {
                     "estado": novo_estado,
                     "meta_conversa": meta_conversa,
                     "ultima_resposta_bot": resposta_final
                 })
                 salvar_resposta_ia(telefone, canal, "Sistema: Iniciou Questionário", resposta_final, intent, meta_conversa, False, None)
                 return {"resposta": resposta_final, "estado": novo_estado}
             else:
                 logging.warning(f"NLP: Questionário pós-pagamento vazio para {telefone}. Finalizando onboarding.")
                 resposta_final = MENSAGEM_AGRADECIMENTO_ONBOARDING
                 novo_estado = "FINALIZANDO_ONBOARDING"
                 intent = "questionario_vazio"


        # Lógica para COLETANDO_RESPOSTA_QUESTIONARIO
        elif estado_atual == "COLETANDO_RESPOSTA_QUESTIONARIO":
             num_pergunta_respondida_idx = meta_conversa.get("num_pergunta_atual", 0)
             perguntas_questionario = meta_conversa.get("questionario_completo", [])

             if not isinstance(perguntas_questionario, list):
                 logging.error(f"NLP: Erro: 'questionario_completo' não é uma lista no contexto de {telefone}")
                 perguntas_questionario = []

             if num_pergunta_respondida_idx < len(perguntas_questionario):
                 pergunta_respondida_texto = perguntas_questionario[num_pergunta_respondida_idx]
                 chave_resposta = f"resposta_q{num_pergunta_respondida_idx+1}"
                 chave_sentimento = f"sentimento_q{num_pergunta_respondida_idx+1}"
                 meta_conversa[chave_resposta] = texto_mensagem
                 meta_conversa[chave_sentimento] = sentimento
                 logging.info(f"NLP: Resposta Q{num_pergunta_respondida_idx+1} ('{pergunta_respondida_texto[:30]}...') salva para {telefone}. Sentimento: {sentimento}")

                 num_proxima_pergunta_idx = num_pergunta_respondida_idx + 1
                 meta_conversa["num_pergunta_atual"] = num_proxima_pergunta_idx

                 if num_proxima_pergunta_idx < len(perguntas_questionario):
                     proxima_pergunta_texto = perguntas_questionario[num_proxima_pergunta_idx]
                     resposta_final = proxima_pergunta_texto
                     novo_estado = "COLETANDO_RESPOSTA_QUESTIONARIO"
                     intent = f"respondeu_questionario_{num_pergunta_respondida_idx+1}"
                 else:
                     resposta_final = MENSAGEM_AGRADECIMENTO_ONBOARDING
                     novo_estado = "FINALIZANDO_ONBOARDING"
                     intent = "finalizou_questionario"
                     meta_conversa.pop("num_pergunta_atual", None)
                     meta_conversa.pop("questionario_completo", None)
                     logging.info(f"NLP: Questionário finalizado para {telefone}.")
             else:
                 logging.error(f"NLP: Erro de lógica no questionário para {telefone}. Estado: {estado_atual}, Contador: {num_pergunta_respondida_idx}, Total Perguntas: {len(perguntas_questionario)}")
                 resposta_final = MENSAGEM_ERRO_PADRAO
                 novo_estado = "SUPORTE_FAQ"
                 intent = "erro_logica_questionario"


        # --- 4. Fallback com IA ---
        if novo_estado == estado_atual and estado_atual not in ["RISCO_DETECTADO", "AGUARDANDO_ATENDENTE", "FINALIZANDO_ONBOARDING", "CONFIRMANDO_AGENDAMENTO"]:
            logging.info(f"NLP: Nenhuma regra específica tratou a mensagem de {telefone} no estado {estado_atual}. Usando IA como fallback.")

            faq_key_norm = texto_lower.replace("?", "").replace(".", "").replace("!", "").strip()
            matched_faq_key = None
            if faq_key_norm in FAQ_RESPOSTAS:
                matched_faq_key = faq_key_norm
            else:
                for key in FAQ_RESPOSTAS:
                    if key in faq_key_norm:
                        matched_faq_key = key
                        break

            if matched_faq_key:
                 logging.info(f"NLP: Respondendo com FAQ para chave: {matched_faq_key}")
                 resposta_final = FAQ_RESPOSTAS[matched_faq_key]
                 novo_estado = "SUPORTE_FAQ"
                 intent = f"faq_{matched_faq_key.replace(' ', '_')}"
            else:
                 if not OLLAMA_API_URL:
                     logging.error("NLP: ❌ Fallback para IA falhou - OLLAMA_API_URL não configurado.")
                     resposta_final = MENSAGEM_ERRO_PADRAO
                     intent = "erro_config_ia"
                     novo_estado = "SUPORTE_FAQ"
                 else:
                     logging.info(f"NLP: Chamando Ollama para {telefone}...")
                     prompt = await construir_prompt_para_ia(telefone, texto_mensagem, estado_atual, meta_conversa)
                     resposta_textual_ia, json_extraido_ia, tokens_ollama = await chamar_ollama(prompt, telefone)

                     if resposta_textual_ia is None or "⚠️" in resposta_textual_ia:
                         resposta_final = resposta_textual_ia or MENSAGEM_ERRO_IA
                         intent = "erro_ia_fallback"
                         novo_estado = "SUPORTE_FAQ"
                     else:
                         resposta_final = resposta_textual_ia

                         if json_extraido_ia and isinstance(json_extraido_ia, dict):
                             logging.info(f"NLP: JSON extraído da IA: {json_extraido_ia}")
                             intent = json_extraido_ia.get("intent", "ia_generica")
                             entidades_ia = json_extraido_ia.get("entidades", {})
                             if isinstance(entidades_ia, dict):
                                  meta_conversa = atualizar_meta_conversa(meta_conversa, entidades_ia)
                                  entidades = entidades_ia
                             else:
                                  logging.warning(f"NLP: Entidades retornadas pela IA não são um dicionário: {entidades_ia}")

                             sentimento_ia = json_extraido_ia.get("sentimento_detectado")
                             if sentimento_ia and isinstance(sentimento_ia, str):
                                  sentimento = sentimento_ia
                                  meta_conversa["ultimo_sentimento_detectado"] = sentimento
                             else:
                                  logging.warning(f"NLP: Sentimento retornado pela IA inválido ou ausente: {sentimento_ia}. Usando sentimento analisado anteriormente: {sentimento}")
                         else:
                              logging.warning("NLP: ⚠️ IA não retornou JSON reconhecível no final da resposta.")
                              intent = "ia_generica_sem_json"

                         novo_estado = "SUPORTE_FAQ"

    except Exception as e:
        logging.exception(f"NLP: ❌ ERRO INESPERADO durante processamento da mensagem para {telefone}:")
        resposta_final = MENSAGEM_ERRO_PADRAO
        intent = "erro_processamento_geral"
        novo_estado = estado_atual

    # --- 5. Atualizar Contexto e Salvar Histórico ---
    meta_conversa_final = meta_conversa if isinstance(meta_conversa, dict) else {}
    contexto_para_salvar = {
        "estado": novo_estado,
        "ultima_resposta_bot": resposta_final,
        "meta_conversa": meta_conversa_final
    }

    salvar_contexto(telefone, contexto_para_salvar)
    salvar_resposta_ia(telefone, canal, texto_mensagem, resposta_final, intent, entidades, risco_detectado, sentimento)

    logging.info(f"NLP: ✅ Processamento concluído para {telefone}. Novo estado: {novo_estado}. Resposta: '{resposta_final[:50]}...'")
    return {"resposta": resposta_final, "estado": novo_estado}

