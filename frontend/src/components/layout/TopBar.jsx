import React, { useState, useEffect } from 'react';
import { Search, Bell } from 'lucide-react';
import SearchModal from '@/components/search/SearchModal';

export default function TopBar({ title, actions }) {
  const [searchOpen, setSearchOpen] = useState(false);

  useEffect(() => {
    const handler = (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        setSearchOpen(true);
      }
    };
    document.addEventListener('keydown', handler);
    return () => document.removeEventListener('keydown', handler);
  }, []);

  return (
    <>
      <header className="h-14 flex-shrink-0 bg-white border-b border-gray-100 flex items-center px-6 gap-4">
        {title && (
          <h1 className="text-base font-semibold text-gray-800 truncate">
            {title}
          </h1>
        )}
        <div className="flex-1" />
        <button
          onClick={() => setSearchOpen(true)}
          className="flex items-center gap-2 px-3 py-1.5 text-sm text-gray-500 bg-gray-50 hover:bg-gray-100 border border-gray-200 rounded-lg transition-colors"
        >
          <Search size={14} />
          <span>Search</span>
          <kbd className="hidden sm:inline text-xs text-gray-400 font-mono">⌘K</kbd>
        </button>
        {actions}
      </header>
      <SearchModal isOpen={searchOpen} onClose={() => setSearchOpen(false)} />
    </>
  );
}
