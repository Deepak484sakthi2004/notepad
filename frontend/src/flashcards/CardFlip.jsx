import React from 'react';
import { Flag, RotateCcw } from 'lucide-react';
import { difficultyLabel, difficultyColor, classNames } from '@/utils/helpers';

export default function CardFlip({ card, isFlipped, onFlip }) {
  if (!card) return null;

  return (
    <div className="flip-card w-full h-64 sm:h-72 cursor-pointer select-none" onClick={onFlip}>
      <div className={classNames('flip-card-inner w-full h-full', isFlipped && 'flipped')}>
        {/* Front */}
        <div className="flip-card-front w-full h-full bg-white rounded-2xl border border-gray-200 shadow-lg flex flex-col">
          <div className="flex items-center justify-between px-5 pt-4 pb-2">
            <span className={classNames(
              'text-xs font-medium px-2 py-0.5 rounded-full',
              difficultyColor(card.difficulty)
            )}>
              {difficultyLabel(card.difficulty)}
            </span>
            <span className="text-xs text-gray-400 bg-gray-100 px-2 py-0.5 rounded-full">
              {card.question_type || 'recall'}
            </span>
          </div>
          <div className="flex-1 flex items-center justify-center px-8 py-4">
            <p className="text-lg font-medium text-gray-900 text-center leading-relaxed">
              {card.question}
            </p>
          </div>
          <div className="px-5 pb-4 text-center">
            <p className="text-xs text-gray-400">Click to reveal answer</p>
          </div>
        </div>

        {/* Back */}
        <div className="flip-card-back w-full h-full bg-indigo-50 rounded-2xl border border-indigo-200 shadow-lg flex flex-col">
          <div className="flex items-center justify-between px-5 pt-4 pb-2">
            <span className="text-xs font-semibold text-indigo-600 uppercase tracking-wider">Answer</span>
            {card.is_flagged && (
              <span className="text-xs text-amber-600 flex items-center gap-1">
                <Flag size={11} /> Flagged
              </span>
            )}
          </div>
          <div className="flex-1 overflow-y-auto flex items-center justify-center px-8 py-4">
            <p className="text-base text-gray-800 text-center leading-relaxed">
              {card.answer}
            </p>
          </div>
          {card.source_snippet && (
            <div className="mx-5 mb-4 px-3 py-2 bg-white/70 rounded-lg text-xs text-gray-500 italic border border-indigo-100">
              "{card.source_snippet}"
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
