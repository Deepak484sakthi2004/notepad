import React, { useEffect, useRef, useState, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Star, StarOff, Trash2, Download, Copy, Sparkles,
  BookOpen, Play, ChevronRight, CheckCircle, Clock, Loader2,
} from 'lucide-react';
import BlockEditor from '@/editor/BlockEditor';
import TopBar from '@/components/layout/TopBar';
import Button from '@/components/ui/Button';
import Spinner from '@/components/ui/Spinner';
import AskAIPanel from '@/flashcards/AskAIPanel';
import { useEditorStore } from '@/store/editorStore';
import { useWorkspaceStore } from '@/store/workspaceStore';
import { getPage, updatePage, deletePage, addFavourite, removeFavourite, exportPage } from '@/api/pages';
import { generateFlashcards, getDeckStats } from '@/api/flashcards';
import { useAutoSave } from '@/hooks/useAutoSave';
import { downloadBlob, timeAgo } from '@/utils/helpers';
import toast from 'react-hot-toast';

export default function NoteEditorPage() {
  const { pageId } = useParams();
  const navigate = useNavigate();
  const {
    currentPage,
    setCurrentPage,
    isSaving,
    lastSavedAt,
    showAIPanel,
    toggleAIPanel,
    showFlashcardPanel,
    toggleFlashcardPanel,
  } = useEditorStore();

  const { updatePageInList, removePageFromList } = useWorkspaceStore();
  const [isLoading, setIsLoading] = useState(true);
  const [isFavourited, setIsFavourited] = useState(false);
  const [deckStats, setDeckStats] = useState(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [isExporting, setIsExporting] = useState(false);

  const contentRef = useRef(null);

  const getContent = useCallback(() => contentRef.current, []);
  const { scheduleAutoSave } = useAutoSave(pageId, getContent, 1000);

  useEffect(() => {
    if (!pageId) return;
    loadPage();
  }, [pageId]);

  const loadPage = async () => {
    setIsLoading(true);
    try {
      const res = await getPage(pageId);
      const page = res.data.page;
      setCurrentPage(page);
      setIsFavourited(false); // We'd check page.favourited_by in a real scenario
    } catch (err) {
      if (err.response?.status === 404) {
        toast.error('Page not found');
        navigate('/', { replace: true });
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleContentChange = useCallback(
    ({ blocks, plain_text }) => {
      contentRef.current = { blocks, plain_text };
      scheduleAutoSave({ blocks, plain_text });
    },
    [scheduleAutoSave]
  );

  const handleTitleChange = async (newTitle) => {
    if (!currentPage || newTitle === currentPage.title) return;
    try {
      await updatePage(pageId, { title: newTitle });
      setCurrentPage({ ...currentPage, title: newTitle });
      updatePageInList(pageId, { title: newTitle });
    } catch {
      toast.error('Failed to update title');
    }
  };

  const handleFavourite = async () => {
    try {
      if (isFavourited) {
        await removeFavourite(pageId);
        setIsFavourited(false);
        toast.success('Removed from favourites');
      } else {
        await addFavourite(pageId);
        setIsFavourited(true);
        toast.success('Added to favourites');
      }
    } catch {
      toast.error('Failed to update favourite');
    }
  };

  const handleDelete = async () => {
    if (!confirm('Move this page to trash?')) return;
    try {
      await deletePage(pageId);
      removePageFromList(pageId);
      toast.success('Page moved to trash');
      navigate('/', { replace: true });
    } catch {
      toast.error('Failed to delete page');
    }
  };

  const handleExport = async (format) => {
    setIsExporting(true);
    try {
      const res = await exportPage(pageId, format);
      downloadBlob(res.data, `${currentPage?.title || 'note'}.${format}`);
    } catch {
      toast.error('Export failed');
    } finally {
      setIsExporting(false);
    }
  };

  const handleGenerateFlashcards = async () => {
    setIsGenerating(true);
    try {
      const res = await generateFlashcards({ page_id: pageId, num_cards: 10 });
      const deck = res.data.deck;
      toast.success(`Generated ${deck.card_count ?? 'new'} flashcards!`);
      setDeckStats({ total: deck.card_count ?? 0, due: 0 });
    } catch (err) {
      toast.error(err.response?.data?.error || 'Generation failed');
    } finally {
      setIsGenerating(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <Spinner size="lg" />
      </div>
    );
  }

  if (!currentPage) return null;

  return (
    <div className="flex flex-col h-full">
      <TopBar
        actions={
          <div className="flex items-center gap-2">
            {/* Save indicator */}
            <div className="flex items-center gap-1.5 text-xs text-gray-400">
              {isSaving ? (
                <>
                  <Loader2 size={12} className="animate-spin" />
                  <span>Saving…</span>
                </>
              ) : lastSavedAt ? (
                <>
                  <CheckCircle size={12} className="text-green-500" />
                  <span>Saved {timeAgo(lastSavedAt)}</span>
                </>
              ) : null}
            </div>
            <button
              onClick={handleFavourite}
              className={`p-2 rounded-lg hover:bg-gray-100 transition-colors ${
                isFavourited ? 'text-yellow-500' : 'text-gray-400 hover:text-gray-600'
              }`}
              title={isFavourited ? 'Remove favourite' : 'Add favourite'}
            >
              {isFavourited ? <Star size={16} fill="currentColor" /> : <Star size={16} />}
            </button>
            <div className="relative group">
              <button className="p-2 rounded-lg hover:bg-gray-100 text-gray-400 hover:text-gray-600 transition-colors">
                <Download size={16} />
              </button>
              <div className="absolute right-0 top-full mt-1 bg-white rounded-xl shadow-xl border border-gray-100 py-1 w-36 opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all z-20">
                {['md', 'txt', 'pdf'].map((fmt) => (
                  <button
                    key={fmt}
                    onClick={() => handleExport(fmt)}
                    className="w-full px-4 py-2 text-sm text-left text-gray-700 hover:bg-gray-50 uppercase"
                  >
                    .{fmt}
                  </button>
                ))}
              </div>
            </div>
            <button
              onClick={handleDelete}
              className="p-2 rounded-lg hover:bg-red-50 text-gray-400 hover:text-red-600 transition-colors"
              title="Move to trash"
            >
              <Trash2 size={16} />
            </button>
          </div>
        }
      />

      <div className="flex flex-1 overflow-hidden">
        {/* Editor area */}
        <div className="flex-1 flex flex-col overflow-hidden">
          {/* Page title */}
          <div className="px-8 pt-8 pb-0">
            <div className="flex items-center gap-3 mb-1">
              <span className="text-3xl">{currentPage.icon || '📄'}</span>
            </div>
            <input
              type="text"
              defaultValue={currentPage.title || ''}
              placeholder="Untitled"
              onBlur={(e) => handleTitleChange(e.target.value)}
              className="w-full text-3xl font-bold text-gray-900 placeholder-gray-300 outline-none bg-transparent py-1"
            />
          </div>
          {/* Editor */}
          <div className="flex-1 overflow-hidden">
            <BlockEditor
              initialContent={currentPage.blocks || ''}
              onChange={handleContentChange}
              placeholder="Start writing, or type / for commands…"
            />
          </div>
        </div>

        {/* Right panel */}
        {showFlashcardPanel && (
          <div className="w-72 flex-shrink-0 border-l border-gray-100 flex flex-col overflow-y-auto p-4 gap-4 bg-gray-50">
            <div className="flex items-center justify-between">
              <span className="text-sm font-semibold text-gray-700 flex items-center gap-1.5">
                <BookOpen size={15} className="text-indigo-600" />
                Flashcards
              </span>
              <button
                onClick={toggleFlashcardPanel}
                className="text-gray-400 hover:text-gray-600 p-1"
              >
                <ChevronRight size={14} />
              </button>
            </div>

            {deckStats && (
              <div className="grid grid-cols-2 gap-2">
                <div className="bg-white rounded-xl p-3 border border-gray-100">
                  <div className="text-xl font-bold text-gray-900">{deckStats.total}</div>
                  <div className="text-xs text-gray-500">Total cards</div>
                </div>
                <div className="bg-white rounded-xl p-3 border border-gray-100">
                  <div className="text-xl font-bold text-indigo-600">{deckStats.due}</div>
                  <div className="text-xs text-gray-500">Due today</div>
                </div>
              </div>
            )}

            <Button
              variant="primary"
              size="sm"
              className="w-full"
              icon={<Sparkles size={14} />}
              onClick={handleGenerateFlashcards}
              loading={isGenerating}
            >
              Generate Flashcards
            </Button>

            <Button
              variant="secondary"
              size="sm"
              className="w-full"
              icon={<Play size={14} />}
              onClick={() => navigate('/decks')}
            >
              Go to Decks
            </Button>

            <div className="mt-2 border-t border-gray-200 pt-3">
              <button
                onClick={toggleAIPanel}
                className="w-full flex items-center gap-2 text-sm text-indigo-600 hover:text-indigo-800 font-medium"
              >
                <Sparkles size={14} />
                {showAIPanel ? 'Close AI Chat' : 'Ask AI'}
              </button>
            </div>
          </div>
        )}
      </div>

      {/* AI Panel overlay */}
      {showAIPanel && (
        <div className="fixed bottom-6 right-6 w-96 z-30">
          <AskAIPanel card={null} onClose={toggleAIPanel} />
        </div>
      )}
    </div>
  );
}
