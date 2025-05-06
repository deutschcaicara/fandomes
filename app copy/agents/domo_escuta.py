"""
Agente mínimo de acolhimento inicial.
Usa intents.json → 'ACOLHIMENTO' ou fallback genérico.
"""
from app.agents.agente_base import AgenteBase

class DomoEscuta(AgenteBase):
    async def _gerar_resposta(self, telefone: str, mensagem_original: str) -> str | None:
        return await self._carregar_mensagem_intent("ACOLHIMENTO")
