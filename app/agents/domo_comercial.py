# ===========================================================
# Arquivo: agents/domo_comercial.py
# Agente responsável pelo fluxo de qualificação e venda.
# - Inicia com micro-compromisso.
# - Realiza perguntas de qualificação sequenciais.
# - Valida respostas anteriores com IA.
# - Apresenta planos com foco em VALOR antes do preço.
# - Gerencia o CTA e respostas de recusa.
# ===========================================================
from __future__ import annotations
import logging
from app.agents.agente_base import AgenteBase
from app.core.scoring import score_lead
from app.utils.contexto import salvar_contexto, obter_contexto
from app.core.ia_direct import gerar_resposta_ia # Ou app.utils.ollama

logger = logging.getLogger("famdomes.domo_comercial")

# --- Configuração do Fluxo de Qualificação ---
# Mover para um arquivo de configuração ou JSON seria ideal
PERGUNTAS_QUALIFICACAO = [
    {
        "id": 1,
        "chave_meta": "para_quem", # Chave para salvar a resposta na meta_conversa
        "texto": "Para direcionar melhor, a ajuda que você busca é para você mesmo(a) ou para outra pessoa (ex: filho, esposa, irmão)?"
    },
    {
        "id": 2,
        "chave_meta": "preferencia_atendimento",
        "texto": "Considerando a necessidade atual, você teria preferência por um atendimento online ou presencial?"
    },
    {
        "id": 3,
        "chave_meta": "possibilidade_investimento",
        "texto": "Pensando no cuidado contínuo, existe a possibilidade de um investimento mensal em um acompanhamento profissional?"
    }
]
TOTAL_PERGUNTAS = len(PERGUNTAS_QUALIFICACAO)

# Intents relevantes para este agente (carregados via _carregar_mensagem_intent)
INTENT_MICRO_COMPROMISSO = "MICRO_COMPROMISSO"
INTENT_PITCH_PLANO1 = "PITCH_PLANO1"
INTENT_PITCH_PLANO3 = "PITCH_PLANO3"
INTENT_DETALHES_PLANO = "COMERCIAL_DETALHES_PLANO"
INTENT_CTA = "CALL_TO_ACTION"
INTENT_RECUSA = "RECUSA_PRECO"
INTENT_DEFAULT_COMERCIAL = "FAQ_COMO_FUNCIONA" # Fallback se algo der errado no fluxo

# Palavras-chave para análise de resposta (simplificado)
RESPOSTAS_AFIRMATIVAS = ["sim", "quero", "pode", "manda", "link", "pagar", "começar", "aceito", "claro", "ok", "positivo", "tenho", "existe"]
RESPOSTAS_NEGATIVAS = ["não", "nao", "agora não", "sem chance", "impossível", "negativo", "nunca"]
RESPOSTAS_PEDIDO_DETALHES = ["detalhes", "mais", "como é", "explica", "quais", "opções"]

