# ===========================================================
# Arquivo: agents/agente_base.py
# Classe-base para todos os agentes DOMO
# - Garante que sentimento seja armazenado.
# - Mantém método para carregar intents.
# ===========================================================
from __future__ import annotations

import json
import logging # Adicionado logging
from pathlib import Path
from typing import Dict, Any, Optional

# Assume que intents.py está em core
from app.core.intents import obter_intent
# Assume que mensageria.py está em utils
from app.utils.mensageria import enviar_mensagem
# Assume que contexto.py está em utils
from app.utils.contexto import salvar_contexto, obter_contexto # Adicionado obter_contexto

logger = logging.getLogger("famdomes.agente_base") # Logger específico

class AgenteBase:
    """
    Classe base abstrata para todos os agentes DOMO.
    Cada agente concreto deve implementar _gerar_resposta().
    """

    def __init__(self, intent: str, sentimento: Dict[str, Any] | None = None) -> None:
        """
        Inicializa o agente com a intent detectada e o sentimento da mensagem do usuário.

        Args:
            intent (str): A intenção principal identificada pelo Orquestrador.
            sentimento (Dict[str, Any] | None): Dicionário com scores de sentimento
                                                (ex: {'positivo': 0.1, 'negativo': 0.8, 'neutro': 0.1}).
                                                Pode ser None se a análise falhar.
        """
        self.intent = intent
        # Garante que sentimento seja sempre um dicionário, mesmo que vazio
        self.sentimento: Dict[str, Any] = sentimento if sentimento is not None else {}
        self.nome: str = self.__class__.__name__
        logger.debug(f"Agente '{self.nome}' inicializado com intent '{self.intent}' e sentimento {self.sentimento}")

    # ------------------------------------------------------
    async def executar(self, telefone: str, mensagem_original: str) -> None:
        """
        Método principal chamado pelo MCP Orquestrador.
        1. Chama _gerar_resposta() para obter o texto da resposta.
        2. Envia a resposta via mensageria (se houver).
        3. Salva a resposta do bot no contexto para evitar loops.
        """
        resposta_texto: str | None = None
        try:
            # Chama o método que cada agente implementa para definir sua lógica
            resposta_texto = await self._gerar_resposta(telefone, mensagem_original)

            if resposta_texto:
                logger.info(f"Agente '{self.nome}': Enviando resposta para {telefone}: '{resposta_texto[:60]}...'")
                # Envia a mensagem para o usuário
                resultado_envio = await enviar_mensagem(telefone, resposta_texto)

                # Verifica se o envio foi bem-sucedido antes de salvar no contexto
                if resultado_envio.get("status") == "enviado" or resultado_envio.get("code") == 200:
                    # Salva a resposta enviada no contexto para referência e anti-loop
                    # É importante que o Orquestrador também salve o estado final após a execução
                    salvar_contexto(telefone=telefone, ultimo_texto_bot=resposta_texto)
                    logger.debug(f"Agente '{self.nome}': Resposta salva no contexto de {telefone}.")
                else:
                    logger.error(f"Agente '{self.nome}': Falha ao enviar mensagem para {telefone}. Status: {resultado_envio.get('status')}, Erro: {resultado_envio.get('erro')}")
                    # Não salva ultimo_texto_bot se o envio falhou

            else:
                # Loga se o agente decidiu não responder
                logger.info(f"Agente '{self.nome}' optou por não responder para {telefone} (intent='{self.intent}').")
                # Garante que o ultimo_texto_bot seja limpo ou mantido como estava
                # salvar_contexto(telefone=telefone, ultimo_texto_bot=None) # Ou não fazer nada

        except NotImplementedError:
             logger.error(f"Agente '{self.nome}' não implementou o método _gerar_resposta().")
             # Considerar enviar uma mensagem de erro genérica ou levantar a exceção
             raise # Re-levanta a exceção para o Orquestrador tratar
        except Exception as e:
            logger.exception(f"Agente '{self.nome}': Erro inesperado durante _gerar_resposta ou envio para {telefone}: {e}")
            # Considerar enviar uma mensagem de erro genérica
            await enviar_mensagem(telefone, "Desculpe, ocorreu um erro interno ao processar sua solicitação.")
            # Levanta a exceção para o Orquestrador registrar o erro
            raise

    # ------------------------------------------------------
    async def _gerar_resposta(self, telefone: str, mensagem_original: str) -> str | None:
        """
        Método abstrato que DEVE ser implementado por cada agente concreto.

        Responsável por definir a lógica específica do agente e retornar a string
        da mensagem a ser enviada ao usuário, ou None se o agente não deve responder.

        Args:
            telefone (str): O número de telefone do usuário.
            mensagem_original (str): A mensagem exata que o usuário enviou nesta interação.

        Returns:
            str | None: O texto da resposta a ser enviada, ou None para não enviar nada.
        """
        raise NotImplementedError(f"Agente '{self.nome}' não implementou '_gerar_resposta'")

    # ------------------------------------------------------
    async def _carregar_mensagem_intent(self, intent_id: str) -> Dict[str, Any] | None:
        """
        Utilitário para buscar os dados de uma intent específica (incluindo a resposta)
        nos arquivos JSON carregados por `core/intents.py`.

        Args:
            intent_id (str): O ID da intent a ser buscada (ex: "ACOLHIMENTO", "FAQ_PAGAMENTO").

        Returns:
            Dict[str, Any] | None: Um dicionário contendo os dados da intent (incluindo
                                    'resposta', 'triggers', 'escala_humano', etc.) se encontrada,
                                    ou None caso contrário.
        """
        intent_data = obter_intent(intent_id)
        if not intent_data:
            logger.warning(f"Agente '{self.nome}': Intent '{intent_id}' não encontrada nos arquivos JSON.")
            return None
        # Retorna o dicionário completo da intent
        return intent_data

    # ------------------------------------------------------
    # Métodos utilitários adicionais podem ser adicionados aqui,
    # como chamar a IA para tarefas específicas, formatar dados, etc.
    # Exemplo: Chamar IA para refrasear (pode ficar aqui ou em um utilitário separado)
    async def _refrasear_com_ia(self, texto_original: str, telefone: str, contexto_breve: str = "geral") -> str:
        """Tenta refrasear uma mensagem padrão usando a IA para soar mais natural."""
        # Importa aqui para evitar dependência circular ou coloca em utils/ia_utils.py
        from app.core.ia_direct import gerar_resposta_ia # Ou outra função de IA

        if not texto_original: return ""

        try:
            # Ajuste o prompt conforme necessário para sua IA
            prompt = f"""
            Contexto: {contexto_breve}.
            Reescreva a mensagem abaixo para soar um pouco mais natural e empática, mantendo o sentido original e o tamanho similar.
            Mensagem Original: "{texto_original}"
            Mensagem Reescrevida:
            """
            # Use um contexto específico para a chamada da IA se necessário
            resposta_ia = await gerar_resposta_ia({"prompt_context": prompt})

            if resposta_ia and len(resposta_ia) > 5: # Verifica se a resposta é minimamente válida
                logger.debug(f"Agente '{self.nome}': Texto refraseado para {telefone}: '{resposta_ia[:60]}...'")
                return resposta_ia.strip()
            else:
                logger.warning(f"Agente '{self.nome}': IA não conseguiu refrasear '{texto_original[:30]}...'. Usando original.")
                return texto_original # Retorna original se IA falhar ou resposta for inadequada
        except Exception as e:
            logger.error(f"Agente '{self.nome}': Erro ao chamar IA para refrasear: {e}")
            return texto_original # Retorna original em caso de erro

