from pydantic import BaseModel

class IAComandoInput(BaseModel):
    telefone: str
    nome: str
    comando: str
