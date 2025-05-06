/* Estrutura simples: topo + conteúdo central */
import React, { type ReactNode } from 'react';
import { Link, Outlet } from 'react-router-dom';
import { KanbanSquare, MessagesSquare, BarChart2 } from 'lucide-react';

interface Props { children?: ReactNode }

const DomoShell: React.FC<Props> = ({ children }) => (
  <div className="min-h-screen flex flex-col">
    {/* topo */}
    <header className="h-12 flex items-center px-4 bg-slate-800 text-slate-100">
      <h1 className="text-lg font-semibold mr-6">Domo Hub</h1>
      <nav className="flex gap-4 text-sm">
        <Link className="flex items-center gap-1 hover:text-emerald-300" to="/kanban">
          <KanbanSquare size={16} /> Kanban
        </Link>
        <Link className="flex items-center gap-1 hover:text-emerald-300" to="/conversas">
          <MessagesSquare size={16} /> Conversas
        </Link>
        <Link className="flex items-center gap-1 hover:text-emerald-300" to="/analytics">
          <BarChart2 size={16} /> Analytics
        </Link>
      </nav>
    </header>

    {/* conteúdo */}
    <main className="flex-1 bg-slate-100 p-4 overflow-auto">
      {children ?? <Outlet />}
    </main>
  </div>
);

export default DomoShell;
