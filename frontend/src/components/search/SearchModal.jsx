import React, { useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, FileText, X } from 'lucide-react';
import { useSearch } from '@/hooks/useSearch';
import Spinner from '@/components/ui/Spinner';
import { timeAgo } from '@/utils/helpers';

export default function SearchModal({ isOpen, onClose }) {
  const navigate = useNavigate();
  const inputRef = useRef(null);
  const { query, results, isSearching, handleQueryChange, clear } = useSearch();

  useEffect(() => {
    if (isOpen) {
      setTimeout(() => inputRef.current?.focus(), 50);
    } else {
      clear();
    }
  }, [isOpen]);

  useEffect(() => {
    if (!isOpen) return;
    const handler = (e) => {
      if (e.key === 'Escape') onClose();
    };
    document.addEventListener('keydown', handler);
    return () => document.removeEventListener('keydown', handler);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const handleSelect = (page) => {
    navigate(`/page/${page.id}`);
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center pt-24 px-4">
      <div
        className="absolute inset-0 bg-black/40 backdrop-blur-sm"
        onClick={onClose}
      />
      <div className="relative w-full max-w-xl bg-white rounded-2xl shadow-2xl overflow-hidden animate-fade-in">
        {/* Search input */}
        <div className="flex items-center gap-3 px-4 py-3 border-b border-gray-100">
          {isSearching ? (
            <Spinner size="sm" />
          ) : (
            <Search size={18} className="text-gray-400 flex-shrink-0" />
          )}
          <input
            ref={inputRef}
            type="text"
            placeholder="Search pages…"
            value={query}
            onChange={(e) => handleQueryChange(e.target.value)}
            className="flex-1 text-sm text-gray-900 placeholder-gray-400 outline-none"
          />
          {query && (
            <button onClick={clear} className="text-gray-400 hover:text-gray-600">
              <X size={16} />
            </button>
          )}
          <kbd className="hidden sm:inline-flex items-center px-2 py-0.5 text-xs text-gray-500 bg-gray-100 rounded font-mono">
            Esc
          </kbd>
        </div>

        {/* Results */}
        <div className="max-h-96 overflow-y-auto">
          {!query && (
            <div className="px-4 py-8 text-center text-sm text-gray-400">
              Start typing to search your notes…
            </div>
          )}
          {query && results.length === 0 && !isSearching && (
            <div className="px-4 py-8 text-center text-sm text-gray-400">
              No pages found for "{query}"
            </div>
          )}
          {results.map((page) => (
            <button
              key={page.id}
              onClick={() => handleSelect(page)}
              className="w-full flex items-start gap-3 px-4 py-3 hover:bg-gray-50 transition-colors text-left border-b border-gray-50 last:border-0"
            >
              <span className="text-lg mt-0.5 flex-shrink-0">
                {page.icon || '📄'}
              </span>
              <div className="flex-1 min-w-0">
                <div className="text-sm font-medium text-gray-900 truncate">
                  {page.title || 'Untitled'}
                </div>
                {page.snippet && (
                  <div className="text-xs text-gray-500 mt-0.5 line-clamp-2">
                    {page.snippet}
                  </div>
                )}
              </div>
              <span className="text-xs text-gray-400 flex-shrink-0 mt-0.5">
                {timeAgo(page.updated_at)}
              </span>
            </button>
          ))}
        </div>

        {/* Footer */}
        <div className="px-4 py-2 border-t border-gray-100 bg-gray-50 flex items-center gap-4 text-xs text-gray-400">
          <span>
            <kbd className="font-mono bg-white border border-gray-200 rounded px-1">↑↓</kbd>{' '}
            navigate
          </span>
          <span>
            <kbd className="font-mono bg-white border border-gray-200 rounded px-1">↵</kbd>{' '}
            open
          </span>
          <span>
            <kbd className="font-mono bg-white border border-gray-200 rounded px-1">Esc</kbd>{' '}
            close
          </span>
        </div>
      </div>
    </div>
  );
}
