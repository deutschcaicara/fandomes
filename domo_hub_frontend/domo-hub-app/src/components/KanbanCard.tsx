/* ---------------------------------------------------------------------------
Card de paciente para o Kanban
CORREÇÃO: Substituído classes 'slate' por 'neutral'
--------------------------------------------------------------------------- */

import React from 'react';
import { useSortable, defaultAnimateLayoutChanges } from '@dnd-kit/sortable';
import type { AnimateLayoutChanges } from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import type { UniqueIdentifier } from '@dnd-kit/core';
import type { CSSProperties } from 'react';
import dayjs from 'dayjs';
import relativeTime from 'dayjs/plugin/relativeTime';
import { useConversaModal } from '@/contexts/ModalConversaContext';

dayjs.extend(relativeTime);

/* -----------------------  Tipos ----------------------- */
export interface KanbanCardProps {
  id: UniqueIdentifier;            // telefone
  nome: string;
  emoji_sentimento: string;
  risco: boolean;
  ultima_mensagem_ts: string | Date;
}

/* -----------------------  Animations ------------------ */
const animateLayoutChanges: AnimateLayoutChanges = (args) =>
  defaultAnimateLayoutChanges(args);   // sem wasDragged

/* -----------------------  Componente ------------------ */
const KanbanCard: React.FC<KanbanCardProps> = ({
  id,
  nome,
  emoji_sentimento,
  risco,
  ultima_mensagem_ts,
}) => {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } =
    useSortable({ id }); // Usa 'id' que agora é o telefone (UniqueId)

  const { abrir } = useConversaModal();

  const style: CSSProperties = {
    transform: CSS.Translate.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  };

  return (
    // CORREÇÃO: Trocado border-slate-200
    <div
      ref={setNodeRef}
      style={style}
      className="bg-white shadow rounded-lg p-3 mb-2 border border-neutral-200"
      {...attributes}
      {...listeners}
    >
      <div className="flex justify-between items-center">
        <span className="font-medium truncate">{nome}</span>
        <span className="text-xl">{emoji_sentimento}</span>
      </div>

      {/* CORREÇÃO: Trocado text-slate-500 */}
      <div className="text-xs text-neutral-500 mt-1">
        Última mensagem: {dayjs(ultima_mensagem_ts).fromNow()}
      </div>

      {risco && (
        <div className="mt-1 text-xs text-red-600 font-semibold">
          ⚠ Risco Detectado
        </div>
      )}

      {/* CORREÇÃO: Trocado bg-slate-200, hover:bg-slate-300 */}
      <button
        className="mt-2 w-full text-xs px-2 py-1 bg-neutral-200 hover:bg-neutral-300 rounded"
        onClick={() => abrir(String(id))} // Converte id para string
      >
        ver conversa
      </button>
    </div>
  );
};

export default KanbanCard;
