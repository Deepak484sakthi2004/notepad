import { useState, useCallback, useRef } from 'react';
import { searchPages } from '@/api/search';
import { useWorkspaceStore } from '@/store/workspaceStore';

export function useSearch() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [isSearching, setIsSearching] = useState(false);
  const timerRef = useRef(null);
  const { activeWorkspaceId } = useWorkspaceStore();

  const search = useCallback(
    async (q) => {
      if (!q || q.trim().length < 2) {
        setResults([]);
        return;
      }
      setIsSearching(true);
      try {
        const res = await searchPages(q, activeWorkspaceId);
        setResults(res.data.results);
      } catch {
        setResults([]);
      } finally {
        setIsSearching(false);
      }
    },
    [activeWorkspaceId]
  );

  const handleQueryChange = useCallback(
    (value) => {
      setQuery(value);
      if (timerRef.current) clearTimeout(timerRef.current);
      timerRef.current = setTimeout(() => search(value), 300);
    },
    [search]
  );

  const clear = useCallback(() => {
    setQuery('');
    setResults([]);
  }, []);

  return { query, results, isSearching, handleQueryChange, clear };
}
