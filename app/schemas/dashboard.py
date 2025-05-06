        # ===========================================================
        # Arquivo: app/schemas/dashboard.py
        # Define os modelos de dados (Pydantic) para as rotas do dashboard.
        # ===========================================================
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class ConversationCard(BaseModel):
            """Modelo para os cards no Kanban."""
            tel: str
            nome: Optional[str] = None
            estado: str
            ultima_interacao_ts: datetime = Field(alias="ts") # Timestamp da última atualização do contexto
            ultima_mensagem_snippet: Optional[str] = None # Snippet da última msg bot ou user
            sentimento_predominante: Optional[str] = None # 'positivo', 'negativo', 'neutro'
            score_lead: Optional[int] = None
            risco_detectado: Optional[bool] = False
            atendente_humano_necessario: Optional[bool] = False # Se estado é AGUARDANDO_ATENDENTE, etc.

            class Config:
                allow_population_by_field_name = True # Permite usar 'ts' como alias
                orm_mode = True # Para compatibilidade se vier do ORM

class KanbanColumn(BaseModel):
            """Modelo para uma coluna no Kanban."""
            id: str # Ex: 'entrada', 'qualificacao'
            title: str # Ex: 'Entrada', 'Qualificação'
            cards: List[ConversationCard]

class KanbanBoard(BaseModel):
            """Modelo para o quadro Kanban completo."""
            columns: List[KanbanColumn]

class Message(BaseModel):
            """Modelo para uma mensagem no histórico do chat."""
            id: str # ID único da mensagem (pode ser o _id do MongoDB)
            timestamp: datetime = Field(alias="criado_em")
            sender: str # 'user', 'bot', 'human'
            text: str = Field(alias="mensagem_usuario_ou_resposta_gerada") # Mapear do DB
            intent: Optional[str] = None # Se for mensagem do usuário
            sentimento: Optional[Dict[str, float]] = None # Se for mensagem do usuário

            class Config:
                allow_population_by_field_name = True
                orm_mode = True

class ConversationDetail(BaseModel):
            """Modelo para os detalhes de uma conversa."""
            tel: str
            nome: Optional[str] = None
            estado: str
            contexto: Dict[str, Any] # O documento completo de contexto do MongoDB
            historico: List[Message] # Lista de mensagens formatadas
class UpdateStateRequest(BaseModel):
            """Modelo para requisição de atualização de estado."""
            novo_estado: str

class SendHumanMessageRequest(BaseModel):
            """Modelo para requisição de envio de mensagem humana."""
            texto: str

class SimulateUserMessageRequest(BaseModel):
            """Modelo para requisição de simulação de mensagem."""
            texto: str

        # --- Modelos de Autenticação Simples ---
class Token(BaseModel):
            access_token: str
            token_type: str

class User(BaseModel):
             username: str
             disabled: Optional[bool] = None

class UserInDB(User):
             hashed_password: str

        