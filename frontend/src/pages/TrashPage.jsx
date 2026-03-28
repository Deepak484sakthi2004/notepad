import React, { useEffect, useState } from 'react';
import { Trash2, RotateCcw, AlertTriangle } from 'lucide-react';
import TopBar from '@/components/layout/TopBar';
import Button from '@/components/ui/Button';
import EmptyState from '@/components/ui/EmptyState';
import ConfirmDialog from '@/components/ui/ConfirmDialog';
import Spinner from '@/components/ui/Spinner';
import { useWorkspaceStore } from '@/store/workspaceStore';
import { getTrash } from '@/api/workspaces';
import { restorePage, permanentDeletePage } from '@/api/pages';
import { timeAgo } from '@/utils/helpers';
import toast from 'react-hot-toast';

export default function TrashPage() {
  const { activeWorkspaceId } = useWorkspaceStore();
  const [trashPages, setTrashPages] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [confirmDelete, setConfirmDelete] = useState(null);
  const [isDeleting, setIsDeleting] = useState(false);

  useEffect(() => {
    loadTrash();
  }, [activeWorkspaceId]);

  const loadTrash = async () => {
    setIsLoading(true);
    try {
      const res = await getTrash(activeWorkspaceId);
      setTrashPages(res.data.pages);
    } catch {
      toast.error('Failed to load trash');
    } finally {
      setIsLoading(false);
    }
  };

  const handleRestore = async (page) => {
    try {
      await restorePage(page.id);
      setTrashPages((prev) => prev.filter((p) => p.id !== page.id));
      toast.success(`"${page.title}" restored`);
    } catch {
      toast.error('Failed to restore page');
    }
  };

  const handlePermanentDelete = async () => {
    if (!confirmDelete) return;
    setIsDeleting(true);
    try {
      await permanentDeletePage(confirmDelete.id);
      setTrashPages((prev) => prev.filter((p) => p.id !== confirmDelete.id));
      toast.success('Page permanently deleted');
    } catch {
      toast.error('Failed to delete page');
    } finally {
      setIsDeleting(false);
      setConfirmDelete(null);
    }
  };

  return (
    <div className="flex flex-col h-full">
      <TopBar title="Trash" />
      <div className="flex-1 overflow-y-auto p-6">
        {isLoading ? (
          <div className="flex justify-center py-16">
            <Spinner size="lg" />
          </div>
        ) : trashPages.length === 0 ? (
          <EmptyState
            icon={<Trash2 size={48} />}
            title="Trash is empty"
            description="Deleted pages will appear here"
          />
        ) : (
          <div className="max-w-2xl mx-auto">
            <p className="text-sm text-gray-500 mb-4">
              Pages in trash are permanently deleted after 30 days.
            </p>
            <div className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
              {trashPages.map((page) => (
                <div
                  key={page.id}
                  className="flex items-center gap-3 px-4 py-3 border-b border-gray-50 last:border-0"
                >
                  <span className="text-xl flex-shrink-0">{page.icon || '📄'}</span>
                  <div className="flex-1 min-w-0">
                    <div className="text-sm font-medium text-gray-900 truncate">
                      {page.title || 'Untitled'}
                    </div>
                    <div className="text-xs text-gray-400">
                      Deleted {timeAgo(page.deleted_at)}
                    </div>
                  </div>
                  <div className="flex items-center gap-2 flex-shrink-0">
                    <button
                      onClick={() => handleRestore(page)}
                      className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
                    >
                      <RotateCcw size={12} />
                      Restore
                    </button>
                    <button
                      onClick={() => setConfirmDelete(page)}
                      className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-red-600 bg-red-50 hover:bg-red-100 rounded-lg transition-colors"
                    >
                      <Trash2 size={12} />
                      Delete
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      <ConfirmDialog
        isOpen={!!confirmDelete}
        onClose={() => setConfirmDelete(null)}
        onConfirm={handlePermanentDelete}
        isLoading={isDeleting}
        title="Permanently delete?"
        message={`"${confirmDelete?.title || 'This page'}" will be deleted forever. This cannot be undone.`}
        confirmLabel="Delete forever"
      />
    </div>
  );
}
