"""
Rotas de Sugestão de Próximo Passo – FAMDOMES
Gera orientação da IA para o profissional com base no histórico recente
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from app.utils.contexto import obter_contexto
from app.utils.ia import gerar_sugestao_proximo_passo  # wrapper p/ Ollama

router = APIRouter(prefix="/sugestao", tags=["Sugestão"])


class SugestaoResp(BaseModel):
    telefone: str
    sugestao: str


@router.get(
    "/{telefone}",
    response_model=SugestaoResp,
    summary="IA sugere próximo passo para a conversa",
)
async def sugerir_proximo_passo(telefone: str) -> SugestaoResp:
    ctx = obter_contexto(telefone)
    if not ctx:
        raise HTTPException(404, "Conversa não encontrada")

    sugestao = await gerar_sugestao_proximo_passo(ctx)
    return SugestaoResp(telefone=telefone, sugestao=sugestao)


# Adicione no main.py:
#     from app.routes.sugestao import router as sugestao_router
#     app.include_router(sugestao_router)
