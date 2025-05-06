# ===========================================================
# Arquivo: agents/agente_base.py
# Classe‑base para todos os agentes DOMO
# – carrega intents de qualquer JSON em app/intents/
# – disponibiliza utilitário de resposta por intent
# ===========================================================
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Any, Optional

from app.core.intents import obter_intent


class AgenteBase:
    """
    Classe que todos os agentes devem herdar.
    Each agent implementa _gerar_resposta().
    """

    def __init__(self, intent: str, sentimento: Dict[str, Any] | None = None) -> None:
        self.intent = intent
        self.sentimento = sentimento or {}
        self.nome = self.__class__.__name__

    # ------------------------------------------------------
    async def executar(self, telefone: str, mensagem_original: str) -> None:
        """
        Método chamado pelo MCP. Gera texto e envia via mensageria.
        """
        from app.utils.mensageria import enviar_mensagem

        resposta = await self._gerar_resposta(telefone, mensagem_original)
        if resposta:
            await enviar_mensagem(telefone, resposta)
        else:
            # opcional: logar “não respondeu”
            import logging

            logging.info("ℹ️  %s optou por não responder (intent=%s)", self.nome, self.intent)

    # ------------------------------------------------------
    async def _gerar_resposta(self, telefone: str, mensagem_original: str) -> str | None:
        """
        Cada agente concreto sobrescreve este método.
        Deve devolver texto pronto para enviar ou None.
        """
        raise NotImplementedError

    # ------------------------------------------------------
    async def _carregar_mensagem_intent(self, intent_id: str) -> Optional[str]:
        """
        Busca resposta em qualquer arquivo intents/*.json
        """
        intent = obter_intent(intent_id)
        return intent.get("resposta") if intent else None
