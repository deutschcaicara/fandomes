"""
Avalia padrão emocional ao longo do tempo e decide escalonar ou ajustar trilha.
Por ora, apenas registra – sem resposta.
"""
from app.agents.agente_base import AgenteBase
from app.core.rastreamento import registrar_evento

class DomoMonitor(AgenteBase):
    async def _gerar_resposta(self, telefone: str, mensagem_original: str) -> str | None:
        registrar_evento(telefone, etapa="monitor", dados=self.sentimento)
        return None

