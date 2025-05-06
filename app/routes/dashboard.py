# ===========================================================
# Arquivo: app/routes/dashboard.py
# Define as rotas da API FastAPI para o frontend do Domo Hub.
# VERIFICAÇÃO FINAL DE INDENTAÇÃO: Linhas de import e nível superior
# devem começar na coluna 1, sem espaços antes.
# ===========================================================
import logging # <-- SEM ESPAÇOS ANTES
from fastapi import APIRouter, Depends, HTTPException, status, Body
from fastapi.security import OAuth2PasswordRequestForm
from typing import List, Dict, Any, Optional
from datetime import timedelta, datetime, timezone

# Imports da aplicação
try:
    from app.schemas.dashboard import (
        KanbanBoard, KanbanColumn, ConversationCard, ConversationDetail, Message,
        UpdateStateRequest, SendHumanMessageRequest, SimulateUserMessageRequest,
        Token, User
    )
    # Usar a versão temporária de auth.py que ignora a senha
    from app.core.auth import (
        create_access_token, get_current_active_user, # MANTÉM ESTES
        ACCESS_TOKEN_EXPIRE_MINUTES, oauth2_scheme
        # authenticate_user # Comentado na versão temporária
    )
    from app.utils.contexto import obter_contexto, salvar_contexto, respostas_ia_db, contextos_db
    from app.utils.mensageria import enviar_mensagem
    from app.core.mcp_orquestrador import MCPOrquestrador
# Indentação correta
except ImportError as e:
    # Indentação correta
    logging.basicConfig(level="INFO")
    logging.critical(f"DASHBOARD_API: Erro Crítico de Importação: {e}. Verifique os caminhos.")
    raise e

# Nível superior - sem indentação
logger = logging.getLogger("famdomes.dashboard_api")
router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

# --- Rota de Autenticação (Temporária) ---
@router.post("/token", response_model=Token, summary="Obtém token de acesso (LOGIN TEMPORÁRIO)")
async def login_for_access_token_temporary(form_data: OAuth2PasswordRequestForm = Depends()):
    # Indentação de 4 espaços
    """
    *** LOGIN TEMPORÁRIO E INSEGURO PARA DESENVOLVIMENTO ***
    Gera um token para o usuário 'admin' (ou o digitado) sem verificar a senha.
    """
    username_for_token = form_data.username
    logger.warning(f"!!! USANDO LOGIN TEMPORÁRIO E INSEGURO para usuário: '{username_for_token}' !!!")

    if not username_for_token:
         raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username cannot be empty"
         )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": username_for_token},
        expires_delta=access_token_expires
    )
    logger.info(f"Token TEMPORÁRIO gerado com sucesso para usuário: '{username_for_token}'")
    return {"access_token": access_token, "token_type": "bearer"}

# --- Rota para verificar usuário atual ---
@router.get("/users/me", response_model=User, summary="Obtém informações do usuário atual")
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    """Retorna os dados do usuário autenticado pelo token."""
    logger.info(f"Rota /users/me acessada por usuário: {current_user.username}")
    return current_user

