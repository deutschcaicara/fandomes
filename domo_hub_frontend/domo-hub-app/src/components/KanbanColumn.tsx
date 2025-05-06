/* ---------------------------------------------------------------------------
Coluna do Kanban
CORREÇÃO: Substituído classes 'slate' por 'neutral'
--------------------------------------------------------------------------- */

import React from 'react';
import { useDroppable } from '@dnd-kit/core';
import type { KanbanCardProps } from './KanbanCard';
import KanbanCard from './KanbanCard';

// Define as props que o componente KanbanColumn espera receber
interface KanbanColumnProps extends React.HTMLAttributes<HTMLDivElement> {
  nome: string; // Título da coluna
  cards: KanbanCardProps[]; // Array de cards a serem exibidos
}

const KanbanColumn: React.FC<KanbanColumnProps> = ({ nome, cards, className = '', ...rest }) => {
  // Configura a coluna como uma área "soltável" para o Drag and Drop
  const { setNodeRef, isOver } = useDroppable({
      id: nome, // Usa o nome da coluna como ID único para o DND
      data: { coluna: nome } // Dados extras associados à área soltável
  });

  return (
    // Container principal da coluna
    // CORREÇÃO: Trocado bg-slate-50, border-slate-300
    <div
      ref={setNodeRef} // Referência para o DND Kit
      className={`flex flex-col bg-neutral-50 rounded-lg border border-neutral-300 p-3 ${className}`}
      {...rest} // Permite passar outras props HTML (como 'style')
    >
      {/* Título da Coluna e Contagem de Cards */}
      <h2 className="text-sm font-semibold mb-2 uppercase tracking-wide">
        {nome} ({cards.length})
      </h2>

      {/* Área que contém os cards e permite scroll vertical */}
      <div className={`flex-1 overflow-y-auto ${isOver ? 'bg-emerald-50 border' : ''}`}> {/* Feedback visual ao arrastar sobre */}
        {/* Mapeia e renderiza cada card */}
        {cards.map((card) => (
          <KanbanCard key={card.id} {...card} />
        ))}
        {/* Mensagem exibida se a coluna estiver vazia */}
        {/* CORREÇÃO: Trocado text-slate-400 */}
        {cards.length === 0 && (
          <div className="text-xs text-neutral-400 text-center mt-4">Sem conversas</div>
        )}
      </div>
    </div>
  );
};

export default KanbanColumn;
