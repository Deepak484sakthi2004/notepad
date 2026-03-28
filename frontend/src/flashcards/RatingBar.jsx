import React from 'react';

const RATINGS = [
  { quality: 1, label: 'Again', color: 'bg-red-500 hover:bg-red-600', key: '1' },
  { quality: 2, label: 'Hard', color: 'bg-orange-400 hover:bg-orange-500', key: '2' },
  { quality: 3, label: 'Good', color: 'bg-blue-500 hover:bg-blue-600', key: '3' },
  { quality: 4, label: 'Easy', color: 'bg-green-500 hover:bg-green-600', key: '4' },
  { quality: 5, label: 'Perfect', color: 'bg-emerald-500 hover:bg-emerald-600', key: '5' },
];

export default function RatingBar({ onRate, disabled = false }) {
  return (
    <div className="flex items-center justify-center gap-3 flex-wrap">
      {RATINGS.map((r) => (
        <button
          key={r.quality}
          onClick={() => !disabled && onRate(r.quality)}
          disabled={disabled}
          className={`px-5 py-2 rounded-xl text-white text-sm font-semibold transition-colors disabled:opacity-40 disabled:cursor-not-allowed ${r.color}`}
          title={`Press ${r.key}`}
        >
          {r.label}
          <span className="ml-1.5 text-xs opacity-70">({r.key})</span>
        </button>
      ))}
    </div>
  );
}
