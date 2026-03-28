import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { BookOpen, CheckCircle, Layers, TrendingUp, Play, Plus } from 'lucide-react';
import TopBar from '@/components/layout/TopBar';
import Button from '@/components/ui/Button';
import Spinner from '@/components/ui/Spinner';
import { useFlashcardStore } from '@/store/flashcardStore';
import { useAuthStore } from '@/store/authStore';
import { timeAgo } from '@/utils/helpers';

function StatCard({ icon: Icon, label, value, color = 'indigo' }) {
  const colors = {
    indigo: 'bg-indigo-50 text-indigo-600',
    green: 'bg-green-50 text-green-600',
    amber: 'bg-amber-50 text-amber-600',
    blue: 'bg-blue-50 text-blue-600',
  };
  return (
    <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-5 flex items-start gap-4">
      <div className={`w-11 h-11 rounded-xl flex items-center justify-center flex-shrink-0 ${colors[color]}`}>
        <Icon size={20} />
      </div>
      <div>
        <div className="text-2xl font-bold text-gray-900">{value ?? '—'}</div>
        <div className="text-sm text-gray-500 mt-0.5">{label}</div>
      </div>
    </div>
  );
}

export default function DashboardPage() {
  const navigate = useNavigate();
  const { user } = useAuthStore();
  const { stats, decks, fetchStats, fetchDecks, isLoading } = useFlashcardStore();

  useEffect(() => {
    fetchStats();
    fetchDecks();
  }, []);

  const dueDecks = decks.filter((d) => d.card_count > 0).slice(0, 4);

  return (
    <div className="flex flex-col h-full">
      <TopBar title="Dashboard" />
      <div className="flex-1 overflow-y-auto p-6">
        <div className="max-w-4xl mx-auto">
          {/* Greeting */}
          <div className="mb-8">
            <h2 className="text-2xl font-bold text-gray-900">
              Good {getTimeOfDay()}, {user?.name?.split(' ')[0] ?? 'there'} 👋
            </h2>
            <p className="text-gray-500 mt-1">
              {stats?.due_today > 0
                ? `You have ${stats.due_today} cards due for review today.`
                : "You're all caught up on your flashcards!"}
            </p>
          </div>

          {/* Stats row */}
          {isLoading ? (
            <div className="flex justify-center py-8">
              <Spinner size="lg" />
            </div>
          ) : (
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-8">
              <StatCard icon={Layers} label="Total decks" value={stats?.total_decks} color="indigo" />
              <StatCard icon={BookOpen} label="Total cards" value={stats?.total_cards} color="blue" />
              <StatCard icon={CheckCircle} label="Due today" value={stats?.due_today} color="amber" />
              <StatCard icon={TrendingUp} label="Accuracy" value={stats ? `${stats.accuracy}%` : null} color="green" />
            </div>
          )}

          {/* Due now CTA */}
          {stats?.due_today > 0 && (
            <div className="bg-gradient-to-br from-indigo-600 to-indigo-700 rounded-2xl p-6 mb-6 flex items-center justify-between">
              <div>
                <div className="text-white font-bold text-lg">
                  {stats.due_today} cards due for review
                </div>
                <div className="text-indigo-200 text-sm mt-1">
                  Keep your streak going — study now!
                </div>
              </div>
              <Button
                variant="secondary"
                icon={<Play size={15} />}
                onClick={() => navigate('/decks')}
              >
                Study now
              </Button>
            </div>
          )}

          {/* Recent decks */}
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-base font-semibold text-gray-800">Your decks</h3>
            <button
              onClick={() => navigate('/decks')}
              className="text-sm text-indigo-600 hover:text-indigo-800 font-medium"
            >
              View all
            </button>
          </div>

          {dueDecks.length === 0 ? (
            <div className="bg-gray-50 rounded-2xl p-8 text-center">
              <div className="text-gray-400 mb-3"><BookOpen size={36} className="mx-auto" /></div>
              <p className="text-gray-600 font-medium">No flashcard decks yet</p>
              <p className="text-gray-400 text-sm mt-1">Open a page and generate flashcards from your notes</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {dueDecks.map((deck) => (
                <div
                  key={deck.id}
                  className="bg-white rounded-2xl border border-gray-100 shadow-sm p-5 hover:border-indigo-200 hover:shadow-md transition-all"
                >
                  <div className="flex items-center justify-between mb-3">
                    <h4 className="font-semibold text-gray-900 truncate">{deck.name}</h4>
                    <span className="text-xs text-gray-400">{timeAgo(deck.updated_at)}</span>
                  </div>
                  <div className="text-sm text-gray-500 mb-4">
                    {deck.card_count} cards
                  </div>
                  <button
                    onClick={() => navigate(`/study/${deck.id}`)}
                    className="w-full flex items-center justify-center gap-2 py-2 text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 rounded-xl transition-colors"
                  >
                    <Play size={13} />
                    Study
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function getTimeOfDay() {
  const h = new Date().getHours();
  if (h < 12) return 'morning';
  if (h < 17) return 'afternoon';
  return 'evening';
}
