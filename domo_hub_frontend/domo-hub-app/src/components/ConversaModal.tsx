/* ---------------------------------------------------------------------------
Arquivo: src/components/ConversaModal.tsx
Modal lateral para exibir conversa completa e responder manualmente
--------------------------------------------------------------------------- */

import React, { Fragment, useEffect, useState } from 'react';
import { Dialog, Transition } from '@headlessui/react';
import dayjs from 'dayjs';
import {
  obterConversaCompleta,
  responderHumano,
  obterSugestaoIA,
} from '@/services/api';

interface Mensagem {
  criado_em: string;
  remetente: string;
  texto: string;
  intent?: string;
  fallback?: boolean;
}

interface ConversaModalProps {
  telefone: string | null;
  aberto: boolean;
  onClose: () => void;
}

const ConversaModal: React.FC<ConversaModalProps> = ({
  telefone,
  aberto,
  onClose,
}) => {
  const [mensagens, setMensagens] = useState<Mensagem[]>([]);
  const [loading, setLoading] = useState(false);
  const [mensagemResp, setMensagemResp] = useState('');
  const [sugestao, setSugestao] = useState<string | null>(null);

  useEffect(() => {
    if (!telefone) return;
    setLoading(true);
    obterConversaCompleta(telefone)
      .then((msgs: unknown) => setMensagens(msgs as Mensagem[]))
      .finally(() => setLoading(false));
  }, [telefone]);

  const enviarResposta = async () => {
    if (!telefone || !mensagemResp.trim()) return;
    await responderHumano(telefone, mensagemResp.trim(), 'Profissional');
    setMensagemResp('');
    onClose();
  };

  const pedirSugestao = async () => {
    if (!telefone) return;
    const txt = await obterSugestaoIA(telefone);
    setSugestao(txt);
  };

  return (
    <Transition show={aberto} as={Fragment}>
      <Dialog as="div" className="relative z-20" onClose={onClose}>
        {/* backdrop */}
        <Transition.Child
          as={Fragment}
          enter="ease-out duration-300"
          enterFrom="opacity-0"
          enterTo="opacity-100"
          leave="ease-in duration-200"
          leaveFrom="opacity-100"
          leaveTo="opacity-0"
        >
          <div className="fixed inset-0 bg-black/30 backdrop-blur-sm" />
        </Transition.Child>

        {/* painel */}
        <div className="fixed inset-0 flex justify-end">
          <Transition.Child
            as={Fragment}
            enter="transform transition ease-out duration-300"
            enterFrom="translate-x-full"
            enterTo="translate-x-0"
            leave="transform transition ease-in duration-200"
            leaveFrom="translate-x-0"
            leaveTo="translate-x-full"
          >
            <Dialog.Panel className="w-full max-w-lg bg-white shadow-xl p-6 flex flex-col">
              <Dialog.Title className="text-lg font-semibold mb-4">
                Conversa – {telefone ?? ''}
              </Dialog.Title>

              {/* mensagens */}
              <div className="flex-1 overflow-y-auto space-y-3 pr-1">
                {loading && <div>Carregando...</div>}
                {mensagens.map((m, idx) => (
                  <div
                    key={idx}
                    className={`rounded p-2 text-sm ${
                      m.remetente === 'paciente'
                        ? 'bg-slate-100'
                        : m.remetente.startsWith('[HUMANO')
                        ? 'bg-sky-100'
                        : m.fallback
                        ? 'bg-amber-100'
                        : 'bg-green-100'
                    }`}
                  >
                    <div className="text-xs text-slate-500 mb-1">
                      {m.remetente} • {dayjs(m.criado_em).format('DD/MM HH:mm')}
                      {m.fallback && ' • fallback'}
                    </div>
                    <div className="whitespace-pre-wrap">{m.texto}</div>
                  </div>
                ))}
              </div>

              {/* resposta manual */}
              <textarea
                className="border w-full p-2 mt-4 rounded h-24 resize-none"
                placeholder="Responder como humano..."
                value={mensagemResp}
                onChange={(e) => setMensagemResp(e.target.value)}
              />

              {sugestao && (
                <div className="mt-2 p-2 text-xs bg-emerald-50 rounded border border-emerald-200">
                  <strong>Sugestão IA:</strong> {sugestao}
                </div>
              )}

              <div className="flex gap-2 mt-3">
                <button
                  className="flex-1 bg-slate-200 hover:bg-slate-300 rounded p-2 text-sm"
                  onClick={pedirSugestao}
                >
                  pedir sugestão IA
                </button>
                <button
                  className="flex-1 bg-emerald-600 hover:bg-emerald-700 text-white rounded p-2 text-sm"
                  onClick={enviarResposta}
                >
                  enviar resposta
                </button>
              </div>

              <button
                className="absolute top-2 right-3 text-slate-500 hover:text-slate-700"
                onClick={onClose}
              >
                ✕
              </button>
            </Dialog.Panel>
          </Transition.Child>
        </div>
      </Dialog>
    </Transition>
  );
};

export default ConversaModal;
