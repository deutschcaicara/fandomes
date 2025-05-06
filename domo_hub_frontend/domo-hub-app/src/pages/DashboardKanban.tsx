/* ---------------------------------------------------------------------------
Dashboard Kanban de Conversas
--------------------------------------------------------------------------- */

import React, { useCallback, useEffect, useMemo, useState } from 'react';
import {
  DndContext,
  closestCenter,
  PointerSensor,
  useSensor,
  useSensors,
  type DragEndEvent,
} from '@dnd-kit/core';
import {
  SortableContext,
  arrayMove,
  verticalListSortingStrategy,
} from '@dnd-kit/sortable';
import dayjs from 'dayjs';

import { obterQuadroKanban, moverConversa } from '@/services/api';
import KanbanColumn from '@/components/KanbanColumn';
import type { KanbanCardProps } from '@/components/KanbanCard';

export type ColunaNome =
  | 'Novos'
  | 'IA Respondendo'
  | 'Triagem Emocional'
  | 'Aguardando Agendamento'
  | 'Com Profissional'
  | 'Escalonado'
  | 'Finalizado';

type Quadro = Record<ColunaNome, KanbanCardProps[]>;

const DashboardKanban: React.FC = () => {
  const [quadro, setQuadro] = useState<Quadro>({
    Novos: [],
    'IA Respondendo': [],
    'Triagem Emocional': [],
    'Aguardando Agendamento': [],
    'Com Profissional': [],
    Escalonado: [],
    Finalizado: [],
  });
  const [latencia, setLatencia] = useState(0);

  const carregarQuadro = useCallback(async () => {
    const ini = performance.now();
    const dados = await obterQuadroKanban();
    setLatencia(Math.round(performance.now() - ini));
    setQuadro(dados.colunas as Quadro);
  }, []);

  useEffect(() => {
    carregarQuadro();
    const id = setInterval(carregarQuadro, 30_000);
    return () => clearInterval(id);
  }, [carregarQuadro]);

  /* ---------- DnD ---------- */
  const sensors = useSensors(useSensor(PointerSensor));

  const handleDragEnd = async (event: DragEndEvent) => {
    const { active, over } = event;
    if (!over || active.id === over.id) return;

    const origem = active.data.current?.coluna as ColunaNome;
    const destino = over.data.current?.coluna as ColunaNome;
    if (!origem || !destino || origem === destino) return;

    const card = quadro[origem].find((c) => c.id === active.id);
    if (!card) return;

    await moverConversa(String(card.id), destino);

    setQuadro((prev) => {
      const sem = prev[origem].filter((c) => c.id !== active.id);
      return {
        ...prev,
        [origem]: sem,
        [destino]: [card, ...prev[destino]],
      };
    });
  };

  const colunas: ColunaNome[] = useMemo(
    () => [
      'Novos',
      'IA Respondendo',
      'Triagem Emocional',
      'Aguardando Agendamento',
      'Com Profissional',
      'Escalonado',
      'Finalizado',
    ],
    [],
  );

  return (
    <div className="p-4 bg-slate-100 min-h-screen overflow-x-auto">
      <h1 className="text-2xl font-semibold mb-4">Painel de Conversas</h1>

      <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={handleDragEnd}>
        <div className="flex gap-4">
          {colunas.map((col) => (
            <SortableContext
              key={col}
              items={quadro[col].map((c) => c.id)}
              strategy={verticalListSortingStrategy}
            >
              <KanbanColumn nome={col} cards={quadro[col]} className="w-72" />
            </SortableContext>
          ))}
        </div>
      </DndContext>

      <div className="mt-6 text-xs text-slate-500">
        Latência API: {latencia} ms • Atualizado {dayjs().format('HH:mm:ss')}
      </div>
    </div>
  );
};

export default DashboardKanban;
