# ===========================================================
# Arquivo: agents/domo_triagem.py
# Agente responsável pelo questionário pós-pagamento.
# - Envia introdução antes da primeira pergunta.
# - Gerencia o fluxo de perguntas e respostas.
# - Salva as respostas na meta_conversa.
# ===========================================================
from pathlib import Path
import json
import logging
from app.agents.agente_base import AgenteBase
from app.utils.contexto import obter_contexto, salvar_contexto
# Importa a lista de perguntas e a introdução do utilitário
from app.utils.questionario_pos_pagamento import QUESTIONARIO_COMPLETO_POS_PAGAMENTO, INTRODUCAO_QUESTIONARIO

logger = logging.getLogger("famdomes.domo_triagem")

# Define o ID da trilha para o contexto (pode ser configurável)
TRILHA_ID = "QUESTIONARIO_POS_PAGAMENTO"
# Mensagem de agradecimento ao final
MENSAGEM_AGRADECIMENTO_ONBOARDING = "Obrigado por compartilhar essas informações! Elas são muito importantes e ajudarão o profissional na sua consulta. Em breve ele(a) entrará em contato no horário agendado."

class DomoTriagem(AgenteBase):
    """
    Conduz o questionário de triagem após a confirmação do pagamento.
    """

    async def _gerar_resposta(self, telefone: str, mensagem_original: str) -> str | None:
        """
        Gera a próxima pergunta do questionário ou a mensagem final.
        """
        ctx = obter_contexto(telefone)
        meta = ctx.get("meta_conversa", {})
        # Usa um campo específico para o cursor do questionário na meta
        cursor_questionario = meta.get("cursor_questionario", {"id": TRILHA_ID, "etapa_atual": 0})

        # Validação inicial: Garante que estamos na trilha correta
        if cursor_questionario.get("id") != TRILHA_ID:
            logger.warning(f"DomoTriagem: Cursor inválido para {telefone}. Reiniciando questionário.")
            cursor_questionario = {"id": TRILHA_ID, "etapa_atual": 0}

        etapa_respondida = cursor_questionario.get("etapa_atual", 0) # Etapa que o usuário ACABOU de responder
        proxima_etapa = etapa_respondida + 1

        # --- Salvar Resposta Anterior (se não for a primeira interação) ---
        if etapa_respondida > 0:
            if etapa_respondida <= len(QUESTIONARIO_COMPLETO_POS_PAGAMENTO):
                pergunta_respondida_texto = QUESTIONARIO_COMPLETO_POS_PAGAMENTO[etapa_respondida - 1]
                chave_resposta = f"resposta_q{etapa_respondida}"
                chave_sentimento = f"sentimento_q{etapa_respondida}"
                meta[chave_resposta] = mensagem_original # Salva a resposta do usuário
                meta[chave_sentimento] = self.sentimento # Salva o sentimento da resposta
                logger.info(f"DomoTriagem: Resposta Q{etapa_respondida} ('{pergunta_respondida_texto[:30]}...') salva para {telefone}.")
            else:
                 logger.error(f"DomoTriagem: Índice de etapa respondida ({etapa_respondida}) fora dos limites para {telefone}.")
                 # Considerar um fallback ou mensagem de erro

        # --- Determinar Próximo Passo ---
        resposta = None
        novo_estado_sugerido = "COLETANDO_RESPOSTA_QUESTIONARIO" # Estado padrão durante o questionário

        # Se for a primeira pergunta (etapa_respondida == 0)
        if etapa_respondida == 0:
            if not QUESTIONARIO_COMPLETO_POS_PAGAMENTO:
                 logger.warning(f"DomoTriagem: Lista de perguntas vazia para {telefone}.")
                 resposta = MENSAGEM_AGRADECIMENTO_ONBOARDING # Agradece mesmo sem perguntas
                 novo_estado_sugerido = "FINALIZANDO_ONBOARDING"
                 meta.pop("cursor_questionario", None) # Limpa cursor
            else:
                 # Envia a introdução + primeira pergunta
                 primeira_pergunta = QUESTIONARIO_COMPLETO_POS_PAGAMENTO[0]
                 resposta = f"{INTRODUCAO_QUESTIONARIO}\n\n{primeira_pergunta}"
                 cursor_questionario["etapa_atual"] = 1 # Atualiza cursor para a próxima etapa
                 logger.info(f"DomoTriagem: Iniciando questionário para {telefone}.")

        # Se ainda houver perguntas a fazer
        elif proxima_etapa <= len(QUESTIONARIO_COMPLETO_POS_PAGAMENTO):
            proxima_pergunta_texto = QUESTIONARIO_COMPLETO_POS_PAGAMENTO[proxima_etapa - 1]
            resposta = proxima_pergunta_texto
            cursor_questionario["etapa_atual"] = proxima_etapa # Atualiza cursor
            logger.info(f"DomoTriagem: Enviando pergunta Q{proxima_etapa} para {telefone}.")

        # Se terminou o questionário
        else:
            resposta = MENSAGEM_AGRADECIMENTO_ONBOARDING
            novo_estado_sugerido = "FINALIZANDO_ONBOARDING" # Ou um estado como "AGUARDANDO_CONSULTA"
            meta.pop("cursor_questionario", None) # Limpa o cursor da meta
            logger.info(f"DomoTriagem: Questionário finalizado para {telefone}.")


        # --- Salvar Contexto ---
        # Salva a meta_conversa atualizada (com respostas e novo cursor) e o estado sugerido
        meta["cursor_questionario"] = cursor_questionario # Atualiza o cursor na meta
        salvar_contexto(telefone=telefone, meta_conversa=meta, estado=novo_estado_sugerido)

        return resposta

