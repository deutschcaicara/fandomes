// File: src/types/index.ts
// Define tipos TypeScript para os dados usados no frontend.

export interface UserData {
  username: string;
  disabled?: boolean;
}

export interface ConversationCardData {
  tel: string;
  nome?: string;
  estado: string;
  ultima_interacao_ts: string; // Vem como string ISO do backend
  ultima_mensagem_snippet?: string;
  sentimento_predominante?: 'positivo' | 'negativo' | 'neutro';
  score_lead?: number;
  risco_detectado?: boolean;
  atendente_humano_necessario?: boolean;
}

export interface KanbanColumnData {
  id: string;
  title: string;
  cards: ConversationCardData[];
}

export interface KanbanBoardData {
  columns: KanbanColumnData[];
}

export interface MessageData {
  id: string;
  timestamp: string; // Vem como string ISO
  sender: 'user' | 'bot' | 'human';
  text: string;
  intent?: string;
  sentimento?: Record<string, number>; // {positivo: 0.8, ...}
}

export interface ConversationDetailData {
  tel: string;
  nome?: string;
  estado: string;
  contexto: any; // Objeto de contexto completo (pode tipar melhor depois)
  historico: MessageData[];
}

// Tipo para o estado do Kanban no frontend (para react-beautiful-dnd)
export interface KanbanState {
    columns: {
        [key: string]: KanbanColumnData; // Usa o ID da coluna como chave
    };
    columnOrder: string[]; // Array com a ordem dos IDs das colunas
}
