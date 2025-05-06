from pydantic import BaseModel

class PagamentoRequest(BaseModel):
    produto_id: str
    email: str
    telefone: str
    redirect_url: str
