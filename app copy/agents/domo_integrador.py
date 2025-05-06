"""
Encapsula chamada à API WhatsApp para manter padrão único.
Outros agentes devem usar enviar_mensagem de utils.mensageria diretamente,
mas este agente permite ações administrativas (ex: envio em lote).
"""
from app.agents.agente_base import AgenteBase
from app.utils.mensageria import enviar_mensagem

class DomoIntegrador(AgenteBase):
    async def _gerar_resposta(self, telefone: str, mensagem_original: str) -> str | None:
        # Apenas ecoa mensagem administrativa (não usado no fluxo paciente)
        await enviar_mensagem(telefone, "Operação concluída.")
        return None
