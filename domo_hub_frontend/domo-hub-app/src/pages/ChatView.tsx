// File: src/pages/ChatView.tsx
// Exibe a lista de conversas ou o detalhe de uma conversa específica.
// CORREÇÃO: Substituído classes 'slate' por 'neutral'

import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useParams, Link } from 'react-router-dom';
import { getConversationDetail, sendHumanMessage, simulateUserMessage, updateConversationState } from '../services/api';
import type { ConversationDetailData, MessageData } from '../types';
import ChatMessage from '../components/ChatMessage';
import {
  Loader2,
  Send,
  Bot,
  AlertTriangle,
  ArrowLeft,
  Info,
  MessageSquare,
  ChevronDown,
  CheckCircle,
  XCircle,
} from 'lucide-react';

const ChatView: React.FC = () => {
  const { telefone } = useParams<{ telefone?: string }>();
  const [conversation, setConversation] = useState<ConversationDetailData | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [humanMessage, setHumanMessage] = useState('');
  const [simulateMessage, setSimulateMessage] = useState('');
  const [isSendingHuman, setIsSendingHuman] = useState(false);
  const [isSimulating, setIsSimulating] = useState(false);
  const [showContext, setShowContext] = useState(false);
  const [sendSuccess, setSendSuccess] = useState<string | null>(null);
  const [sendError, setSendError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const fetchConversation = useCallback(async (tel: string) => {
    setIsLoading(true);
    setError(null);
    setConversation(null);
    console.log(`Buscando conversa para: ${tel}`);
    try {
      const data = await getConversationDetail(tel);
      setConversation(data);
    } catch (err: any) {
      console.error(`Erro ao buscar conversa ${tel}:`, err);
      setError(
        err.response?.status === 404
          ? `Conversa com telefone ${tel} não encontrada.`
          : "Falha ao carregar a conversa. Verifique a conexão com a API."
      );
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    if (telefone) {
      fetchConversation(telefone);
    } else {
      setConversation(null);
      setIsLoading(false);
      setError(null);
    }
  }, [telefone, fetchConversation]);

  useEffect(() => {
    const timer = setTimeout(() => {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' });
    }, 150);
    return () => clearTimeout(timer);
  }, [conversation?.historico]);

  useEffect(() => {
    let timer: ReturnType<typeof setTimeout> | undefined;
    if (sendSuccess || sendError) {
      timer = setTimeout(() => {
        setSendSuccess(null);
        setSendError(null);
      }, 4000);
    }
    return () => clearTimeout(timer);
  }, [sendSuccess, sendError]);

  const handleSendHumanMessage = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!humanMessage.trim() || !telefone || isSendingHuman) return;

    setIsSendingHuman(true);
    setSendError(null);
    setSendSuccess(null);
    const messageText = humanMessage;
    setHumanMessage('');

    try {
      await sendHumanMessage(telefone, messageText);
      const newMessage: MessageData = {
        id: `human_${Date.now()}`,
        timestamp: new Date().toISOString(),
        sender: 'human',
        text: messageText,
      };
      setConversation(prev => prev ? ({ ...prev, historico: [...prev.historico, newMessage] }) : null);
      setSendSuccess("Mensagem enviada!");
    } catch (err: any) {
      console.error("Erro ao enviar mensagem humana:", err);
      const errorMsg = err.response?.data?.detail || err.message || "Falha ao enviar.";
      setSendError(`Erro: ${errorMsg}`);
      setHumanMessage(messageText);
    } finally {
      setIsSendingHuman(false);
    }
  };

   const handleSimulateUserMessage = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!simulateMessage.trim() || !telefone || isSimulating) return;

    setIsSimulating(true);
    setSendError(null);
    setSendSuccess(null);
    const messageText = simulateMessage;
    setSimulateMessage('');

    try {
      const result = await simulateUserMessage(telefone, messageText);
      console.log("Resultado da simulação:", result);
      setSendSuccess("Simulação enviada. Atualizando...");
      await fetchConversation(telefone);
    } catch (err: any) {
      console.error("Erro ao simular mensagem:", err);
      const errorMsg = err.response?.data?.detail || err.message || "Falha ao simular.";
      setSendError(`Erro simulação: ${errorMsg}`);
      setSimulateMessage(messageText);
    } finally {
      setIsSimulating(false);
    }
  };

  const handleStateChange = async (event: React.ChangeEvent<HTMLSelectElement>) => {
      const novoEstado = event.target.value;
      if (!telefone || !novoEstado || novoEstado === conversation?.estado) return;

      const originalState = conversation?.estado;
      setConversation(prev => prev ? ({...prev, estado: novoEstado}) : null);
      setSendError(null);
      setSendSuccess(null);

      try {
          await updateConversationState(telefone, novoEstado);
          setSendSuccess(`Estado atualizado para ${novoEstado}.`);
      } catch (err: any) {
          console.error("Erro ao atualizar estado:", err);
          const errorMsg = err.response?.data?.detail || err.message || "Falha ao atualizar.";
          setSendError(`Erro estado: ${errorMsg}`);
          setConversation(prev => prev ? ({...prev, estado: originalState ?? prev.estado}) : null);
      }
  }

  if (!telefone) {
    return (
      // CORREÇÃO: Trocado text-slate-500, text-slate-300, text-slate-700
      <div className="flex flex-col items-center justify-center h-full text-neutral-500 p-10 text-center bg-white rounded-lg shadow">
        <MessageSquare size={60} className="mb-5 text-neutral-300" />
        <h3 className="text-xl font-semibold mb-2 text-neutral-700">Selecione uma Conversa</h3>
        <p className="max-w-md">Para visualizar os detalhes e interagir, clique em um card no quadro Kanban.</p>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
        {/* CORREÇÃO: Trocado text-slate-600 */}
        <span className="ml-3 text-neutral-600">Carregando conversa...</span>
      </div>
    );
  }

  if (error && !conversation) {
    return (
      // CORREÇÃO: Trocado text-slate-500, hover:text-slate-700, border-slate-300
      <div className="flex flex-col items-center justify-center h-full text-red-600 p-6 bg-red-50 rounded-lg border border-red-200 relative">
         <Link to="/kanban" className="absolute top-4 left-4 text-neutral-500 hover:text-neutral-700 flex items-center text-sm bg-white px-2 py-1 rounded border border-neutral-300 shadow-sm">
             <ArrowLeft size={16} className="mr-1"/> Kanban
         </Link>
        <AlertTriangle className="h-10 w-10 mb-3 text-red-500" />
        <p className="text-center font-medium mb-4">{error}</p>
        <button
            onClick={() => fetchConversation(telefone)}
            className="mt-2 px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2"
        >
            Tentar Novamente
        </button>
      </div>
    );
  }

  if (!conversation) {
    return (
         // CORREÇÃO: Trocado text-slate-500, bg-slate-50, text-slate-500, hover:text-slate-700, border-slate-300
         <div className="flex flex-col items-center justify-center h-full text-neutral-500 p-6 bg-neutral-50 rounded-lg border relative">
             <Link to="/kanban" className="absolute top-4 left-4 text-neutral-500 hover:text-neutral-700 flex items-center text-sm bg-white px-2 py-1 rounded border border-neutral-300 shadow-sm">
                 <ArrowLeft size={16} className="mr-1"/> Kanban
             </Link>
             <p>Não foi possível carregar os dados desta conversa.</p>
        </div>
    );
  }

  return (
    <div className="flex h-full max-h-[calc(100vh-4rem)]">
      <div className="flex flex-col flex-1 h-full bg-white rounded-lg shadow-lg overflow-hidden border border-slate-200">
        {/* CORREÇÃO: Trocado bg-slate-50, border-slate-200, text-slate-500, hover:text-slate-700, text-slate-800, hover:bg-slate-200, text-slate-500, hover:text-slate-800, hover:bg-slate-100 */}
        <header className="bg-neutral-50 p-3 border-b border-neutral-200 flex items-center justify-between flex-shrink-0 sticky top-0 z-10">
           <div className='flex items-center min-w-0'>
               <Link to="/kanban" className="text-neutral-500 hover:text-neutral-700 mr-3 p-1 rounded-full hover:bg-neutral-200" title="Voltar ao Kanban">
                   <ArrowLeft size={20} />
               </Link>
               <h2 className="text-lg font-semibold text-neutral-800 truncate mr-3" title={conversation.tel}>
                 {conversation.nome || conversation.tel}
               </h2>
               <div className="relative inline-block text-left">
                  <select
                      value={conversation.estado}
                      onChange={handleStateChange}
                      title={`Estado atual: ${conversation.estado}. Clique para alterar.`}
                      className="appearance-none text-xs font-semibold bg-blue-100 text-blue-800 px-3 py-1 rounded-full border border-blue-200 focus:outline-none focus:ring-2 focus:ring-blue-400 focus:ring-offset-1 cursor-pointer pr-6"
                  >
                      <option value={conversation.estado} disabled>{conversation.estado}</option>
                      <option value="entrada">Entrada</option>
                      <option value="qualificacao">Qualificação</option>
                      <option value="proposta">Proposta</option>
                      <option value="pagamento_pendente">Pagamento Pendente</option>
                      <option value="triagem">Triagem Pós-Pgto</option>
                      <option value="agendado">Agendado</option>
                      <option value="atendimento_humano">Atendimento Humano</option>
                      <option value="followup">Follow-up</option>
                      <option value="concluido">Concluído/Perdido</option>
                  </select>
                  <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-1.5 text-blue-700">
                      <ChevronDown size={14} />
                  </div>
              </div>
           </div>
           <button
              onClick={() => setShowContext(!showContext)}
              className={`p-1.5 rounded-full transition-colors ${showContext ? 'bg-blue-100 text-blue-700' : 'text-neutral-500 hover:text-neutral-800 hover:bg-neutral-100'}`}
              title={showContext ? "Ocultar Contexto" : "Mostrar Contexto"}
            >
              <Info size={18} />
            </button>
        </header>

        {/* CORREÇÃO: Trocado from-slate-50, to-slate-100, scrollbar-thumb-slate-300, scrollbar-track-neutral-100, text-slate-400 */}
        <div className="flex-1 overflow-y-auto p-4 space-y-3 bg-gradient-to-b from-neutral-50 to-neutral-100 scrollbar-thin scrollbar-thumb-neutral-300 scrollbar-track-neutral-100">
          {conversation.historico.length === 0 && (
            <p className="text-center text-neutral-400 text-sm mt-10 px-4">Nenhuma mensagem para exibir.</p>
          )}
          {conversation.historico.map((msg) => (
            <ChatMessage key={msg.id} message={msg} />
          ))}
          <div ref={messagesEndRef} />
        </div>

        {/* CORREÇÃO: Trocado border-slate-200, border-slate-300 */}
        <footer className="p-3 border-t border-neutral-200 bg-white flex-shrink-0 space-y-2">
          <form onSubmit={handleSendHumanMessage} className="flex items-center">
            <input
              type="text"
              value={humanMessage}
              onChange={(e) => setHumanMessage(e.target.value)}
              placeholder="Mensagem do atendente..."
              disabled={isSendingHuman}
              className="flex-1 px-3 py-2 border border-neutral-300 rounded-l-md focus:outline-none focus:ring-1 focus:ring-green-500 focus:border-green-500 text-sm transition-colors"
            />
            <button
              type="submit"
              disabled={isSendingHuman || !humanMessage.trim()}
              className="px-4 py-2 bg-green-600 text-white rounded-r-md hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-1 focus:ring-green-500 disabled:opacity-60 disabled:cursor-not-allowed transition-opacity duration-150 flex items-center justify-center h-[40px] w-[50px]"
              title="Enviar como Atendente"
            >
              {isSendingHuman ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send size={16} />}
            </button>
          </form>

          <form onSubmit={handleSimulateUserMessage} className="flex items-center">
            <input
              type="text"
              value={simulateMessage}
              onChange={(e) => setSimulateMessage(e.target.value)}
              placeholder="Simular mensagem do usuário..."
              disabled={isSimulating}
              className="flex-1 px-3 py-2 border border-neutral-300 rounded-l-md focus:outline-none focus:ring-1 focus:ring-orange-500 focus:border-orange-500 text-sm transition-colors"
            />
            <button
              type="submit"
              disabled={isSimulating || !simulateMessage.trim()}
              className="px-3 py-2 bg-orange-500 text-white rounded-r-md hover:bg-orange-600 focus:outline-none focus:ring-2 focus:ring-offset-1 focus:ring-orange-400 disabled:opacity-60 disabled:cursor-not-allowed flex items-center h-[40px]"
              title="Enviar esta mensagem como se fosse o usuário (para testar o bot)"
            >
              <Bot size={16} />
              <span className="ml-1 text-xs hidden sm:inline">Simular</span>
            </button>
          </form>

           <div className="h-4 mt-1 text-center">
             {sendSuccess && (
               <p className="text-xs text-green-600 flex items-center justify-center animate-pulse">
                 <CheckCircle size={12} className="mr-1" /> {sendSuccess}
               </p>
             )}
             {sendError && (
               <p className="text-xs text-red-600 flex items-center justify-center">
                 <XCircle size={12} className="mr-1" /> {sendError}
               </p>
             )}
           </div>
        </footer>
      </div>

      {/* CORREÇÃO: Trocado border-slate-200, bg-slate-50, text-slate-700, text-slate-400, hover:text-slate-600, hover:bg-slate-200, border-slate-200, scrollbar-thumb-slate-300, scrollbar-track-neutral-100 */}
      <aside className={`transition-all duration-300 ease-in-out overflow-hidden ${showContext ? 'w-80 lg:w-96 border-l' : 'w-0 border-l-0'} border-neutral-200 flex-shrink-0`}>
        {showContext && (
          <div className="p-4 h-full overflow-y-auto bg-neutral-50">
            <div className="flex justify-between items-center mb-3">
              <h3 className="text-base font-semibold text-neutral-700">Contexto da Conversa</h3>
              <button onClick={() => setShowContext(false)} className="text-neutral-400 hover:text-neutral-600 p-1 rounded-full hover:bg-neutral-200" title="Fechar Contexto">
                ✕
              </button>
            </div>
            <div className="text-xs bg-white p-3 rounded border border-neutral-200 shadow-sm">
              <pre className="whitespace-pre-wrap break-all scrollbar-thin scrollbar-thumb-neutral-300 scrollbar-track-neutral-100 max-h-[calc(100vh-10rem)]">
                {JSON.stringify(conversation.contexto, null, 2)}
              </pre>
            </div>
          </div>
        )}
      </aside>

    </div>
  );
};

export default ChatView;
