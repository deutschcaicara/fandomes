# ===========================================================
# Arquivo: core/mcp_orquestrador.py
# Orquestrador principal – versão aprimorada com:
# • Passagem de sentimento para agentes
# • Análise de sentimento mais consistente
# • Melhor tratamento de estado inicial e fallback
# • Chamada de agente com mensagem original
# • Tratamento de erro mais robusto
# • CORRIGIDO: Chamada para salvar_contexto com argumento 'estado' correto.
# ===========================================================
from __future__ import annotations
import logging
from importlib import import_module
from typing import Dict, Type, Any

# Funções core e utils
from app.core.ia_analisador import detectar_intencao, analisar_sentimento
from app.core.intents import buscar_por_trigger, obter_intent
from app.core.scoring import score_lead
from app.utils.contexto import obter_contexto, salvar_contexto
from app.core.rastreamento import registrar_evento
from app.utils.mensageria import enviar_mensagem # Para fallback de erro

# Classe base do agente
from app.agents.agente_base import AgenteBase

logger = logging.getLogger("famdomes.mcp")

# Mapeamento de Intents para Classes de Agentes (Manter atualizado)
_INTENT_MAP: Dict[str, str] = {
    # Clínicas / Acolhimento
    "ACOLHIMENTO": "app.agents.domo_escuta.DomoEscuta",
    "PRESENCA_VIVA": "app.agents.domo_presenca.DomoPresenca",
    "TRIAGEM_INICIAL": "app.agents.domo_triagem.DomoTriagem", # Disparado após pagamento
    "ESCALONAR_HUMANO": "app.agents.domo_escalonador.DomoEscalonador", # Ou intent específica de risco
    "RISCO_DETECTADO": "app.agents.domo_escalonador.DomoEscalonador", # Se usar intent de risco

    # Comerciais / Vendas
    "MICRO_COMPROMISSO": "app.agents.domo_comercial.DomoComercial",
    "PITCH_PLANO3": "app.agents.domo_comercial.DomoComercial",
    "PITCH_PLANO1": "app.agents.domo_comercial.DomoComercial",
    "CALL_TO_ACTION": "app.agents.domo_comercial.DomoComercial",
    "RECUSA_PRECO": "app.agents.domo_comercial.DomoComercial",
    "COMERCIAL_DETALHES_PLANO": "app.agents.domo_comercial.DomoComercial",

    # Follow-up (Disparado pelo Scheduler ou outras lógicas)
    "FOLLOW_UP_QUALIFICACAO": "app.agents.domo_followup.DomoFollowUp",
    "FOLLOW_UP_24H": "app.agents.domo_followup.DomoFollowUp", # Follow-up de pagamento

    # FAQ / Orientação
    "FAQ_COMO_FUNCIONA": "app.agents.domo_orientador.DomoOrientador",
    "FAQ_PAGAMENTO": "app.agents.domo_orientador.DomoOrientador",
    "FAQ_CANCELAMENTO": "app.agents.domo_orientador.DomoOrientador",
    "FAQ_ROBO": "app.agents.domo_orientador.DomoOrientador",
    # Adicionar outras intents FAQ mapeadas para DomoOrientador
    "INTENT_091": "app.agents.domo_orientador.DomoOrientador", # FAQ Internação
    "INTENT_097": "app.agents.domo_orientador.DomoOrientador", # FAQ Sigilo
    "INTENT_036": "app.agents.domo_orientador.DomoOrientador", # FAQ Internação Involuntária
    # ... mapear outras intents de FAQ ...

    # Default / Generativo / Fallback
    "DEFAULT": "app.agents.domo_generativo.DomoGenerativo",
    # Mapear intents não-FAQ que devem ir para o generativo
    "INTENT_001": "app.agents.domo_generativo.DomoGenerativo",
    "INTENT_006": "app.agents.domo_generativo.DomoGenerativo",
    "INTENT_271": "app.agents.domo_generativo.DomoGenerativo",
    "INTENT_273": "app.agents.domo_generativo.DomoGenerativo",
    "INTENT_276": "app.agents.domo_generativo.DomoGenerativo",
    "INTENT_278": "app.agents.domo_generativo.DomoGenerativo", # Não falar agora -> IA pode dar espaço
    "INTENT_280": "app.agents.domo_generativo.DomoGenerativo", # Desaparecer -> IA pode acolher
    "INTENT_281": "app.agents.domo_generativo.DomoGenerativo", # Recomeçar
    "INTENT_283": "app.agents.domo_generativo.DomoGenerativo", # Fugir
    "INTENT_285": "app.agents.domo_generativo.DomoGenerativo", # Agradecimento -> IA responde
    "INTENT_241": "app.agents.domo_generativo.DomoGenerativo", # Cuidado físico -> IA orienta
    "INTENT_246": "app.agents.domo_generativo.DomoGenerativo", # Desesperança -> IA acolhe
    "INTENT_249": "app.agents.domo_generativo.DomoGenerativo", # Travado -> IA valida
    "INTENT_251": "app.agents.domo_generativo.DomoGenerativo", # Parar cigarro -> IA apoia
    "INTENT_254": "app.agents.domo_generativo.DomoGenerativo", # Rotina saudável -> IA incentiva
    "INTENT_256": "app.agents.domo_generativo.DomoGenerativo", # Nada resta -> IA acolhe
    "INTENT_258": "app.agents.domo_generativo.DomoGenerativo", # Culpa/sujeira -> IA acolhe
    "INTENT_211": "app.agents.domo_generativo.DomoGenerativo", # Recaída -> IA acolhe
    "INTENT_216": "app.agents.domo_generativo.DomoGenerativo", # Autoestima baixa -> IA valida
    "INTENT_220": "app.agents.domo_generativo.DomoGenerativo", # Resolver sozinho -> IA valida/oferece ajuda
    "INTENT_222": "app.agents.domo_generativo.DomoGenerativo", # Vontade de usar -> IA acolhe/oferece ajuda
    "INTENT_224": "app.agents.domo_generativo.DomoGenerativo", # Planos futuros -> IA incentiva
    "INTENT_226": "app.agents.domo_generativo.DomoGenerativo", # Vício como companhia -> IA acolhe
    "INTENT_228": "app.agents.domo_generativo.DomoGenerativo", # Falha em terapia -> IA valida/oferece nova chance
    "INTENT_181": "app.agents.domo_generativo.DomoGenerativo", # Brigas -> IA acolhe/oferece escuta
    "INTENT_186": "app.agents.domo_generativo.DomoGenerativo", # Quero ajudar -> IA orienta
    "INTENT_189": "app.agents.domo_generativo.DomoGenerativo", # Você é esperto? -> IA responde
    "INTENT_151": "app.agents.domo_generativo.DomoGenerativo", # Trauma religioso -> IA acolhe
    "INTENT_153": "app.agents.domo_generativo.DomoGenerativo", # Você sente? -> IA responde
    "INTENT_155": "app.agents.domo_generativo.DomoGenerativo", # Descrença -> IA valida/oferece alternativa
    "INTENT_157": "app.agents.domo_generativo.DomoGenerativo", # Recaída frequente -> IA acolhe
    "INTENT_159": "app.agents.domo_generativo.DomoGenerativo", # Quero acertar -> IA incentiva
    "INTENT_161": "app.agents.domo_generativo.DomoGenerativo", # Insônia -> IA oferece técnica/escuta
    "INTENT_163": "app.agents.domo_generativo.DomoGenerativo", # Reza por mim -> IA responde com respeito
    "INTENT_165": "app.agents.domo_generativo.DomoGenerativo", # Me distrai -> IA oferece história
    "INTENT_121": "app.agents.domo_generativo.DomoGenerativo", # Ansiedade -> IA acolhe
    "INTENT_126": "app.agents.domo_generativo.DomoGenerativo", # Ajuda casal -> IA orienta
    "INTENT_129": "app.agents.domo_generativo.DomoGenerativo", # Agressividade -> IA acolhe
    "INTENT_131": "app.agents.domo_generativo.DomoGenerativo", # Ser melhor pai/mãe -> IA incentiva
    "INTENT_133": "app.agents.domo_generativo.DomoGenerativo", # Solidão -> IA acolhe
    "INTENT_135": "app.agents.domo_generativo.DomoGenerativo", # Voluntariado -> IA encaminha
    "INTENT_137": "app.agents.domo_generativo.DomoGenerativo", # PCD -> IA acolhe/adapta
    "INTENT_093": "app.agents.domo_generativo.DomoGenerativo", # Culpa -> IA acolhe
    "INTENT_095": "app.agents.domo_generativo.DomoGenerativo", # Ódio -> IA acolhe/oferece espaço seguro
    "INTENT_099": "app.agents.domo_generativo.DomoGenerativo", # Abandono familiar -> IA acolhe
    "INTENT_106": "app.agents.domo_generativo.DomoGenerativo", # Luto -> IA acolhe
    "INTENT_061": "app.agents.domo_generativo.DomoGenerativo", # Espiritualidade -> IA acolhe/integra
    "INTENT_063": "app.agents.domo_generativo.DomoGenerativo", # Afastado/ improdutivo -> IA valida/oferece ajuda
    "INTENT_065": "app.agents.domo_generativo.DomoGenerativo", # Grupos -> IA informa/convida
    "INTENT_073": "app.agents.domo_generativo.DomoGenerativo", # Outra cidade -> IA informa opções
    "INTENT_075": "app.agents.domo_generativo.DomoGenerativo", # Sem dinheiro -> IA acolhe/oferece alternativas
    # Intents de risco devem ir para DomoEscalonador
    "INTENT_031": "app.agents.domo_escalonador.DomoEscalonador", # Risco de suicídio
}

