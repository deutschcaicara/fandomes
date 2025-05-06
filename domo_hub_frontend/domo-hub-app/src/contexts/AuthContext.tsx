// ===========================================================
// Arquivo: src/contexts/AuthContext.tsx
// Gerencia o estado de autenticação (token, usuário) na aplicação.
// CORRIGIDO: Importações de tipo.
// ===========================================================
import React, { createContext, useState, useContext, useEffect } from 'react';
import type { ReactNode } from 'react'; // Usa 'import type'
import { login as apiLogin, getCurrentUser } from '../services/api';
import type { User } from '../types'; // Usa 'import type'

interface AuthContextType {
  token: string | null;
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [token, setToken] = useState<string | null>(() => localStorage.getItem('authToken')); // Lê inicial do localStorage
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  useEffect(() => {
    const verifyToken = async () => {
      const storedToken = localStorage.getItem('authToken'); // Pega o token atual
      if (storedToken) {
        console.log("AuthContext: Token encontrado no localStorage, verificando...");
        setToken(storedToken); // Garante que o estado local tenha o token
        try {
          const currentUser = await getCurrentUser();
          setUser(currentUser);
          console.log("AuthContext: Token válido, usuário:", currentUser.username);
        } catch (error: any) {
          console.error("AuthContext: Falha ao verificar token (provavelmente expirado ou inválido):", error.response?.data || error.message);
          localStorage.removeItem('authToken');
          setToken(null);
          setUser(null);
        }
      } else {
         console.log("AuthContext: Nenhum token no localStorage.");
      }
      setIsLoading(false);
    };
    verifyToken();
  }, []); // Roda apenas uma vez na montagem inicial

  const login = async (username: string, password: string) => {
    try {
      setIsLoading(true);
      const data = await apiLogin(username, password);
      localStorage.setItem('authToken', data.access_token);
      setToken(data.access_token); // Atualiza o token no estado
      // Busca dados do usuário IMEDIATAMENTE após setar o token
      const currentUser = await getCurrentUser();
      setUser(currentUser);
      console.log("AuthContext: Login bem-sucedido, usuário:", currentUser.username);
      setIsLoading(false);
    } catch (error) {
      setIsLoading(false);
      console.error("AuthContext: Erro no login:", error);
      // Limpa qualquer token antigo em caso de falha
      localStorage.removeItem('authToken');
      setToken(null);
      setUser(null);
      throw error; // Re-lança o erro
    }
  };

  const logout = () => {
    console.log("AuthContext: Executando logout...");
    localStorage.removeItem('authToken');
    setToken(null);
    setUser(null);
    // Opcional: redirecionar para /login aqui se necessário,
    // mas o ProtectedRoute fará isso automaticamente.
  };

  // Recalcula isAuthenticated sempre que token ou user mudar
  const isAuthenticated = !!token && !!user;

  // Não renderiza children até que a verificação inicial esteja completa
  // if (isLoading) {
  //   return <div>Verificando autenticação...</div>; // Ou um spinner global
  // }

  return (
    <AuthContext.Provider value={{ token, user, isAuthenticated, isLoading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth deve ser usado dentro de um AuthProvider');
  }
  return context;
};
