"""
Detecta risco e avisa equipe humana. Não responde ao paciente.
"""
import logging, asyncio
from app.agents.agente_base import AgenteBase
from app.utils.mensageria import enviar_mensagem

logger = logging.getLogger("famdomes.escalonador")

EQUIPE_SUPORTE = ["+5511999990000"]  # ajuste para números reais

class DomoEscalonador(AgenteBase):
    async def _gerar_resposta(self, telefone: str, mensagem_original: str) -> str | None:
        aviso = f"⚠️ Atenção: possível crise detectada do paciente {telefone}."
        await asyncio.gather(*(enviar_mensagem(dest, aviso) for dest in EQUIPE_SUPORTE))
        logger.info("Equipe humana notificada para %s", telefone)
        return None          # nada enviado ao paciente