class MCPOrquestrador:
    _inst: "MCPOrquestrador | None" = None
    def __new__(cls):
        if not cls._inst:
            cls._inst = super().__new__(cls)
        return cls._inst

    # ------------------------------------------------------
    async def processar_mensagem(self, tel: str, texto: str) -> None:
        """
        Processa uma mensagem recebida, determina a intenção,
        analisa o sentimento, seleciona e executa o agente apropriado.
        """
        logger.info(f"MCP ▶ Iniciando processamento para tel={tel}, texto='{texto[:50]}...'")
        ctx = obter_contexto(tel)
        # Garante que ctx seja um dicionário antes de prosseguir
        if not isinstance(ctx, dict):
             logger.error(f"MCP: Falha ao obter contexto válido para {tel}. Abortando processamento.")
             # Tentar enviar mensagem de erro genérica
             await enviar_mensagem(tel, "Desculpe, ocorreu um erro ao carregar sua conversa. Tente novamente.")
             return

        estado_anterior = ctx.get("estado", "INICIAL")
        meta_conversa = ctx.get("meta_conversa", {})
        # Garante que meta_conversa seja um dicionário
        if not isinstance(meta_conversa, dict):
            logger.warning(f"MCP: meta_conversa para {tel} não era um dicionário. Resetando para {{}}.")
            meta_conversa = {}


        # --- 1. Detecção de Risco (Executada primeiro, se aplicável) ---
        # (A lógica de risco pode estar aqui ou integrada na detecção de intenção)
        # Exemplo simplificado:
        # if "quero morrer" in texto.lower() or "me matar" in texto.lower(): # Usar app.utils.risco para análise robusta
        #     intent = "INTENT_031" # Força intent de risco
        #     logger.warning(f"MCP: Risco potencial detectado para {tel}. Intent definida como {intent}.")
        #     sentimento_atual = {"negativo": 1.0, "positivo": 0.0, "neutro": 0.0}
        #     meta_conversa["ultimo_sentimento_detectado"] = sentimento_atual
        #     await self._executar_agente(tel, texto, intent, sentimento_atual, meta_conversa, estado_anterior)
        #     return

        # --- 2. Análise de Sentimento da Mensagem Atual ---
        try:
            sentimento_atual = await analisar_sentimento(texto)
            # Atualiza o sentimento na meta_conversa ANTES de salvar o contexto intermediário
            meta_conversa["ultimo_sentimento_detectado"] = sentimento_atual
            logger.info(f"MCP: Sentimento detectado para {tel}: {sentimento_atual}")
        except Exception as e:
            logger.error(f"MCP: Erro ao analisar sentimento para {tel}: {e}. Usando neutro.")
            sentimento_atual = {"positivo": 0.33, "negativo": 0.33, "neutro": 0.34}
            meta_conversa["ultimo_sentimento_detectado"] = sentimento_atual

        # --- 3. Detecção de Intenção ---
        intent = "DEFAULT" # Começa com default
        try:
            intent_trigger, score_trigger = buscar_por_trigger(texto.lower())
            if intent_trigger:
                logger.info(f"MCP: Intent por trigger '{intent_trigger}' (score: {score_trigger:.2f}) para {tel}")
                intent = intent_trigger
            else:
                logger.info(f"MCP: Nenhum trigger encontrado. Usando IA para detectar intenção para {tel}.")
                intent_ia = await detectar_intencao(texto)
                if intent_ia in _INTENT_MAP or obter_intent(intent_ia): # Verifica mapeamento ou existência no JSON
                     intent = intent_ia
                     logger.info(f"MCP: Intent por IA '{intent}' para {tel}")
                else:
                     logger.warning(f"MCP: Intent da IA '{intent_ia}' não mapeada/encontrada. Usando DEFAULT para {tel}.")
                     intent = "DEFAULT"
        except Exception as e:
            logger.error(f"MCP: Erro ao detectar intenção para {tel}: {e}. Usando DEFAULT.")
            intent = "DEFAULT"

        # --- 4. Guard-rails e Lógica de Fluxo (Ajustes) ---
        # Se acabou de receber acolhimento, a próxima intent provavelmente inicia a qualificação
        if estado_anterior == "ACOLHIMENTO_ENVIADO" and intent != "ESCALONAR_HUMANO": # Exemplo de estado pós-acolhimento
             intent = "MICRO_COMPROMISSO"
             logger.info(f"MCP: Estado anterior era ACOLHIMENTO_ENVIADO. Forçando intent para {intent} para {tel}.")

        # Não permitir triagem antes do pagamento
        if intent == "TRIAGEM_INICIAL" and estado_anterior != "PAGAMENTO_OK":
            logger.warning(f"MCP: Tentativa de acessar TRIAGEM_INICIAL no estado {estado_anterior} para {tel}. Redirecionando.")
            intent = "FAQ_COMO_FUNCIONA" # Ou outra intent informativa

        # --- 5. Scoring de Lead (se aplicável) ---
        score_atual = meta_conversa.get("score_lead", 0)
        # Recalcula score em estados iniciais ou de qualificação
        if estado_anterior in ["INICIAL", "ACOLHIMENTO_ENVIADO", "MICRO_COMPROMISSO"]:
            try:
                score_atual = score_lead(texto) # Usa texto atual para score inicial
                meta_conversa["score_lead"] = score_atual
                logger.info(f"MCP: Score de lead calculado/atualizado para {tel}: {score_atual}")
            except Exception as e:
                logger.error(f"MCP: Erro ao calcular score para {tel}: {e}")

        # --- 6. Salvar Contexto Intermediário (Importante!) ---
        # Salva o estado ANTES da execução do agente, incluindo a intent detectada e meta atualizada
        sucesso_save_interm = salvar_contexto(
            telefone=tel,
            texto_usuario=texto,
            # CORREÇÃO: Usar o argumento 'estado' para salvar o estado ANTERIOR aqui
            estado=estado_anterior,
            meta_conversa=meta_conversa, # Inclui sentimento e score atualizados
            intent_detectada=intent, # Salva a intent que será usada pelo agente
            incrementar_interacoes=True # Incrementa aqui, antes do agente
        )
        if not sucesso_save_interm:
             logger.error(f"MCP: Falha ao salvar contexto intermediário para {tel}. Risco de inconsistência.")
             # Considerar abortar ou logar criticamente
        else:
            registrar_evento(tel, etapa="analise_concluida", dados={"intent": intent, "score": score_atual, "sentimento": sentimento_atual, "estado_anterior": estado_anterior})

        # --- 7. Executar Agente ---
        # Passa a intent detectada e o sentimento atualizado para o agente
        await self._executar_agente(tel, texto, intent, sentimento_atual, meta_conversa, estado_anterior)

    # ------------------------------------------------------
    def _resolver_agente(self, intent: str) -> Type[AgenteBase] | None:
        """Resolve a classe do agente com base na intent."""
        caminho_agente = _INTENT_MAP.get(intent)
        if not caminho_agente:
            intent_info = obter_intent(intent)
            if intent_info:
                 # Se a intent existe no JSON mas não no MAP, decidir o que fazer
                 # Ex: Se for FAQ -> Orientador, se for outra -> Generativo
                 if intent.startswith("FAQ_"):
                     caminho_agente = "app.agents.domo_orientador.DomoOrientador"
                     logger.info(f"MCP: Intent {intent} não mapeada explicitamente, mas identificada como FAQ. Usando DomoOrientador.")
                 else: # Outras intents não mapeadas explicitamente vão para o generativo
                      caminho_agente = "app.agents.domo_generativo.DomoGenerativo"
                      logger.info(f"MCP: Intent {intent} não mapeada explicitamente. Usando DomoGenerativo.")
            else:
                 logger.warning(f"MCP: Intent '{intent}' não encontrada no mapeamento nem nos arquivos JSON. Usando DEFAULT.")
                 caminho_agente = _INTENT_MAP.get("DEFAULT", "app.agents.domo_generativo.DomoGenerativo")

        try:
            mod_path, _, cls_name = caminho_agente.rpartition(".")
            modulo = import_module(mod_path)
            agente_cls = getattr(modulo, cls_name)
            if not issubclass(agente_cls, AgenteBase):
                 logger.error(f"MCP: Classe {caminho_agente} não herda de AgenteBase.")
                 return None # Retorna None para indicar falha na resolução
            return agente_cls
        except (ImportError, AttributeError, Exception) as e:
            logger.exception(f"MCP: Erro ao resolver agente para intent '{intent}' (caminho: {caminho_agente}): {e}")
            # Tenta resolver para o DEFAULT em caso de erro
            try:
                caminho_default = _INTENT_MAP.get("DEFAULT", "app.agents.domo_generativo.DomoGenerativo")
                mod_path, _, cls_name = caminho_default.rpartition(".")
                return getattr(import_module(mod_path), cls_name)
            except Exception:
                 logger.critical("MCP: Falha CRÍTICA ao resolver até mesmo o agente DEFAULT.")
                 return None

    # ------------------------------------------------------
    async def _executar_agente(self, tel: str, texto_usuario: str, intent: str, sentimento: dict, meta_conversa: dict, estado_anterior: str):
        """Instancia e executa o agente selecionado."""
        agente_cls = self._resolver_agente(intent)

        if not agente_cls:
            logger.error(f"MCP: Não foi possível resolver um agente para a intent '{intent}'. Nenhuma resposta será enviada.")
            registrar_evento(tel, etapa="erro_resolucao_agente", dados={"intent": intent})
            await enviar_mensagem(tel, "Desculpe, tive um problema interno para processar sua solicitação.")
            return

        agente_nome = agente_cls.__name__
        logger.info(f"MCP: Selecionado Agente '{agente_nome}' para intent '{intent}' (Telefone: {tel})")

        agente: AgenteBase = agente_cls(intent=intent, sentimento=sentimento)

        try:
            # Executa o agente
            await agente.executar(tel, texto_usuario)
            logger.info(f"MCP: Agente '{agente_nome}' executado com sucesso para {tel}.")
            registrar_evento(tel, etapa="execucao_agente_sucesso", dados={"agente": agente_nome, "intent": intent})

            # --- Atualização de Estado Pós-Agente ---
            # O agente pode ter chamado salvar_contexto e alterado o estado ou meta.
            # Recarregamos para garantir que o estado final seja o correto.
            ctx_final = obter_contexto(tel)
            estado_final = ctx_final.get("estado", estado_anterior) # Usa estado atualizado se o agente mudou
            meta_final = ctx_final.get("meta_conversa", meta_conversa)
            ultimo_bot = ctx_final.get("ultimo_texto_bot", "") # Resposta que o agente enviou (se ele salvou)

            # Salva o ESTADO FINAL definido pelo agente (ou o anterior se não mudou)
            # Não precisa salvar outros campos aqui se o agente já salvou via executar()
            # Apenas garante que o estado final esteja correto
            if estado_final != estado_anterior:
                 logger.info(f"MCP: Agente '{agente_nome}' alterou estado para '{estado_final}' para {tel}.")
                 # O salvar_contexto dentro de agente.executar() já deve ter salvo o estado novo.
                 # Se quisermos ter certeza, podemos chamar salvar_contexto aqui APENAS com o estado:
                 # salvar_contexto(telefone=tel, estado=estado_final, incrementar_interacoes=False)
            else:
                 logger.info(f"MCP: Estado final para {tel} após agente '{agente_nome}': {estado_final} (inalterado pelo agente)")


        except Exception as exc:
            logger.exception(f"MCP: Erro durante execução do Agente '{agente_nome}' para {tel}: {exc}")
            registrar_evento(tel, etapa="erro_execucao_agente", dados={"agente": agente_nome, "intent": intent, "err": str(exc)})
            try:
                await enviar_mensagem(tel, "Desculpe, ocorreu um erro ao processar sua solicitação. Tente novamente.")
            except Exception as send_err:
                 logger.error(f"MCP: Falha ao enviar mensagem de erro para {tel} após falha do agente: {send_err}")

