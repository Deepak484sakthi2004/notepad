import { useEffect, useRef, useCallback } from 'react';
import { useEditorStore } from '@/store/editorStore';
import { updatePageContent } from '@/api/pages';
import toast from 'react-hot-toast';

export function useAutoSave(pageId, getContent, delay = 1000) {
  const timerRef = useRef(null);
  const { setSaving, setLastSavedAt, setSaveError } = useEditorStore();
  const pendingRef = useRef(false);

  const save = useCallback(
    async (content) => {
      if (!pageId || !content) return;
      setSaving(true);
      setSaveError(null);
      try {
        await updatePageContent(pageId, content);
        setLastSavedAt(new Date());
      } catch (err) {
        setSaveError('Failed to save');
        toast.error('Auto-save failed');
      } finally {
        setSaving(false);
        pendingRef.current = false;
      }
    },
    [pageId, setSaving, setLastSavedAt, setSaveError]
  );

  const scheduleAutoSave = useCallback(
    (content) => {
      if (timerRef.current) {
        clearTimeout(timerRef.current);
      }
      pendingRef.current = true;
      timerRef.current = setTimeout(() => {
        save(content);
      }, delay);
    },
    [save, delay]
  );

  // Flush on unmount
  useEffect(() => {
    return () => {
      if (timerRef.current) {
        clearTimeout(timerRef.current);
      }
      if (pendingRef.current && getContent) {
        const content = getContent();
        if (content) save(content);
      }
    };
  }, [save, getContent]);

  return { scheduleAutoSave, saveNow: save };
}
