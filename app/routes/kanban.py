"""
Rotas Kanban e Conversas – FAMDOMES
Autor: Diego Feijó de Abreu
Descrição: fornece a API REST para o dashboard Kanban de conversas
            (Novos → IA Respondendo → Triagem Emocional → Aguardando Agendamento
            → Com Profissional → Escalonado → Finalizado)
"""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional

from fastapi import APIRouter, HTTPException, status, Body, Path
from pydantic import BaseModel, Field
from bson import ObjectId

from app.utils.contexto import (
    contextos_db,
    respostas_ia_db,
    obter_contexto,
    salvar_contexto,
    salvar_resposta_ia,
)

router = APIRouter(prefix="/kanban", tags=["Kanban"])

# ---------------------------
# ⬇️  Modelos de Dados
# ---------------------------


class KanbanCard(BaseModel):
    id: str = Field(..., description="ID da conversa (telefone)")
    nome: Optional[str] = Field(None, description="Nome do paciente se disponível")
    emoji_sentimento: str = Field(..., description="Emoji do sentimento detectado")
    risco: bool = Field(False, description="Flag de risco detectado")
    ultima_mensagem_ts: datetime = Field(..., description="Data/hora da última mensagem")


class KanbanColuna(BaseModel):
    nome: str
    cards: List[KanbanCard]


class KanbanQuadro(BaseModel):
    colunas: Dict[str, List[KanbanCard]]


class AtualizaEstadoReq(BaseModel):
    novo_estado: str = Field(..., description="Novo estado da conversa")


class RespostaHumanaReq(BaseModel):
    telefone: str = Field(..., description="Telefone do paciente")
    mensagem: str = Field(..., description="Texto a ser enviado")
    respondente: str = Field(..., description="Nome do profissional")


# ---------------------------
# ⬇️  Constantes e Utilidades
# ---------------------------

ESTADOS_KANBAN = {
    "Novos": ["INICIAL", "IDENTIFICANDO_NECESSIDADE"],
    "IA Respondendo": ["SUPORTE_FAQ", "IA_RESPONDENDO"],
    "Triagem Emocional": ["AGUARDANDO_RESPOSTA_QUALIFICACAO", "COLETANDO_RESPOSTA_QUESTIONARIO"],
    "Aguardando Agendamento": ["EXPLICANDO_CONSULTA", "AGUARDANDO_PAGAMENTO", "CONFIRMANDO_AGENDAMENTO"],
    "Com Profissional": ["AGUARDANDO_ATENDENTE", "COM_PROFISSIONAL"],
    "Escalonado": ["ESCALONADO", "RISCO_DETECTADO"],
    "Finalizado": ["FINALIZANDO_ONBOARDING", "FINALIZADO", "ENCERRADO"],
}

EMOJI_SENTIMENTO = {
    "positivo": "🙂",
    "negativo": "🙁",
    "neutro": "😐",
    "ansioso": "😰",
    "esperançoso": "🤞",
    "frustrado": "😣",
    "confuso": "😕",
}


def _sentimento_to_emoji(sent: Optional[str]) -> str:
    return EMOJI_SENTIMENTO.get(str(sent).lower(), "🟡")


def _contexto_para_card(ctx: Dict[str, Any]) -> KanbanCard:
    meta = ctx.get("meta_conversa", {}) or {}
    tel = ctx["tel"]
    nome = meta.get("nome_paciente") or ctx.get("nome") or "Paciente"
    sentimento = meta.get("ultimo_sentimento_detectado")
    risco_flag = bool(meta.get("ultimo_risco"))
    ts = ctx.get("ts") or ctx.get("criado_em") or datetime.now(timezone.utc)
    return KanbanCard(
        id=str(tel),
        nome=nome,
        emoji_sentimento=_sentimento_to_emoji(sentimento),
        risco=risco_flag,
        ultima_mensagem_ts=ts,
    )


