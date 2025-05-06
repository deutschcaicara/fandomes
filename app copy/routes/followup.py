# routes/followup.py

from fastapi import APIRouter
from utils.followup import checar_followup

router = APIRouter()

@router.get("/verificar-followup")
def verificar():
    mensagens = checar_followup()
    return {"mensagens": mensagens}
