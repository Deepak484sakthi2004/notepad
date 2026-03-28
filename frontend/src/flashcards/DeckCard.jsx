import React from 'react';
import { useNavigate } from 'react-router-dom';
import { BookOpen, Play, Trash2, MoreHorizontal } from 'lucide-react';
import { timeAgo } from '@/utils/helpers';

export default function DeckCard({ deck, onDelete }) {
  const navigate = useNavigate();

  return (
    <div className="bg-white border border-gray-200 rounded-2xl p-5 hover:border-indigo-200 hover:shadow-md transition-all group flex flex-col gap-4">
      <div className="flex items-start justify-between">
        <div className="flex-1 min-w-0">
          <h3 className="font-semibold text-gray-900 truncate">{deck.name}</h3>
          {deck.description && (
            <p className="text-sm text-gray-500 mt-0.5 line-clamp-2">{deck.description}</p>
          )}
        </div>
        <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0 ml-2">
          <button
            onClick={() => onDelete?.(deck)}
            className="p-1.5 rounded-lg hover:bg-red-50 text-gray-400 hover:text-red-600 transition-colors"
          >
            <Trash2 size={14} />
          </button>
        </div>
      </div>

      <div className="flex items-center gap-3 text-sm text-gray-500">
        <div className="flex items-center gap-1.5 bg-gray-50 px-2.5 py-1 rounded-lg">
          <BookOpen size={13} className="text-indigo-400" />
          <span className="font-medium text-gray-700">{deck.card_count ?? 0}</span>
          <span className="text-gray-400">cards</span>
        </div>
        <span className="text-gray-300">·</span>
        <span className="text-xs text-gray-400">{timeAgo(deck.updated_at)}</span>
      </div>

      <div className="flex gap-2">
        <button
          onClick={() => navigate(`/decks/${deck.id}`)}
          className="flex-1 flex items-center justify-center gap-1.5 px-3 py-2 text-sm font-medium text-gray-700 bg-gray-50 hover:bg-gray-100 rounded-xl transition-colors"
        >
          <BookOpen size={14} />
          Browse
        </button>
        <button
          onClick={() => navigate(`/study/${deck.id}`)}
          className="flex-1 flex items-center justify-center gap-1.5 px-3 py-2 text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 rounded-xl transition-colors"
        >
          <Play size={14} />
          Study
        </button>
      </div>
    </div>
  );
}
