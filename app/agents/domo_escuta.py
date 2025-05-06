# ===========================================================
# Arquivo: agents/domo_escuta.py
# Agente responsável pelo acolhimento inicial.
# - Usa o sentimento da primeira mensagem para personalizar a saudação.
# - Carrega a resposta padrão de ACOLHIMENTO como fallback.
# ===========================================================
from app.agents.agente_base import AgenteBase
# Usaremos a função de refrasear da classe base ou uma chamada direta à IA
from app.core.ia_direct import gerar_resposta_ia # Ou app.utils.ollama
import logging

logger = logging.getLogger("famdomes.domo_escuta")

class DomoEscuta(AgenteBase):
    """
    Agente para a primeira interação, focando em acolhimento empático.
    Adapta a saudação com base no sentimento detectado na mensagem inicial do usuário.
    """
    async def _gerar_resposta(self, telefone: str, mensagem_original: str) -> str | None:
        """
        Gera a mensagem de acolhimento inicial, personalizada pelo sentimento.
        """
        # Carrega a intent 'ACOLHIMENTO' para obter a resposta padrão
        intent_acolhimento = await self._carregar_mensagem_intent("ACOLHIMENTO")
        resposta_padrao = intent_acolhimento.get("resposta") if intent_acolhimento else "Olá! Sou o Domo. Como posso ajudar?"
        resposta_final = resposta_padrao # Começa com o padrão

        # Tenta personalizar com base no sentimento recebido no construtor (self.sentimento)
        if self.sentimento:
            try:
                sentimento_predominante = max(self.sentimento, key=self.sentimento.get)
                score_predominante = self.sentimento.get(sentimento_predominante, 0)

                prompt_personalizado = None
                # Define o prompt com base no sentimento predominante (se score for significativo)
                if sentimento_predominante == 'negativo' and score_predominante > 0.6: # Limiar ajustável
                    prompt_personalizado = f"""
                    O usuário iniciou a conversa com uma mensagem de sentimento predominantemente NEGATIVO.
                    Gere uma saudação CURTA e ACOLHEDORA (máx 1-2 frases, ~150 caracteres) que:
                    1. Reconheça SUTILMENTE a dificuldade (ex: "Sinto muito que esteja passando por isso", "Sei que às vezes é difícil buscar ajuda").
                    2. Apresente-se como Domo.
                    3. Pergunte como pode ajudar HOJE.
                    EVITE repetir a mensagem original do usuário.
                    Saudação Empática Negativa:
                    """
                elif sentimento_predominante == 'positivo' and score_predominante > 0.6:
                     prompt_personalizado = f"""
                     O usuário iniciou a conversa com uma mensagem de sentimento predominantemente POSITIVO.
                     Gere uma saudação CURTA e POSITIVA (máx 1-2 frases, ~150 caracteres) que:
                     1. Cumprimente de forma leve (ex: "Olá!", "Que bom te ver por aqui!").
                     2. Apresente-se como Domo.
                     3. Pergunte como pode ajudar.
                     Saudação Positiva:
                     """
                # Se for neutro ou score baixo, usa a resposta padrão (resposta_final já é a padrão)

                # Se um prompt foi definido, chama a IA
                if prompt_personalizado:
                    logger.debug(f"DomoEscuta: Gerando resposta personalizada para sentimento '{sentimento_predominante}' para {telefone}")
                    # Adapte a chamada conforme sua função de IA (ia_direct ou ollama)
                    resposta_ia = await gerar_resposta_ia({"prompt_context": prompt_personalizado})
                    # Verifica se a resposta da IA é válida antes de usar
                    if resposta_ia and len(resposta_ia) > 10:
                        resposta_final = resposta_ia.strip()
                        logger.info(f"DomoEscuta: Resposta personalizada gerada para {telefone}.")
                    else:
                        logger.warning(f"DomoEscuta: IA não retornou resposta válida para personalização. Usando padrão para {telefone}.")
                        # Mantém a resposta padrão
            except Exception as e:
                logger.warning(f"DomoEscuta: Falha ao gerar resposta personalizada: {e}. Usando padrão para {telefone}.")
                # Mantém a resposta padrão em caso de erro

        # Define o estado seguinte no contexto para o Orquestrador saber
        # É MELHOR o Orquestrador definir o estado após a execução do agente.
        # Mas se o agente precisar forçar um estado, pode fazer aqui:
        # salvar_contexto(telefone=telefone, novo_estado="ACOLHIMENTO_ENVIADO")
        # logger.info(f"DomoEscuta: Estado definido para ACOLHIMENTO_ENVIADO para {telefone}")

        return resposta_final