# --- Rota do Kanban ---
@router.get("/kanban", response_model=KanbanBoard, summary="Obtém dados do quadro Kanban")
async def get_kanban_board(current_user: User = Depends(get_current_active_user)):
    """Busca conversas no MongoDB e as organiza nas colunas do Kanban."""
    logger.info(f"Usuário '{current_user.username}' solicitou dados do Kanban.")
    if contextos_db is None:
         logger.error("API Kanban: DB não conectado.")
         raise HTTPException(status_code=503, detail="Serviço indisponível (DB)")

    colunas_definidas: Dict[str, str] = {
        "entrada": "Entrada", "qualificacao": "Qualificação", "proposta": "Proposta",
        "pagamento_pendente": "Pagamento Pendente", "triagem": "Triagem Pós-Pgto",
        "agendado": "Agendado", "atendimento_humano": "Atendimento Humano",
        "followup": "Follow-up", "concluido": "Concluído/Perdido",
    }
    mapa_estado_coluna: Dict[str, str] = {
        "INICIAL": "entrada", "ACOLHIMENTO_ENVIADO": "entrada",
        "MICRO_COMPROMISSO": "qualificacao",
        "PITCH_PLANO1": "proposta", "PITCH_PLANO3": "proposta", "COMERCIAL_DETALHES_PLANO": "proposta",
        "CALL_TO_ACTION": "pagamento_pendente", "AGUARDANDO_PAGAMENTO": "pagamento_pendente",
        "TRIAGEM_INICIAL": "triagem", "COLETANDO_RESPOSTA_QUESTIONARIO": "triagem",
        "FINALIZANDO_ONBOARDING": "agendado", "AGUARDANDO_CONSULTA": "agendado",
        "AGUARDANDO_ATENDENTE": "atendimento_humano", "RISCO_DETECTADO": "atendimento_humano", "ATENDIMENTO_EM_ANDAMENTO": "atendimento_humano",
        "RECUSA_PRECO": "followup",
        "LEAD_MATERIAL_GRATUITO": "concluido", "FINALIZADO_SEM_VENDA": "concluido",
    }
    coluna_default = "concluido"

    try:
        all_contexts_cursor = contextos_db.find().sort("ts", -1).limit(200)
        all_contexts = list(all_contexts_cursor)
        logger.info(f"API Kanban: {len(all_contexts)} contextos encontrados.")

        cards_por_coluna: Dict[str, List[ConversationCard]] = {col_id: [] for col_id in colunas_definidas}

        for ctx in all_contexts:
            estado_atual = ctx.get("estado", "INICIAL")
            coluna_id = mapa_estado_coluna.get(estado_atual, coluna_default)
            meta = ctx.get("meta_conversa", {})
            if not isinstance(meta, dict): meta = {}

            card_data = {
                "tel": ctx.get("tel", "N/A"),
                "nome": meta.get("nome_cliente") or ctx.get("nome"),
                "estado": estado_atual,
                "ts": ctx.get("ts", datetime.now(timezone.utc)),
                "ultima_mensagem_snippet": (ctx.get("ultimo_texto_bot") or ctx.get("ultimo_texto_usuario", ""))[:50] + "...",
                "score_lead": meta.get("score_lead"),
                "risco_detectado": meta.get("ultimo_risco") is not None,
                "atendente_humano_necessario": estado_atual in ["AGUARDANDO_ATENDENTE", "RISCO_DETECTADO"]
            }
            sentimento = meta.get("ultimo_sentimento_detectado")
            if isinstance(sentimento, dict) and sentimento:
                 card_data["sentimento_predominante"] = max(sentimento, key=sentimento.get, default=None)

            cards_por_coluna.get(coluna_id, cards_por_coluna[coluna_default]).append(ConversationCard(**card_data))

        kanban_columns = [
            KanbanColumn(id=col_id, title=title, cards=cards_por_coluna[col_id])
            for col_id, title in colunas_definidas.items()
        ]
        return KanbanBoard(columns=kanban_columns)

    except Exception as e:
        logger.exception(f"API Kanban: Erro ao buscar ou processar dados: {e}")
        raise HTTPException(status_code=500, detail="Erro ao gerar dados do Kanban.")

# --- Rotas de Conversa ---
@router.get("/conversations/{telefone}", response_model=ConversationDetail, summary="Obtém detalhes de uma conversa")
async def get_conversation_detail(telefone: str, current_user: User = Depends(get_current_active_user)):
    """Busca o contexto e o histórico de mensagens para um telefone específico."""
    logger.info(f"Usuário '{current_user.username}' solicitou detalhes da conversa de {telefone}.")
    if contextos_db is None or respostas_ia_db is None:
         logger.error(f"API Detalhes ({telefone}): DB não conectado.")
         raise HTTPException(status_code=503, detail="Serviço indisponível (DB)")

    try:
        contexto_doc = obter_contexto(telefone)
        if not contexto_doc or "tel" not in contexto_doc :
             logger.warning(f"API Detalhes ({telefone}): Contexto não encontrado ou inválido.")
             raise HTTPException(status_code=404, detail="Conversa não encontrada.")

        historico_cursor = respostas_ia_db.find({"telefone": telefone}).sort("criado_em", 1).limit(200)

        historico_formatado: List[Message] = []
        last_timestamp = None
        for msg_doc in historico_cursor:
            doc_id = str(msg_doc.get("_id"))
            timestamp = msg_doc.get("criado_em", datetime.now(timezone.utc))

            if msg_doc.get("mensagem_usuario"):
                 user_ts = timestamp - timedelta(milliseconds=10) if last_timestamp and timestamp == last_timestamp else timestamp
                 historico_formatado.append(Message(
                     id=f"{doc_id}_user",
                     criado_em=user_ts,
                     sender="user",
                     mensagem_usuario_ou_resposta_gerada=msg_doc.get("mensagem_usuario"),
                     intent=msg_doc.get("intent_detectada"),
                     sentimento=msg_doc.get("sentimento_detectado")
                 ))

            if msg_doc.get("resposta_gerada"):
                sender = "human" if msg_doc.get("enviado_por_humano") else "bot"
                historico_formatado.append(Message(
                    id=doc_id,
                    criado_em=timestamp,
                    sender=sender,
                    mensagem_usuario_ou_resposta_gerada=msg_doc.get("resposta_gerada"),
                    intent=None,
                    sentimento=None
                ))
            last_timestamp = timestamp

        meta = contexto_doc.get("meta_conversa", {})
        if not isinstance(meta, dict): meta = {}

        return ConversationDetail(
            tel=contexto_doc.get("tel"),
            nome=meta.get("nome_cliente") or contexto_doc.get("nome"),
            estado=contexto_doc.get("estado"),
            contexto=contexto_doc,
            historico=historico_formatado
        )

    except HTTPException as http_exc:
         raise http_exc
    except Exception as e:
        logger.exception(f"API Detalhes ({telefone}): Erro ao buscar dados: {e}")
        raise HTTPException(status_code=500, detail="Erro ao buscar detalhes da conversa.")

