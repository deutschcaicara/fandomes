import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';                 // <-- sem “.tsx”
import { ConversaModalProvider } from '@/contexts/ModalConversaContext';
import './index.css';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <ConversaModalProvider>
      <App />
    </ConversaModalProvider>
  </React.StrictMode>,
);
