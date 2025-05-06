import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import DomoShell from '@/layouts/DomoShell';
import DashboardKanban from '@/pages/DashboardKanban';
import KanbanView from '@/pages/KanbanView';           // legado
import ChatView from '@/pages/ChatView';               // legado
import AnalyticsView from '@/pages/AnalyticsView';     // legado

const App: React.FC = () => (
  <BrowserRouter>
    <Routes>
      <Route element={<DomoShell />}>
        {/* novo painel */}
        <Route path="/kanban" element={<DashboardKanban />} />

        {/* rotas antigas para não quebrar nada */}
        <Route path="/kanban-old" element={<KanbanView />} />
        <Route path="/conversas" element={<ChatView />} />
        <Route path="/analytics" element={<AnalyticsView />} />

        {/* fallback */}
        <Route path="*" element={<Navigate to="/kanban" replace />} />
      </Route>
    </Routes>
  </BrowserRouter>
);

export default App;
