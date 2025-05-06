// File: src/components/ChatMessage.tsx
// Componente para exibir uma única mensagem na tela de chat.
// CORREÇÃO: Substituído classes 'slate' por 'neutral'

import React from 'react';
import type { MessageData } from '../types';
import { format } from 'date-fns';
import { ptBR } from 'date-fns/locale';
import { Bot, User, UserCog } from 'lucide-react';

interface ChatMessageProps {
  message: MessageData;
}

const ChatMessage: React.FC<ChatMessageProps> = ({ message }) => {
  const isUser = message.sender === 'user';
  const isBot = message.sender === 'bot';

  const formattedTime = message.timestamp
    ? format(new Date(message.timestamp), 'dd/MM HH:mm', { locale: ptBR })
    : '';

  // CORREÇÃO: Trocado bg-slate-200, text-slate-800
  const bubbleClasses = isUser
    ? 'bg-blue-600 text-white rounded-tr-none shadow-md'
    : isBot
    ? 'bg-neutral-200 text-neutral-800 rounded-tl-none shadow-sm' // Bot: Cinza neutro
    : 'bg-green-100 text-green-900 border border-green-200 rounded-tl-none shadow-sm'; // Humano: Verde

  const alignmentClasses = isUser ? 'items-end' : 'items-start';
  const senderName = isUser ? 'Você' : isBot ? 'Domo' : 'Atendente';

  // CORREÇÃO: Trocado text-slate-500
  const SenderIcon = isUser ? User : isBot ? Bot : UserCog;
  const iconColor = isUser ? 'text-blue-400' : isBot ? 'text-neutral-500' : 'text-green-600';

  return (
    <div className={`flex flex-col w-full my-2 ${alignmentClasses}`}>
      {/* CORREÇÃO: Trocado text-slate-600, text-slate-400 */}
      <div className={`flex items-center mb-1 text-xs ${isUser ? 'flex-row-reverse' : 'flex-row'}`}>
        <SenderIcon size={14} className={`mx-1.5 ${iconColor} flex-shrink-0`} />
        <span className="font-medium text-neutral-600">{senderName}</span>
        <span className="text-neutral-400 mx-1.5">•</span>
        <span className="text-neutral-400">{formattedTime}</span>
      </div>

      <div
        className={`max-w-[75%] md:max-w-[65%] px-3 py-2 rounded-lg ${bubbleClasses}`}
      >
        <p className="text-sm whitespace-pre-wrap break-words">{message.text}</p>

        {isUser && (message.intent || message.sentimento) && (
          <div className="mt-1 pt-1 border-t border-white/20 text-xs opacity-80 italic flex flex-wrap gap-x-2">
            {message.intent && <span>Intent: {message.intent}</span>}
            {message.sentimento && (
              <span>
                Sent: {Object.entries(message.sentimento)
                  .sort(([, a], [, b]) => b - a)
                  .map(([key, value]) => `${key.substring(0, 3)}: ${Math.round(value * 100)}%`)
                  .join(', ')}
              </span>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default ChatMessage;
