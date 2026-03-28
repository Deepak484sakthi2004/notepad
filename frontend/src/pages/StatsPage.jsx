import React, { useEffect, useState } from 'react';
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, BarChart, Bar,
} from 'recharts';
import { TrendingUp, CheckCircle, BookOpen, Layers } from 'lucide-react';
import TopBar from '@/components/layout/TopBar';
import Spinner from '@/components/ui/Spinner';
import { useFlashcardStore } from '@/store/flashcardStore';
import { formatDate } from '@/utils/helpers';

function StatCard({ icon: Icon, label, value, color }) {
  const colors = {
    indigo: 'bg-indigo-50 text-indigo-600',
    green: 'bg-green-50 text-green-600',
    amber: 'bg-amber-50 text-amber-600',
    blue: 'bg-blue-50 text-blue-600',
  };
  return (
    <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-5 flex items-start gap-4">
      <div className={`w-11 h-11 rounded-xl flex items-center justify-center ${colors[color]}`}>
        <Icon size={20} />
      </div>
      <div>
        <div className="text-2xl font-bold text-gray-900">{value ?? '—'}</div>
        <div className="text-sm text-gray-500 mt-0.5">{label}</div>
      </div>
    </div>
  );
}

export default function StatsPage() {
  const { stats, history, fetchStats, fetchHistory } = useFlashcardStore();
  const [days, setDays] = useState(30);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    Promise.all([fetchStats(), fetchHistory(days)]).finally(() =>
      setIsLoading(false)
    );
  }, [days]);

  const chartData = history.map((h) => ({
    date: formatDate(h.date, 'MMM d'),
    total: h.total,
    correct: h.correct,
    accuracy: h.total > 0 ? Math.round((h.correct / h.total) * 100) : 0,
  }));

  return (
    <div className="flex flex-col h-full">
      <TopBar title="Statistics" />
      <div className="flex-1 overflow-y-auto p-6">
        {isLoading ? (
          <div className="flex justify-center py-16">
            <Spinner size="lg" />
          </div>
        ) : (
          <div className="max-w-4xl mx-auto space-y-8">
            {/* Overview cards */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              <StatCard icon={Layers} label="Total decks" value={stats?.total_decks} color="indigo" />
              <StatCard icon={BookOpen} label="Total cards" value={stats?.total_cards} color="blue" />
              <StatCard icon={CheckCircle} label="Total reviews" value={stats?.total_reviews} color="green" />
              <StatCard icon={TrendingUp} label="Accuracy" value={stats ? `${stats.accuracy}%` : null} color="amber" />
            </div>

            {/* Period selector */}
            <div className="flex items-center gap-2">
              <span className="text-sm text-gray-500">Show last:</span>
              {[7, 14, 30, 90].map((d) => (
                <button
                  key={d}
                  onClick={() => setDays(d)}
                  className={`px-3 py-1 text-sm rounded-lg transition-colors ${
                    days === d
                      ? 'bg-indigo-600 text-white'
                      : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                  }`}
                >
                  {d}d
                </button>
              ))}
            </div>

            {/* Activity chart */}
            <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6">
              <h3 className="text-base font-semibold text-gray-800 mb-6">Daily Reviews</h3>
              {chartData.length === 0 ? (
                <div className="h-48 flex items-center justify-center text-gray-400 text-sm">
                  No review data yet
                </div>
              ) : (
                <ResponsiveContainer width="100%" height={200}>
                  <AreaChart data={chartData}>
                    <defs>
                      <linearGradient id="colorTotal" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#6366f1" stopOpacity={0.15} />
                        <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
                      </linearGradient>
                      <linearGradient id="colorCorrect" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#10b981" stopOpacity={0.15} />
                        <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                    <XAxis dataKey="date" tick={{ fontSize: 11, fill: '#9ca3af' }} tickLine={false} axisLine={false} />
                    <YAxis tick={{ fontSize: 11, fill: '#9ca3af' }} tickLine={false} axisLine={false} />
                    <Tooltip
                      contentStyle={{ border: 'none', borderRadius: 12, boxShadow: '0 4px 24px rgba(0,0,0,0.08)', fontSize: 12 }}
                    />
                    <Area type="monotone" dataKey="total" stroke="#6366f1" strokeWidth={2} fill="url(#colorTotal)" name="Reviewed" />
                    <Area type="monotone" dataKey="correct" stroke="#10b981" strokeWidth={2} fill="url(#colorCorrect)" name="Correct" />
                  </AreaChart>
                </ResponsiveContainer>
              )}
            </div>

            {/* Accuracy chart */}
            <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6">
              <h3 className="text-base font-semibold text-gray-800 mb-6">Accuracy Over Time (%)</h3>
              {chartData.length === 0 ? (
                <div className="h-48 flex items-center justify-center text-gray-400 text-sm">
                  No review data yet
                </div>
              ) : (
                <ResponsiveContainer width="100%" height={200}>
                  <BarChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                    <XAxis dataKey="date" tick={{ fontSize: 11, fill: '#9ca3af' }} tickLine={false} axisLine={false} />
                    <YAxis domain={[0, 100]} tick={{ fontSize: 11, fill: '#9ca3af' }} tickLine={false} axisLine={false} unit="%" />
                    <Tooltip
                      contentStyle={{ border: 'none', borderRadius: 12, boxShadow: '0 4px 24px rgba(0,0,0,0.08)', fontSize: 12 }}
                      formatter={(v) => [`${v}%`, 'Accuracy']}
                    />
                    <Bar dataKey="accuracy" fill="#6366f1" radius={[4, 4, 0, 0]} name="Accuracy" />
                  </BarChart>
                </ResponsiveContainer>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
