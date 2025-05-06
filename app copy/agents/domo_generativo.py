from app.agents.agente_base import AgenteBase
from app.core.ia_direct import gerar_resposta_ia

class DomoGenerativo(AgenteBase):
    async def _gerar_resposta(self, telefone, mensagem_original):
        return await gerar_resposta_ia({"tel": telefone, "msg": mensagem_original})