class DomoComercial(AgenteBase):
    """
    Gerencia o fluxo de qualificação de leads e apresentação dos planos comerciais.
    """

    async def _gerar_validacao_curta(self, telefone: str, mensagem_original: str) -> str:
        """Gera validação empática curta para a resposta anterior."""
        # Não valida a primeira resposta (após micro-compromisso)
        ctx = obter_contexto(telefone)
        etapa_quali = ctx.get("meta_conversa", {}).get("etapa_quali", 0)
        if etapa_quali <= 1: # Não valida antes da Q1 ou após Q1
             return ""

        if not self.sentimento or not mensagem_original:
             return "Ok. " # Fallback muito curto

        sentimento_desc = "neutro"
        if self.sentimento.get('negativo', 0) > 0.6: sentimento_desc = "negativo"
        elif self.sentimento.get('positivo', 0) > 0.6: sentimento_desc = "positivo"

        try:
            prompt = f"""
            O usuário respondeu a uma pergunta de qualificação. O sentimento detectado foi {sentimento_desc}.
            Gere uma ÚNICA PALAVRA de validação (ex: "Entendido.", "Compreendo.", "Perfeito.", "Certo.").
            Validação Curta:
            """
            validacao = await gerar_resposta_ia({"prompt_context": prompt})
            # Garante que a validação seja curta e termine com ponto e espaço
            validacao_limpa = "".join(c for c in validacao if c.isalnum() or c in ['.', ' ']).strip().split('.')[0]
            return f"{validacao_limpa}. " if validacao_limpa else "Ok. "
        except Exception as e:
            logger.warning(f"DomoComercial: Falha ao gerar validação curta: {e}")
            return "Ok. "

    async def _gerar_resposta_valor_preco(self, telefone: str, plano_intent_id: str) -> str:
        """Gera a explicação de valor antes do preço e CTA."""
        plano_info = await self._carregar_mensagem_intent(plano_intent_id)
        if not plano_info or "resposta" not in plano_info:
            logger.error(f"DomoComercial: Falha ao carregar dados da intent {plano_intent_id}")
            return "Temos ótimas opções de acompanhamento. Gostaria do link para começar?" # Fallback

        # A resposta no JSON contém a descrição e o preço. Precisamos que a IA foque no valor.
        descricao_preco_original = plano_info["resposta"]

        try:
            prompt = f"""
            O usuário se qualificou para o plano '{plano_intent_id}'. A descrição original é: "{descricao_preco_original}".
            Gere uma resposta CONCISA (máx 2-3 frases, ~250 caracteres) que:
            1. Comece com uma frase positiva de transição (ex: "Excelente!", "Ótima opção para você!").
            2. DESTAQUE O PRINCIPAL BENEFÍCIO ou TRANSFORMAÇÃO que este plano oferece (use a descrição original como inspiração, mas foque no resultado para o usuário).
            3. APENAS DEPOIS, mencione o investimento de forma clara (ex: "O investimento é de ..."). Use o valor da descrição original.
            4. FINALIZE perguntando DIRETAMENTE se o usuário deseja o link de pagamento para iniciar. (ex: "Deseja o link de pagamento para começar agora?")
            Resposta Focada em Valor e CTA:
            """
            resposta_valor = await gerar_resposta_ia({"prompt_context": prompt})
            if resposta_valor and len(resposta_valor) > 20:
                logger.info(f"DomoComercial: Resposta de valor/preço gerada para {telefone}.")
                return resposta_valor.strip()
            else: # Fallback se IA falhar
                logger.warning(f"DomoComercial: IA falhou ao gerar valor/preço para {plano_intent_id}. Usando fallback.")
                return f"{descricao_preco_original} Deseja o link de pagamento para começar?"
        except Exception as e:
            logger.exception(f"DomoComercial: Erro ao gerar resposta de valor/preço: {e}")
            return f"{descricao_preco_original} Deseja o link de pagamento para começar?" # Fallback

    async def _gerar_resposta(self, telefone: str, msg: str) -> str | None:
        """
        Define a lógica de resposta do agente comercial com base na intent e contexto.
        """
        ctx = obter_contexto(telefone)
        meta = ctx.get("meta_conversa", {})
        etapa_quali_atual = meta.get("etapa_quali", 0) # Etapa *antes* desta interação
        intent_atual = self.intent # Intent que ativou este agente

        resposta = None
        novo_estado_sugerido = None # O agente pode sugerir um novo estado para o Orquestrador

        # --- Fluxo de Qualificação ---
        # Verifica se estamos iniciando ou continuando a qualificação
        if intent_atual == INTENT_MICRO_COMPROMISSO or (etapa_quali_atual > 0 and etapa_quali_atual <= TOTAL_PERGUNTAS):

            # Salva a resposta da pergunta anterior (se não for a primeira)
            if etapa_quali_atual > 0:
                 pergunta_anterior = PERGUNTAS_QUALIFICACAO[etapa_quali_atual - 1]
                 chave_meta = pergunta_anterior["chave_meta"]
                 meta[chave_meta] = msg # Salva a resposta do usuário
                 meta[f"sentimento_{chave_meta}"] = self.sentimento # Salva sentimento da resposta
                 logger.debug(f"DomoComercial: Resposta para '{chave_meta}' salva para {telefone}.")

            # Gera validação curta para a resposta anterior (exceto após micro-compromisso)
            validacao = await self._gerar_validacao_curta(telefone, msg)

            # Verifica se ainda há perguntas a fazer
            if etapa_quali_atual < TOTAL_PERGUNTAS:
                # Prepara a próxima pergunta
                proxima_pergunta_info = PERGUNTAS_QUALIFICACAO[etapa_quali_atual]
                resposta = validacao + proxima_pergunta_info["texto"]
                # Atualiza a etapa no meta_conversa para a próxima interação
                meta["etapa_quali"] = etapa_quali_atual + 1
                novo_estado_sugerido = INTENT_MICRO_COMPROMISSO # Mantém no fluxo de qualificação
                salvar_contexto(telefone=telefone, meta_conversa=meta, estado=novo_estado_sugerido)
                logger.info(f"DomoComercial: Enviando pergunta de qualificação {etapa_quali_atual + 1} para {telefone}.")
            else:
                # Finalizou a qualificação
                logger.info(f"DomoComercial: Qualificação finalizada para {telefone}.")
                # Calcular score final com base nas respostas (exemplo simples)
                # (A função score_lead original pode precisar ser adaptada ou usar as respostas salvas)
                score_final = meta.get("score_lead", 0) # Usa score já calculado ou recalcula
                try:
                    # Exemplo: recalcular baseado na resposta sobre investimento
                    resp_invest = meta.get("possibilidade_investimento", "").lower()
                    if any(affirmative in resp_invest for affirmative in RESPOSTAS_AFIRMATIVAS):
                        score_final += 2
                    elif any(negative in resp_invest for negative in RESPOSTAS_NEGATIVAS):
                        score_final -= 2
                    score_final = max(0, min(6, score_final)) # Garante limite 0-6
                    meta["score_lead"] = score_final
                except Exception as e:
                    logger.error(f"DomoComercial: Erro ao recalcular score final para {telefone}: {e}")

                meta.pop("etapa_quali", None) # Limpa a etapa de qualificação

                # Define o próximo passo (Pitch) baseado no score
                proximo_pitch_intent = INTENT_PITCH_PLANO3 if score_final >= 4 else INTENT_PITCH_PLANO1
                novo_estado_sugerido = proximo_pitch_intent
                salvar_contexto(telefone=telefone, meta_conversa=meta, estado=novo_estado_sugerido)

                # Gera a resposta de valor/preço para o plano apropriado
                resposta = await self._gerar_resposta_valor_preco(telefone, proximo_pitch_intent)

        # --- Fluxo de Pitch (Resposta à apresentação do plano) ---
        elif intent_atual in [INTENT_PITCH_PLANO1, INTENT_PITCH_PLANO3]:
            msg_lower = msg.lower()
            # Resposta positiva ao Pitch -> Vai para CTA
            if any(affirmative in msg_lower for affirmative in RESPOSTAS_AFIRMATIVAS):
                logger.info(f"DomoComercial: Usuário {telefone} aceitou o pitch. Indo para CTA.")
                novo_estado_sugerido = INTENT_CTA
                intent_cta_info = await self._carregar_mensagem_intent(INTENT_CTA)
                resposta = intent_cta_info.get("resposta") if intent_cta_info else "Ótimo! Aqui está o link para pagamento: [link]"
                # Chamar a função para gerar o link de pagamento real (routes/ia.py)
                # Esta parte precisa ser coordenada com o Orquestrador ou uma chamada direta
                # Idealmente, o Orquestrador detectaria a confirmação e chamaria a rota /ia-comando
                # Por simplicidade aqui, apenas enviamos a mensagem do JSON
                # TODO: Integrar com a geração real do link de pagamento Stripe via routes/ia.py
                salvar_contexto(telefone=telefone, estado=novo_estado_sugerido) # Salva estado CTA

            # Pedido de mais detalhes -> Vai para Detalhes
            elif any(detail_request in msg_lower for detail_request in RESPOSTAS_PEDIDO_DETALHES):
                logger.info(f"DomoComercial: Usuário {telefone} pediu mais detalhes. Indo para Detalhes.")
                novo_estado_sugerido = INTENT_DETALHES_PLANO
                intent_detalhes_info = await self._carregar_mensagem_intent(INTENT_DETALHES_PLANO)
                resposta = intent_detalhes_info.get("resposta") if intent_detalhes_info else "Nossos planos incluem X, Y, Z. Quer agendar?"
                salvar_contexto(telefone=telefone, estado=novo_estado_sugerido)

            # Resposta negativa ou incerta -> Vai para Recusa
            else:
                logger.info(f"DomoComercial: Usuário {telefone} recusou ou respondeu incertamente ao pitch. Indo para Recusa.")
                novo_estado_sugerido = INTENT_RECUSA
                intent_recusa_info = await self._carregar_mensagem_intent(INTENT_RECUSA)
                resposta = intent_recusa_info.get("resposta") if intent_recusa_info else "Entendo. Posso ajudar com mais alguma informação?"
                salvar_contexto(telefone=telefone, estado=novo_estado_sugerido)

        # --- Fluxo de Detalhes (Resposta após receber mais detalhes) ---
        elif intent_atual == INTENT_DETALHES_PLANO:
             msg_lower = msg.lower()
             # Resposta positiva aos Detalhes -> Vai para CTA
             if any(affirmative in msg_lower for affirmative in RESPOSTAS_AFIRMATIVAS):
                 logger.info(f"DomoComercial: Usuário {telefone} aceitou após detalhes. Indo para CTA.")
                 novo_estado_sugerido = INTENT_CTA
                 intent_cta_info = await self._carregar_mensagem_intent(INTENT_CTA)
                 resposta = intent_cta_info.get("resposta") if intent_cta_info else "Ótimo! Aqui está o link para pagamento: [link]"
                 # TODO: Integrar com geração real do link Stripe
                 salvar_contexto(telefone=telefone, estado=novo_estado_sugerido)
             # Resposta negativa ou incerta -> Vai para Recusa
             else:
                 logger.info(f"DomoComercial: Usuário {telefone} recusou ou incerto após detalhes. Indo para Recusa.")
                 novo_estado_sugerido = INTENT_RECUSA
                 intent_recusa_info = await self._carregar_mensagem_intent(INTENT_RECUSA)
                 resposta = intent_recusa_info.get("resposta") if intent_recusa_info else "Entendo. Posso ajudar com mais alguma informação?"
                 salvar_contexto(telefone=telefone, estado=novo_estado_sugerido)

        # --- Fluxo de CTA (Resposta após receber link de pagamento) ---
        elif intent_atual == INTENT_CTA:
            logger.info(f"DomoComercial: Usuário {telefone} interagiu após receber link de pagamento.")
            # A confirmação de pagamento deve vir pelo webhook do Stripe.
            # Qualquer mensagem aqui provavelmente é uma dúvida ou comentário.
            # Podemos usar a IA generativa para responder ou direcionar para FAQ/Humano.
            resposta = await self._refrasear_com_ia(
                "Recebi sua mensagem. Se tiver alguma dúvida sobre o pagamento ou o próximo passo, pode perguntar. Assim que o pagamento for confirmado, iniciaremos a triagem.",
                telefone,
                contexto_breve="usuario interagiu apos receber link de pagamento"
            )
            novo_estado_sugerido = "AGUARDANDO_PAGAMENTO" # Estado explícito
            salvar_contexto(telefone=telefone, estado=novo_estado_sugerido)

        # --- Fluxo de Recusa (Resposta à oferta de material gratuito) ---
        elif intent_atual == INTENT_RECUSA:
            msg_lower = msg.lower()
            if any(affirmative in msg_lower for affirmative in RESPOSTAS_AFIRMATIVAS):
                logger.info(f"DomoComercial: Usuário {telefone} aceitou material gratuito.")
                resposta = "Que ótimo! Em breve nossa equipe enviará o material para você por aqui. Algo mais em que posso ajudar hoje?"
                novo_estado_sugerido = "LEAD_MATERIAL_GRATUITO" # Estado final para este fluxo
                # Adicionar lógica para marcar o lead para envio do material, se necessário
                salvar_contexto(telefone=telefone, estado=novo_estado_sugerido)
            else:
                logger.info(f"DomoComercial: Usuário {telefone} recusou material gratuito.")
                resposta = "Tudo bem. Se mudar de ideia ou precisar de algo mais no futuro, é só chamar. Estou à disposição!"
                novo_estado_sugerido = "FINALIZADO_SEM_VENDA" # Estado final
                salvar_contexto(telefone=telefone, estado=novo_estado_sugerido)

        # --- Fallback ---
        if resposta is None:
            logger.warning(f"DomoComercial: Nenhuma lógica tratou a intent '{intent_atual}' ou estado para {telefone}. Verificando fallback.")
            # Tenta carregar uma resposta da própria intent (se houver, ex: FAQ dentro do fluxo)
            intent_info = await self._carregar_mensagem_intent(intent_atual)
            if intent_info and intent_info.get("resposta"):
                resposta = intent_info.get("resposta")
                novo_estado_sugerido = intent_atual # Mantém a intent como estado? Ou vai para FAQ?
                salvar_contexto(telefone=telefone, estado="SUPORTE_FAQ") # Manda para suporte geral
            else:
                # Se não há resposta na intent, usa um fallback mais genérico
                fallback_info = await self._carregar_mensagem_intent(INTENT_DEFAULT_COMERCIAL)
                resposta = fallback_info.get("resposta") if fallback_info else "Não entendi bem. Pode reformular ou me dizer o que gostaria de fazer?"
                novo_estado_sugerido = "SUPORTE_FAQ" # Estado de suporte geral
                salvar_contexto(telefone=telefone, estado=novo_estado_sugerido)


        # --- Anti-Loop ---
        # Compara a resposta gerada com a última enviada pelo bot
        ultimo_bot = ctx.get("ultimo_texto_bot", "")
        if resposta and resposta.strip() == ultimo_bot.strip():
            logger.warning(f"DomoComercial: ANTILOOP DETECTADO para {telefone}! Intent: {intent_atual}. Resposta repetida: '{resposta[:50]}...'")
            # Força uma resposta diferente, talvez usando a IA generativa ou uma mensagem padrão de erro de loop
            resposta_antiloop_info = await self._carregar_mensagem_intent("FAQ_ROBO") # Exemplo: explica que é IA
            if resposta_antiloop_info:
                 resposta = resposta_antiloop_info.get("resposta") + " Às vezes me repito, desculpe! Pode tentar perguntar de outra forma?"
            else:
                 resposta = "Parece que estamos andando em círculos! 😊 Poderia tentar me dizer o que precisa de outra maneira?"
            # Considerar mudar o estado para SUPORTE_FAQ ou pedir ajuda humana
            novo_estado_sugerido = "SUPORTE_FAQ"
            salvar_contexto(telefone=telefone, estado=novo_estado_sugerido)

        return resposta