@router.put("/conversations/{telefone}/state", status_code=status.HTTP_204_NO_CONTENT, summary="Atualiza o estado de uma conversa")
async def update_conversation_state(
    telefone: str,
    request_body: UpdateStateRequest,
    current_user: User = Depends(get_current_active_user)
):
    """Permite atualizar manualmente o estado de uma conversa."""
    novo_estado = request_body.novo_estado
    logger.info(f"Usuário '{current_user.username}' solicitou mudança de estado para '{novo_estado}' para {telefone}.")

    sucesso = salvar_contexto(
        telefone=telefone,
        estado=novo_estado,
        incrementar_interacoes=False
    )
    if not sucesso:
        logger.error(f"API Update State ({telefone}): Falha ao salvar novo estado '{novo_estado}'.")
        raise HTTPException(status_code=500, detail="Falha ao atualizar estado da conversa.")
    logger.info(f"API Update State ({telefone}): Estado atualizado para '{novo_estado}' com sucesso.")


@router.post("/conversations/{telefone}/send_human", status_code=status.HTTP_201_CREATED, summary="Envia mensagem como humano")
async def send_human_message(
    telefone: str,
    request_body: SendHumanMessageRequest,
    current_user: User = Depends(get_current_active_user)
):
    """Envia uma mensagem para o usuário via WhatsApp como se fosse um atendente humano."""
    texto_mensagem = request_body.texto
    logger.info(f"Usuário '{current_user.username}' enviando mensagem humana para {telefone}: '{texto_mensagem[:50]}...'")

    if not texto_mensagem:
        raise HTTPException(status_code=400, detail="Texto da mensagem não pode ser vazio.")

    try:
        resultado_envio = await enviar_mensagem(telefone, texto_mensagem)

        if resultado_envio.get("status") != "enviado" and resultado_envio.get("code") != 200:
             logger.error(f"API Send Human ({telefone}): Falha ao enviar mensagem via WhatsApp: {resultado_envio.get('erro')}")
             raise HTTPException(status_code=502, detail=f"Falha ao enviar mensagem: {resultado_envio.get('erro')}")

        from app.utils.contexto import salvar_resposta_ia
        salvou_hist = salvar_resposta_ia(
            telefone=telefone,
            canal="dashboard",
            mensagem_usuario="",
            resposta_gerada=texto_mensagem,
            intent="intervencao_humana",
            nome_agente=current_user.username,
            enviado_por_humano=True
        )
        if not salvou_hist:
             logger.error(f"API Send Human ({telefone}): Mensagem enviada, mas FALHA ao salvar no histórico.")

        salvou_ctx = salvar_contexto(telefone=telefone, estado="ATENDIMENTO_EM_ANDAMENTO", incrementar_interacoes=False)
        if not salvou_ctx:
             logger.error(f"API Send Human ({telefone}): Mensagem enviada e histórico salvo, mas FALHA ao atualizar estado.")

        logger.info(f"API Send Human ({telefone}): Mensagem enviada e registrada com sucesso.")
        return {"status": "mensagem enviada"}

    except Exception as e:
        logger.exception(f"API Send Human ({telefone}): Erro inesperado: {e}")
        raise HTTPException(status_code=500, detail="Erro interno ao enviar mensagem humana.")

@router.post("/conversations/{telefone}/simulate_user", status_code=status.HTTP_200_OK, summary="Simula mensagem do usuário")
async def simulate_user_message(
    telefone: str,
    request_body: SimulateUserMessageRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    Recebe um texto e o processa pelo MCPOrquestrador como se o usuário
    tivesse enviado essa mensagem. NÃO envia para o WhatsApp.
    """
    texto_simulado = request_body.texto
    logger.info(f"Usuário '{current_user.username}' simulando mensagem para {telefone}: '{texto_simulado[:50]}...'")

    if not texto_simulado:
        raise HTTPException(status_code=400, detail="Texto simulado não pode ser vazio.")

    try:
        orquestrador = MCPOrquestrador()
        await orquestrador.processar_mensagem(telefone, texto_simulado)
        contexto_atualizado = obter_contexto(telefone)

        logger.info(f"API Simulate User ({telefone}): Simulação processada. Estado final: {contexto_atualizado.get('estado')}")
        return {
            "status": "simulacao_concluida",
            "estado_resultante": contexto_atualizado.get("estado"),
            "resposta_bot_simulada": contexto_atualizado.get("ultimo_texto_bot"),
        }

    except Exception as e:
        logger.exception(f"API Simulate User ({telefone}): Erro durante simulação: {e}")
        raise HTTPException(status_code=500, detail="Erro interno ao simular mensagem.")

