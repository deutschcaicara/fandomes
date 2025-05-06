// File: src/components/ProtectedRoute.tsx
// Componente para proteger rotas que exigem autenticação.
// CORREÇÃO: Substituído bg-slate-100, text-slate-700

import React from 'react';
import { Navigate, Outlet } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext'; // Descomentar quando usar login real

const ProtectedRoute: React.FC = () => {
  // --- Lógica de Autenticação (Descomentar quando reimplementar) ---
  const { isAuthenticated, isLoading } = useAuth();

  // Mostra um estado de carregamento enquanto verifica o token inicial
  if (isLoading) {
    return (
        // CORREÇÃO: Trocado bg-slate-100, text-slate-700
        <div className="flex items-center justify-center h-screen bg-neutral-100">
            <div className="text-xl font-semibold text-neutral-700">Verificando autenticação...</div>
            {/* Adicionar um spinner/loading visual aqui seria ideal */}
        </div>
    );
  }

  // Redireciona para a página de login se não estiver autenticado
  if (!isAuthenticated) {
    console.log("ProtectedRoute: Não autenticado, redirecionando para /login");
    // O parâmetro 'replace' evita que a rota protegida entre no histórico do navegador
    return <Navigate to="/login" replace />;
  }
  // --------------------------------------------------------------

  // Renderiza o conteúdo da rota filha (Outlet) se autenticado
  console.log("ProtectedRoute: Autenticado, renderizando Outlet");
  return <Outlet />;
};

export default ProtectedRoute;
