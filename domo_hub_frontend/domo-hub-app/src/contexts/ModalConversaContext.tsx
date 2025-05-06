/* ---------------------------------------------------------------------------
Contexto global para abrir/fechar <ConversaModal />
--------------------------------------------------------------------------- */

import React, { createContext, useState, useContext, ReactNode } from 'react';
import ConversaModal from '@/components/ConversaModal';

interface ModalCtx {
  abrir: (telefone: string) => void;
}

const Ctx = createContext<ModalCtx | null>(null);

export const useConversaModal = (): ModalCtx => {
  const ctx = useContext(Ctx);
  if (!ctx) throw new Error('ConversaModalProvider ausente');
  return ctx;
};

export const ConversaModalProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [telefoneAtivo, setTelefoneAtivo] = useState<string | null>(null);

  const abrir = (tel: string) => setTelefoneAtivo(tel);
  const fechar = () => setTelefoneAtivo(null);

  return (
    <Ctx.Provider value={{ abrir }}>
      {children}
      <ConversaModal telefone={telefoneAtivo} aberto={!!telefoneAtivo} onClose={fechar} />
    </Ctx.Provider>
  );
};
