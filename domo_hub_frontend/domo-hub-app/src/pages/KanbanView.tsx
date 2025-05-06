// File: src/pages/KanbanView.tsx
// Componente principal para a visualização do Kanban.
// CORREÇÃO: Substituído classes 'slate' por 'neutral'

import React, { useState, useEffect, useCallback } from 'react';
import {
  DragDropContext,
  Droppable,
} from '@hello-pangea/dnd'; // Biblioteca para Drag and Drop
import type { DropResult } from '@hello-pangea/dnd';
import { getKanbanBoard, updateConversationState } from '../services/api';
import type { KanbanBoardData, KanbanState, KanbanColumnData, ConversationCardData } from '../types';
import type { KanbanCardProps } from '../components/KanbanCard';
import KanbanColumn from '../components/KanbanColumn';
import { Loader2, AlertTriangle, RefreshCw } from 'lucide-react';

// Função auxiliar para mapear sentimento para emoji
const getSentimentEmoji = (sentiment?: 'positivo' | 'negativo' | 'neutro'): string => {
  if (sentiment === 'positivo') return '🙂';
  if (sentiment === 'negativo') return '🙁';
  return '😐'; // Default para neutro ou undefined
};

const KanbanView: React.FC = () => {
  const [boardState, setBoardState] = useState<KanbanState | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchBoardData = useCallback(async (isRefreshing = false) => {
    if (!isRefreshing) {
        setError(null);
        setIsLoading(true);
    } else {
        console.log("Refreshing Kanban data...");
    }

    try {
      const boardData: KanbanBoardData = await getKanbanBoard();
      const columnsMap: { [key: string]: KanbanColumnData } = {};
      boardData.columns.forEach(col => {
        columnsMap[col.id] = { ...col, cards: Array.isArray(col.cards) ? col.cards : [] };
      });
      const newState: KanbanState = {
        columns: columnsMap,
        columnOrder: boardData.columns.map(col => col.id),
      };
      setBoardState(newState);
      if (isRefreshing) setError(null);
    } catch (err: any) {
      console.error("Erro ao buscar dados do Kanban:", err);
      const errorMsg = err.code === 'ERR_NETWORK'
          ? "Erro de rede: Não foi possível conectar à API. Verifique se o backend está rodando e acessível."
          : err.response?.data?.detail || err.message || "Falha ao carregar o quadro Kanban.";
      setError(errorMsg);
      if (!isRefreshing) setBoardState(null);
    } finally {
      if (!isRefreshing) setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchBoardData();
  }, [fetchBoardData]);

  const onDragEnd = useCallback(async (result: DropResult) => {
    const { destination, source, draggableId, type } = result;

    if (type !== 'CARD' || !destination) return;
    if (
      destination.droppableId === source.droppableId &&
      destination.index === source.index
    ) return;
    if (!boardState) return;

    const startColumn = boardState.columns[source.droppableId];
    const endColumn = boardState.columns[destination.droppableId];
    if (!startColumn || !endColumn) return;

    const startCards = Array.from(startColumn.cards);
    const draggedCardIndex = startCards.findIndex(card => card.tel === draggableId);
    if (draggedCardIndex === -1) return;
    const [draggedCardData] = startCards.splice(draggedCardIndex, 1);

    const originalState = JSON.parse(JSON.stringify(boardState));

    const newEndCardsData = Array.from(endColumn.cards);
    newEndCardsData.splice(destination.index, 0, draggedCardData);

    const newState: KanbanState = {
      ...boardState,
      columns: {
        ...boardState.columns,
        [startColumn.id]: { ...startColumn, cards: startCards },
        [endColumn.id]: { ...endColumn, cards: newEndCardsData },
      },
    };
    setBoardState(newState);

    const novoEstadoBackend = destination.droppableId;
    try {
      await updateConversationState(draggedCardData.tel, novoEstadoBackend);
      console.log(`Backend update success: State for ${draggedCardData.tel} set to ${novoEstadoBackend}.`);
    } catch (err: any) {
      console.error(`Erro ao atualizar estado no backend para ${draggedCardData.tel}:`, err);
      setError(`Falha ao mover o card ${draggedCardData.tel}. Tentando reverter...`);
      setBoardState(originalState);
    }
  }, [boardState]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full pt-10">
        <Loader2 className="h-10 w-10 animate-spin text-blue-600" />
        {/* CORREÇÃO: Trocado text-slate-600 */}
        <span className="ml-3 text-lg text-neutral-600">Carregando Kanban...</span>
      </div>
    );
  }

  if (error && !boardState) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-red-600 p-6 bg-red-50 rounded-lg border border-red-200">
        <AlertTriangle className="h-12 w-12 mb-3 text-red-500" />
        <p className="text-center font-medium mb-1">Erro ao Carregar Kanban</p>
        <p className="text-center text-sm text-red-700 mb-4">{error}</p>
        <button
            onClick={() => fetchBoardData()}
            className="mt-2 px-5 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2 flex items-center"
        >
            <RefreshCw size={16} className="mr-2"/>
            Tentar Novamente
        </button>
      </div>
    );
  }

  if (!boardState || boardState.columnOrder.length === 0) {
    return (
        // CORREÇÃO: Trocado text-slate-500, bg-slate-100, text-slate-800
        <div className="flex flex-col items-center justify-center h-full text-neutral-500 p-6 bg-neutral-100 rounded-lg">
             <h2 className="text-2xl font-semibold text-neutral-800 mb-5 px-1 flex-shrink-0">
                Fluxo de Atendimento
             </h2>
             <p className="text-center">Nenhuma coluna ou dado para exibir no Kanban.</p>
             <p className="text-center text-sm mt-2">Verifique a API ou aguarde novas conversas.</p>
             <button
                onClick={() => fetchBoardData(true)}
                className="mt-4 px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 transition-colors focus:outline-none focus:ring-2 focus:ring-blue-400 focus:ring-offset-2 flex items-center"
                title="Atualizar dados do Kanban"
             >
                <RefreshCw size={16} className="mr-2"/>
                Atualizar
             </button>
        </div>
    );
  }

  return (
    // CORREÇÃO: Trocado bg-slate-100
    <div className="flex flex-col h-full bg-neutral-100">
       {/* CORREÇÃO: Trocado text-slate-800, text-slate-500, border-slate-300, hover:bg-slate-100, hover:text-slate-700 */}
       <div className="flex justify-between items-center mb-5 px-1 flex-shrink-0">
           <h2 className="text-2xl font-semibold text-neutral-800">
             Fluxo de Atendimento
           </h2>
           {error && (
               <div className="text-xs text-red-600 flex items-center border border-red-200 bg-red-50 px-2 py-1 rounded">
                   <AlertTriangle size={14} className="mr-1"/> {error}
               </div>
           )}
           <button
             onClick={() => fetchBoardData(true)}
             className="p-2 text-neutral-500 bg-white border border-neutral-300 rounded-md hover:bg-neutral-100 hover:text-neutral-700 transition-colors focus:outline-none focus:ring-1 focus:ring-blue-400"
             title="Atualizar dados do Kanban"
           >
             <RefreshCw size={16} />
           </button>
       </div>

       <DragDropContext onDragEnd={onDragEnd}>
         <Droppable droppableId="all-columns" direction="horizontal" type="COLUMN">
            {(provided) => (
                // CORREÇÃO: Trocado scrollbar-thumb-slate-300, scrollbar-track-neutral-100
                <div
                    {...provided.droppableProps}
                    ref={provided.innerRef}
                    className="flex flex-1 space-x-4 overflow-x-auto pb-4 px-1 scrollbar-thin scrollbar-thumb-neutral-300 scrollbar-track-neutral-100"
                >
                {boardState.columnOrder.map((columnId) => {
                    const column = boardState.columns[columnId];
                    if (!column) {
                        console.warn(`Coluna com ID ${columnId} não encontrada no estado.`);
                        return null;
                    }

                    const transformedCards: KanbanCardProps[] = column.cards.map((cardData: ConversationCardData) => ({
                      id: cardData.tel,
                      nome: cardData.nome || 'Desconhecido',
                      emoji_sentimento: getSentimentEmoji(cardData.sentimento_predominante),
                      risco: cardData.risco_detectado ?? false,
                      ultima_mensagem_ts: cardData.ultima_interacao_ts,
                    }));

                    // Passa as props corretas para KanbanColumn
                    return <KanbanColumn key={column.id} nome={column.title} cards={transformedCards} />;
                })}
                {provided.placeholder}
                </div>
            )}
         </Droppable>
       </DragDropContext>
    </div>
  );
};

export default KanbanView;
