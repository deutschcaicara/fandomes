// File: src/pages/DashboardLayout.tsx
// Define o layout principal do dashboard com sidebar e área de conteúdo.
// CORREÇÃO FINAL: Todas as classes 'slate-*' substituídas por 'neutral-*'

import React from 'react';
import { Outlet, Link, useLocation } from 'react-router-dom';
// import { useAuth } from '../contexts/AuthContext'; // Descomentar quando usar login
import { LayoutDashboard, MessageSquare, BarChart3, LogOut } from 'lucide-react'; // Ícones

const DashboardLayout: React.FC = () => {
  // const { user, logout } = useAuth(); // Descomentar quando usar login
  const location = useLocation(); // Hook para obter a localização atual

  const isActive = (path: string): boolean => {
    if (path === '/kanban') {
      return location.pathname === '/' || location.pathname === '/kanban';
    }
    return location.pathname.startsWith(path) && path !== '/';
  };

  const handleLogout = () => {
    console.log("Logout clicado - implementar lógica real com AuthContext");
    // logout(); // Chamar logout do AuthContext quando reimplementado
  };

  return (
    // Container Flex principal
    <div className="flex h-screen bg-neutral-100 font-sans"> {/* CORREÇÃO */}

      {/* Barra Lateral (Sidebar) */}
      <aside className="w-60 flex flex-col bg-gradient-to-b from-neutral-800 to-neutral-900 text-neutral-100 shadow-lg flex-shrink-0"> {/* CORREÇÃO */}
        {/* Cabeçalho da Sidebar */}
        <div className="px-5 py-5 border-b border-neutral-700"> {/* CORREÇÃO */}
          <h1 className="text-2xl font-bold text-white tracking-tight">Domo Hub</h1>
          {/* <span className="text-xs text-neutral-400 block mt-1">Usuário: {user?.username || 'Admin'}</span> */} {/* CORREÇÃO */}
        </div>

        {/* Navegação Principal */}
        <nav className="flex-1 mt-6 px-3 space-y-1.5">
          {/* Link para Kanban */}
          <Link
            to="/kanban"
            className={`flex items-center px-3 py-2.5 rounded-md text-sm font-medium transition-colors duration-150 group ${
              isActive('/kanban')
                ? 'bg-neutral-700 text-white shadow-inner' // CORREÇÃO
                : 'text-neutral-300 hover:bg-neutral-700 hover:text-white' // CORREÇÃO
            }`}
          >
            <LayoutDashboard className={`mr-3 h-5 w-5 flex-shrink-0 ${isActive('/kanban') ? 'text-white' : 'text-neutral-400 group-hover:text-neutral-300'}`} /> {/* CORREÇÃO */}
            <span>Kanban</span>
          </Link>

          {/* Link para Conversas */}
          <Link
            to="/chat"
            className={`flex items-center px-3 py-2.5 rounded-md text-sm font-medium transition-colors duration-150 group ${
              isActive('/chat')
                ? 'bg-neutral-700 text-white shadow-inner' // CORREÇÃO
                : 'text-neutral-300 hover:bg-neutral-700 hover:text-white' // CORREÇÃO
            }`}
          >
            <MessageSquare className={`mr-3 h-5 w-5 flex-shrink-0 ${isActive('/chat') ? 'text-white' : 'text-neutral-400 group-hover:text-neutral-300'}`} /> {/* CORREÇÃO */}
            <span>Conversas</span>
          </Link>

          {/* Link para Analytics */}
          <Link
            to="/analytics"
            className={`flex items-center px-3 py-2.5 rounded-md text-sm font-medium transition-colors duration-150 group ${
              isActive('/analytics')
                ? 'bg-neutral-700 text-white shadow-inner' // CORREÇÃO
                : 'text-neutral-300 hover:bg-neutral-700 hover:text-white' // CORREÇÃO
            }`}
          >
            <BarChart3 className={`mr-3 h-5 w-5 flex-shrink-0 ${isActive('/analytics') ? 'text-white' : 'text-neutral-400 group-hover:text-neutral-300'}`} /> {/* CORREÇÃO */}
            <span>Analytics</span>
          </Link>
        </nav>

        {/* Rodapé da Sidebar com Botão Sair */}
        <div className="px-3 py-4 mt-auto border-t border-neutral-700"> {/* CORREÇÃO */}
          <button
            onClick={handleLogout}
            className="w-full flex items-center justify-center px-3 py-2 rounded-md text-sm font-medium bg-red-600 hover:bg-red-700 text-white transition-colors duration-150 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2 focus:ring-offset-neutral-800" // CORREÇÃO
          >
            <LogOut className="mr-2 h-5 w-5" />
            Sair
          </button>
        </div>
      </aside>

      {/* Conteúdo Principal */}
      <main className="flex-1 flex flex-col overflow-hidden">
         {/* Área de Conteúdo Rolável */}
         <div className="flex-1 overflow-x-hidden overflow-y-auto bg-neutral-50 p-4 md:p-6 lg:p-8"> {/* CORREÇÃO */}
           <Outlet />
         </div>
      </main>
    </div>
  );
};

export default DashboardLayout;
