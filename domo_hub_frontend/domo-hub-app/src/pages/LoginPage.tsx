// ===========================================================
// Arquivo: src/pages/LoginPage.tsx
// Página de login simples.
// CORREÇÃO: Substituído classes 'slate' por 'neutral'
// ===========================================================
import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { Navigate } from 'react-router-dom';

const LoginPage: React.FC = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isLoggingIn, setIsLoggingIn] = useState(false);
  const { login, isAuthenticated, isLoading } = useAuth();

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setError(null);
    setIsLoggingIn(true);
    try {
      await login(username, password);
    } catch (err) {
      setError('Falha no login. Verifique usuário e senha.');
      console.error(err);
    } finally {
       setIsLoggingIn(false);
    }
  };

  if (!isLoading && isAuthenticated) {
    return <Navigate to="/" replace />;
  }

  if (isLoading && !isAuthenticated && !isLoggingIn) {
      return (
          // CORREÇÃO: Trocado bg-slate-100, text-slate-700
          <div className="flex items-center justify-center min-h-screen bg-neutral-100">
              <div className="text-center">
                  <p className="text-xl font-semibold text-neutral-700">Verificando autenticação...</p>
              </div>
          </div>
      );
  }

  return (
    <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-brand-accent to-blue-100">
      <div className="w-full max-w-md p-8 space-y-6 bg-white rounded-lg shadow-xl">
        {/* CORREÇÃO: Trocado text-slate-800 */}
        <h2 className="text-3xl font-bold text-center text-neutral-800">
          Domo Hub Login
        </h2>
        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            {/* CORREÇÃO: Trocado text-slate-700 */}
            <label
              htmlFor="username"
              className="block text-sm font-medium text-neutral-700"
            >
              Usuário
            </label>
            {/* CORREÇÃO: Trocado text-slate-900, placeholder-slate-500, border-slate-300 */}
            <input
              id="username"
              name="username"
              type="text"
              autoComplete="username"
              required
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="block w-full px-3 py-2 mt-1 text-neutral-900 placeholder-neutral-500 border border-neutral-300 rounded-md shadow-sm appearance-none focus:outline-none focus:ring-brand-secondary focus:border-brand-secondary sm:text-sm"
              placeholder="admin"
            />
          </div>
          <div>
            {/* CORREÇÃO: Trocado text-slate-700 */}
            <label
              htmlFor="password"
              className="block text-sm font-medium text-neutral-700"
            >
              Senha
            </label>
            {/* CORREÇÃO: Trocado text-slate-900, placeholder-slate-500, border-slate-300 */}
            <input
              id="password"
              name="password"
              type="password"
              autoComplete="current-password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="block w-full px-3 py-2 mt-1 text-neutral-900 placeholder-neutral-500 border border-neutral-300 rounded-md shadow-sm appearance-none focus:outline-none focus:ring-brand-secondary focus:border-brand-secondary sm:text-sm"
              placeholder="password"
            />
          </div>

          {error && (
            <p className="text-sm text-center text-red-600">{error}</p>
          )}

          <div>
            <button
              type="submit"
              disabled={isLoggingIn || (isLoading && !isAuthenticated)}
              className="relative flex justify-center w-full px-4 py-2 text-sm font-medium text-white bg-brand-secondary border border-transparent rounded-md group hover:bg-brand-primary focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-brand-primary disabled:opacity-50 disabled:cursor-not-allowed"
            >
               {isLoggingIn ? 'Entrando...' : 'Entrar'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default LoginPage;
