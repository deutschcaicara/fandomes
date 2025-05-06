# ===========================================================
# Orquestrador principal – versão completa com:
# • fuzzy trigger antes da IA
# • guard‑rail triagem
# • scoring lead
# • fallback generativo
# ===========================================================
from __future__ import annotations
import logging
from importlib import import_module
from typing import Dict, Type

from app.core.ia_analisador import detectar_intencao, analisar_sentimento
from app.core.intents import buscar_por_trigger
from app.core.scoring import score_lead
from app.utils.contexto import obter_contexto, salvar_contexto
from app.core.rastreamento import registrar_evento
from app.agents.agente_base import AgenteBase

logger = logging.getLogger("famdomes.mcp")

_INTENT_MAP: Dict[str, str] = {
    # clínicas
    "ACOLHIMENTO": "app.agents.domo_escuta.DomoEscuta",
    "PRESENCA_VIVA": "app.agents.domo_presenca.DomoPresenca",
    "TRIAGEM_INICIAL": "app.agents.domo_triagem.DomoTriagem",
    "ESCALONAR_HUMANO": "app.agents.domo_escalonador.DomoEscalonador",
    # comerciais
    "MICRO_COMPROMISSO": "app.agents.domo_comercial.DomoComercial",
    "PITCH_PLANO3": "app.agents.domo_comercial.DomoComercial",
    "PITCH_PLANO1": "app.agents.domo_comercial.DomoComercial",
    "CALL_TO_ACTION": "app.agents.domo_comercial.DomoComercial",
    "RECUSA_PRECO": "app.agents.domo_comercial.DomoComercial",
    # FAQ
    "FAQ_COMO_FUNCIONA": "app.agents.domo_orientador.DomoOrientador",
    "FAQ_PAGAMENTO": "app.agents.domo_orientador.DomoOrientador",
    "FAQ_CANCELAMENTO": "app.agents.domo_orientador.DomoOrientador",
    "FAQ_ROBO": "app.agents.domo_orientador.DomoOrientador",
    # fallback
    "DEFAULT": "app.agents.domo_generativo.DomoGenerativo",
}

class MCPOrquestrador:
    _inst: "MCPOrquestrador | None" = None
    def __new__(cls):
        if not cls._inst:
            cls._inst = super().__new__(cls)
        return cls._inst

    # ------------------------------------------------------
    async def processar_mensagem(self, tel: str, texto: str) -> None:
        logger.info("MCP ▶ tel=%s texto=%s", tel, texto)
        ctx = obter_contexto(tel)
        estado = ctx.get("estado", "INICIAL")

        # 1. fuzzy trigger
        intent, _ = buscar_por_trigger(texto.lower())

        # 2. IA se necessário
        if not intent:
            intent = await detectar_intencao(texto)

        # 3. guard‑rails
        if intent == "ACOLHIMENTO":
            intent = "MICRO_COMPROMISSO"
        if intent == "TRIAGEM_INICIAL" and ctx.get("estado") != "PAGAMENTO_OK":
            intent = "FAQ_COMO_FUNCIONA"

        # 4. sentimento + score
        sentimento = await analisar_sentimento(texto)
        s_lead = score_lead(texto) if estado in {"INICIAL", "MICRO"} else ctx.get("meta_conversa", {}).get("score_lead", 0)
        salvar_contexto(tel, texto=texto, meta_conversa={"score_lead": s_lead})
        registrar_evento(tel, etapa="análise", dados={"intent": intent, "score": s_lead})

        # 5. agente
        agente_cls = self._resolver_agente(intent)
        agente: AgenteBase = agente_cls(intent=intent, sentimento=sentimento)

        try:
            await agente.executar(tel, texto)
            registrar_evento(tel, etapa="execução", dados={"agente": agente.nome})
        except Exception as exc:
            logger.exception("MCP erro %s", exc)
            registrar_evento(tel, etapa="erro", dados={"err": str(exc)})

    # ------------------------------------------------------
    def _resolver_agente(self, intent: str) -> Type[AgenteBase]:
        caminho = _INTENT_MAP.get(intent, _INTENT_MAP["DEFAULT"])
        mod_path, _, cls_name = caminho.rpartition(".")
        return getattr(import_module(mod_path), cls_name)
