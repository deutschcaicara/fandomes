// File: src/pages/AnalyticsView.tsx
// CORREÇÃO: Substituído classes 'slate' por 'neutral'

import React from 'react';
import { Loader2 } from 'lucide-react';
import { useAnalytics } from '../hooks/useAnalytics';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Legend,
} from 'recharts';
import type { AnalyticsData } from '../types/analytics'; // Importa o tipo

// Componente StatCard movido para dentro ou importado
const StatCard = ({ label, value }: { label: string; value: number | string }) => (
  // CORREÇÃO: Trocado text-slate-500
  <div className="bg-white rounded-lg shadow p-4 text-center">
    <p className="text-sm text-neutral-500">{label}</p>
    <p className="text-3xl font-bold text-brand-primary mt-1">{value}</p>
  </div>
);


const AnalyticsView: React.FC = () => {
  const { data, loading, error } = useAnalytics();

  if (loading)
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 className="animate-spin h-6 w-6 text-brand-secondary" />
      </div>
    );

  if (error || !data)
    return <p className="text-center text-red-600">{error ?? 'Sem dados'}</p>;

  // Certifique-se que 'data' não é null antes de acessar suas propriedades
  const chartData = data ? [
    { nome: 'Leads', valor: data.leads },
    { nome: 'Qualificados', valor: data.qualificados },
    { nome: 'Pagos', valor: data.pagos },
  ] : [];

  return (
    <div className="p-6 space-y-6">
      {/* CORREÇÃO: Trocado text-slate-700 */}
      <h2 className="text-2xl font-semibold text-neutral-700">Painel de KPIs</h2>

      {/* Cartões resumidos */}
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
        <StatCard label="Leads 24 h" value={data.leads} />
        <StatCard label="Qualificados 24 h" value={data.qualificados} />
        <StatCard label="Pagamentos 24 h" value={data.pagos} />
        <StatCard
          label="⌀ Lead → Pgto (s)"
          value={data.tempo_pg_segundos.toFixed(0)}
        />
      </div>

      {/* Gráfico de barras */}
      <div className="bg-white p-6 rounded-lg shadow">
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="nome" />
            <YAxis allowDecimals={false} />
            <Tooltip />
            <Legend />
            <Bar dataKey="valor" name="Total" />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default AnalyticsView;

