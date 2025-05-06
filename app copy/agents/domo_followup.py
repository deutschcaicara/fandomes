from app.agents.agente_base import AgenteBase

class DomoFollowUp(AgenteBase):
    async def _gerar_resposta(self, telefone: str, mensagem_original: str):
        return await self._carregar_mensagem_intent("FOLLOW_UP_24H")
