from pydantic import BaseModel
from typing import Optional, Dict
from datetime import datetime

class Lead(BaseModel):
    paciente_id: str
    canal: str
    mensagem_original: str
    intent: str
    entidades: Dict
    risco: bool
    timestamp: datetime
    tipo: Optional[str] = "desconhecido"
