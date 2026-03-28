import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus, FileText, Clock } from 'lucide-react';
import TopBar from '@/components/layout/TopBar';
import Button from '@/components/ui/Button';
import EmptyState from '@/components/ui/EmptyState';
import { useWorkspaceStore } from '@/store/workspaceStore';
import { createPage } from '@/api/workspaces';
import { timeAgo, buildPageTree } from '@/utils/helpers';
import toast from 'react-hot-toast';

function PageRow({ page, onClick }) {
  return (
    <button
      onClick={onClick}
      className="w-full flex items-center gap-3 px-4 py-3 rounded-xl hover:bg-gray-50 transition-colors text-left group"
    >
      <span className="text-xl flex-shrink-0">{page.icon || '📄'}</span>
      <div className="flex-1 min-w-0">
        <div className="text-sm font-medium text-gray-900 truncate">
          {page.title || 'Untitled'}
        </div>
        {page.updated_at && (
          <div className="text-xs text-gray-400 mt-0.5">{timeAgo(page.updated_at)}</div>
        )}
      </div>
    </button>
  );
}

export default function WorkspacePage() {
  const navigate = useNavigate();
  const { activeWorkspaceId, pages, fetchPages, addPage, activeWorkspace } = useWorkspaceStore();
  const [isCreating, setIsCreating] = useState(false);

  useEffect(() => {
    if (activeWorkspaceId) {
      fetchPages(activeWorkspaceId);
    }
  }, [activeWorkspaceId]);

  const handleNewPage = async () => {
    if (!activeWorkspaceId || isCreating) return;
    setIsCreating(true);
    try {
      const res = await createPage(activeWorkspaceId, { title: 'Untitled' });
      const page = res.data.page;
      addPage(page);
      navigate(`/page/${page.id}`);
    } catch {
      toast.error('Failed to create page');
    } finally {
      setIsCreating(false);
    }
  };

  const activePage = useWorkspaceStore((s) => s.workspaces.find((w) => w.id === s.activeWorkspaceId));
  const visiblePages = pages.filter((p) => !p.is_deleted);
  const recentPages = [...visiblePages]
    .sort((a, b) => new Date(b.updated_at) - new Date(a.updated_at))
    .slice(0, 10);

  return (
    <div className="flex flex-col h-full">
      <TopBar
        title={activePage?.name || 'Workspace'}
        actions={
          <Button
            size="sm"
            icon={<Plus size={15} />}
            onClick={handleNewPage}
            loading={isCreating}
          >
            New page
          </Button>
        }
      />

      <div className="flex-1 overflow-y-auto p-6">
        {visiblePages.length === 0 ? (
          <EmptyState
            icon={<FileText size={48} />}
            title="No pages yet"
            description="Create your first page to start writing notes"
            action={
              <Button icon={<Plus size={16} />} onClick={handleNewPage} loading={isCreating}>
                Create first page
              </Button>
            }
          />
        ) : (
          <div className="max-w-2xl mx-auto">
            <div className="flex items-center gap-2 mb-4">
              <Clock size={16} className="text-gray-400" />
              <h2 className="text-sm font-semibold text-gray-600 uppercase tracking-wide">
                Recent pages
              </h2>
            </div>
            <div className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
              {recentPages.map((page) => (
                <PageRow
                  key={page.id}
                  page={page}
                  onClick={() => navigate(`/page/${page.id}`)}
                />
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
