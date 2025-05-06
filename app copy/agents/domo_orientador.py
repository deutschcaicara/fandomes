"""
Responde dúvidas genéricas com base nas intents FAQ_*.
"""
from app.agents.agente_base import AgenteBase

class DomoOrientador(AgenteBase):
    async def _gerar_resposta(self, telefone: str, mensagem_original: str) -> str | None:
        # Mapeamento simples: intenção já contém a chave FAQ_...
        return await self._carregar_mensagem_intent(self.intent)
