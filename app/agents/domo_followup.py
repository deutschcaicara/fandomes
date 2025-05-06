# ===========================================================
# Arquivo: agents/domo_followup.py
# Agente responsável por enviar mensagens de follow-up.
# - Ativado pelo Scheduler ou outras lógicas.
# - Carrega a mensagem apropriada com base na intent recebida.
# ===========================================================
import logging
from app.agents.agente_base import AgenteBase

logger = logging.getLogger("famdomes.domo_followup")

# Intents esperadas para este agente (devem existir nos JSONs)
INTENTS_FOLLOWUP_SUPORTADAS = [
    "FOLLOW_UP_QUALIFICACAO", # Enviado quando a qualificação para
    "FOLLOW_UP_24H",          # Enviado 24h após link de pagamento (padrão)
    "FOLLOW_UP_PAGAMENTO_BENEFICIO" # Alternativa focada em benefício
    # Adicionar outras intents de follow-up aqui, se necessário
]

class DomoFollowUp(AgenteBase):
    """
    Envia mensagens de follow-up pré-definidas com base na intent.
    Normalmente ativado por tarefas agendadas (scheduler).
    """

    async def _gerar_resposta(self, telefone: str, mensagem_original: str) -> str | None:
        """
        Carrega e retorna a mensagem de follow-up correspondente à intent.
        """
        intent_followup = self.intent # A intent que ativou este agente

        # Verifica se a intent é suportada por este agente
        if intent_followup not in INTENTS_FOLLOWUP_SUPORTADAS:
            logger.error(f"DomoFollowUp: Recebeu intent não suportada '{intent_followup}' para {telefone}. Não responderá.")
            return None

        logger.info(f"DomoFollowUp: Preparando mensagem de follow-up '{intent_followup}' para {telefone}.")

        # Carrega os dados da intent (incluindo a mensagem de resposta)
        intent_data = await self._carregar_mensagem_intent(intent_followup)

        if intent_data and intent_data.get("resposta"):
            resposta = intent_data.get("resposta")
            # Opcional: Tentar refrasear levemente com IA para não ser sempre igual
            # resposta_refraseada = await self._refrasear_com_ia(resposta, telefone, f"follow-up {intent_followup}")
            # return resposta_refraseada
            return resposta
        else:
            logger.error(f"DomoFollowUp: Não foi possível carregar a mensagem para a intent '{intent_followup}'. Verifique os arquivos JSON.")
            # Retorna None para não enviar nada se a mensagem não for encontrada
            return None

