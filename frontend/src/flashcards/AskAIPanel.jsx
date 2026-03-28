import React, { useState } from 'react';
import { Send, Sparkles, X } from 'lucide-react';
import { askAI } from '@/api/flashcards';
import Spinner from '@/components/ui/Spinner';

export default function AskAIPanel({ card, onClose }) {
  const [question, setQuestion] = useState('');
  const [answer, setAnswer] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const handleAsk = async () => {
    if (!question.trim() || !card) return;
    setIsLoading(true);
    setError('');
    setAnswer('');
    try {
      const res = await askAI({ card_id: card.id, question });
      setAnswer(res.data.answer);
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to get AI response');
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleAsk();
    }
  };

  return (
    <div className="bg-white rounded-2xl border border-indigo-100 shadow-lg p-4 flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 text-indigo-600 font-semibold text-sm">
          <Sparkles size={15} />
          <span>Ask AI about this card</span>
        </div>
        <button
          onClick={onClose}
          className="p-1 text-gray-400 hover:text-gray-600 rounded"
        >
          <X size={14} />
        </button>
      </div>

      <div className="flex gap-2">
        <textarea
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask a question about this flashcard…"
          rows={2}
          className="flex-1 text-sm text-gray-900 placeholder-gray-400 border border-gray-200 rounded-lg px-3 py-2 resize-none focus:outline-none focus:border-indigo-400 focus:ring-2 focus:ring-indigo-100"
        />
        <button
          onClick={handleAsk}
          disabled={isLoading || !question.trim()}
          className="px-3 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg transition-colors disabled:opacity-40 flex-shrink-0"
        >
          {isLoading ? <Spinner size="sm" /> : <Send size={14} />}
        </button>
      </div>

      {error && (
        <p className="text-xs text-red-500">{error}</p>
      )}

      {answer && (
        <div className="bg-indigo-50 rounded-lg px-3 py-2.5 text-sm text-gray-800 leading-relaxed">
          {answer}
        </div>
      )}
    </div>
  );
}
