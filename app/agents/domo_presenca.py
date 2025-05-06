"""
Mantém presença viva: envia mensagens breves de acompanhamento sem exigir resposta.
"""
from app.agents.agente_base import AgenteBase

class DomoPresenca(AgenteBase):
    async def _gerar_resposta(self, telefone: str, mensagem_original: str) -> str | None:
        return await self._carregar_mensagem_intent("PRESENCA_VIVA")