def _carregar_quadro() -> KanbanQuadro:
    quadro: Dict[str, List[KanbanCard]] = {col: [] for col in ESTADOS_KANBAN}
    cursor = contextos_db.find({}, {"_id": 0})
    for ctx in cursor:
        estado = ctx.get("estado", "INICIAL")
        coluna_destino = next(
            (col for col, estados in ESTADOS_KANBAN.items() if estado in estados),
            "Novos",
        )
        quadro[coluna_destino].append(_contexto_para_card(ctx))

    # Ordena cada coluna pela data da última mensagem (mais recente no topo)
    for col in quadro:
        quadro[col].sort(key=lambda c: c.ultima_mensagem_ts, reverse=True)

    return KanbanQuadro(colunas=quadro)


# ---------------------------
# ⬇️  Rotas
# ---------------------------


@router.get("/", response_model=KanbanQuadro, summary="Quadro Kanban completo")
async def get_kanban() -> KanbanQuadro:
    """
    Retorna todas as conversas agrupadas por estado Kanban.
    """
    return _carregar_quadro()


@router.put(
    "/{conversa_id}",
    status_code=200,                     # ← trocado de 204 para 200
    summary="Atualiza o estado de uma conversa",
)
async def atualizar_estado_conversa(
    conversa_id: str = Path(..., description="Telefone do paciente"),
    payload: AtualizaEstadoReq = Body(...),
) -> dict:
    """
    Move a conversa para outra coluna/estado.
    """
    novo_estado = payload.novo_estado
    if novo_estado not in {e for lst in ESTADOS_KANBAN.values() for e in lst}:
        raise HTTPException(400, "Estado inválido")

    res = contextos_db.update_one({"tel": conversa_id}, {"$set": {"estado": novo_estado}})
    if res.matched_count == 0:
        raise HTTPException(404, "Conversa não encontrada")

    return {"status": "ok"}            # ← devolve algo, já que é 200



@router.get(
    "/conversa/{telefone}",
    summary="Histórico completo da conversa",
)
async def get_conversa(telefone: str) -> List[Dict[str, Any]]:
    """
    Retorna o histórico da conversa em ordem cronológica crescente.
    Inclui mensagens do usuário, IA e humanos.
    """
    cursor = respostas_ia_db.find(
        {"telefone": telefone},
        {"_id": 0},
    ).sort("criado_em", 1)
    return list(cursor)


@router.post(
    "/responder_humano",
    status_code=status.HTTP_201_CREATED,
    summary="Insere resposta manual no histórico",
)
async def responder_humano(req: RespostaHumanaReq) -> Dict[str, str]:
    """
    Profissional envia uma resposta manual ao paciente;
    registra no histórico e bloqueia IA se necessário.
    """
    ctx = obter_contexto(req.telefone)
    if not ctx:
        raise HTTPException(status_code=404, detail="Conversa não encontrada")

    salvar_resposta_ia(
        telefone=req.telefone,
        canal="whatsapp",
        mensagem_usuario=f"[HUMANO {req.respondente}]",
        resposta_gerada=req.mensagem,
        intent="resposta_humana",
        entidades={},
        risco_detectado=False,
        sentimento_detectado=None,
        enviado_por_humano=True,
    )

    # Desativa IA se conversa for assumida por humano
    salvar_contexto(req.telefone, estado="COM_PROFISSIONAL")
    return {"status": "ok"}


@router.get(
    "/risco_ativos",
    summary="Pacientes com risco detectado (últimas 48h)",
)
async def get_risco_ativos() -> List[Dict[str, Any]]:
    """
    Lista pacientes que apresentaram risco detectado nas últimas 48 horas.
    """
    limite = datetime.now(timezone.utc) - timedelta(hours=48)
    pipeline = [
        {"$match": {"risco_detectado": True, "criado_em": {"$gte": limite}}},
        {
            "$group": {
                "_id": "$telefone",
                "ultima_msg": {"$max": "$criado_em"},
                "qtd_risco": {"$sum": 1},
            }
        },
        {"$sort": {"ultima_msg": -1}},
    ]
    resultados = list(respostas_ia_db.aggregate(pipeline))
    return [
        {
            "telefone": r["_id"],
            "ultima_msg": r["ultima_msg"],
            "qtd_risco": r["qtd_risco"],
        }
        for r in resultados
    ]


# ---------------------------
# ⬇️  Inclusão no app principal
# ---------------------------
# Adicione no main.py:
#     from app.routes.kanban import router as kanban_router
#     app.include_router(kanban_router)
