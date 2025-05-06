/* ---------------------------------------------------------------------------
Wrapper Axios ‑ Compatível com rotas NOVAS (/kanban, /sugestao)
e rotas LEGADAS (/dashboard/…)
--------------------------------------------------------------------------- */

import axios from 'axios';
import type { ColunaNome } from '@/pages/DashboardKanban';
import type { KanbanCardProps } from '@/components/KanbanCard';
import type { KanbanBoardData, ConversationDetailData, AnalyticsData } from '../types';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  timeout: 10000,
});

/* =====================================================================
   NOVA API – USADA PELO NOVO KANBAN
   ===================================================================== */
export interface KanbanQuadroResp {
  colunas: Record<ColunaNome, KanbanCardProps[]>;
}

export const obterQuadroKanban = async (): Promise<KanbanQuadroResp> => {
  const { data } = await api.get('/kanban');
  return data;
};

export const moverConversa = async (
  telefone: string,
  novoEstado: ColunaNome,
): Promise<void> => {
  await api.put(`/kanban/${telefone}`, { novo_estado: novoEstado });
};

export const obterConversaCompleta = async (
  telefone: string,
): Promise<Record<string, unknown>[]> => {
  const { data } = await api.get(`/kanban/conversa/${telefone}`);
  return data;
};

export const responderHumano = async (
  telefone: string,
  texto: string,
  respondente = 'Profissional',
): Promise<void> => {
  await api.post('/kanban/responder_humano', { telefone, mensagem: texto, respondente });
};

export const obterSugestaoIA = async (telefone: string): Promise<string> => {
  const { data } = await api.get(`/sugestao/${telefone}`);
  return data.sugestao;
};

/* =====================================================================
   ⬇️  FUNÇÕES LEGADAS  — mantidas p/ arquivos antigos
   ===================================================================== */

/* ---- KanbanBoard / legacy ---- */
export const getKanbanBoard = async (): Promise<KanbanBoardData> => {
  const { data } = await api.get('/dashboard/kanban');
  return data;
};

export const updateConversationState = async (
  telefone: string,
  novoEstado: string,
): Promise<void> => {
  await api.put(`/dashboard/conversations/${telefone}/state`, { novo_estado: novoEstado });
};

/* ---- Conversa detalhada / legacy ---- */
export const getConversationDetail = async (
  telefone: string,
): Promise<ConversationDetailData> => {
  const { data } = await api.get(`/dashboard/conversations/${telefone}`);
  return data;
};

export const sendHumanMessage = async (
  telefone: string,
  texto: string,
): Promise<{ status: string }> => {
  const { data } = await api.post(`/dashboard/conversations/${telefone}/send_human`, { texto });
  return data;
};

export const simulateUserMessage = async (
  telefone: string,
  texto: string,
): Promise<unknown> => {
  const { data } = await api.post(`/dashboard/conversations/${telefone}/simulate_user`, { texto });
  return data;
};

/* ---- Analytics / legacy ---- */
export const getAnalytics = async (): Promise<AnalyticsData> => {
  const { data } = await api.get('/dashboard/analytics');
  return data;
};

export default api;
