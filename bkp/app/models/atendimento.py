from pydantic import BaseModel

class MensagemIA(BaseModel):
    mensagem: str
    paciente_id: str
    canal: str
