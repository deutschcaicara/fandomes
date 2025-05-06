from fastapi import APIRouter, HTTPException
from app.utils.contexto import limpar_contexto

router = APIRouter()

@router.post("/painel/resetar-contexto/{telefone}")
def resetar_contexto(telefone: str):
    if not telefone:
        raise HTTPException(status_code=400, detail="Telefone é obrigatório.")
    
    try:
        sucesso = limpar_contexto(telefone)
        if sucesso:
            return {"status": "resetado", "telefone": telefone}
        else:
            raise HTTPException(status_code=500, detail="Falha ao tentar limpar o contexto.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro inesperado: {str(e)}")
