import React, { useState, useEffect } from 'react';
import { NavLink, useNavigate, useLocation } from 'react-router-dom';
import {
  Plus,
  ChevronRight,
  ChevronDown,
  Star,
  Trash2,
  Tag,
  LayoutDashboard,
  BookOpen,
  BarChart2,
  Settings,
  LogOut,
  FileText,
  Layers,
} from 'lucide-react';
import { useAuthStore } from '@/store/authStore';
import { useWorkspaceStore } from '@/store/workspaceStore';
import { createPage } from '@/api/workspaces';
import { buildPageTree, truncate } from '@/utils/helpers';
import toast from 'react-hot-toast';

function PageTreeNode({ node, depth = 0 }) {
  const [expanded, setExpanded] = useState(false);
  const navigate = useNavigate();
  const hasChildren = node.children && node.children.length > 0;

  return (
    <div>
      <div
        className="flex items-center gap-1 group cursor-pointer rounded-md px-2 py-1.5 hover:bg-white/10 transition-colors"
        style={{ paddingLeft: `${(depth + 1) * 12}px` }}
      >
        <button
          onClick={() => setExpanded((v) => !v)}
          className="flex-shrink-0 w-4 h-4 flex items-center justify-center text-gray-400"
        >
          {hasChildren ? (
            expanded ? (
              <ChevronDown size={12} />
            ) : (
              <ChevronRight size={12} />
            )
          ) : (
            <span className="w-3" />
          )}
        </button>
        <button
          onClick={() => navigate(`/page/${node.id}`)}
          className="flex-1 flex items-center gap-1.5 text-left min-w-0"
        >
          <span className="text-sm flex-shrink-0">{node.icon || '📄'}</span>
          <span className="text-xs text-sidebar-text truncate">
            {truncate(node.title || 'Untitled', 28)}
          </span>
        </button>
      </div>
      {expanded && hasChildren && (
        <div>
          {node.children.map((child) => (
            <PageTreeNode key={child.id} node={child} depth={depth + 1} />
          ))}
        </div>
      )}
    </div>
  );
}

export default function Sidebar() {
  const navigate = useNavigate();
  const location = useLocation();
  const { user, logout } = useAuthStore();
  const {
    workspaces,
    activeWorkspaceId,
    pages,
    fetchPages,
    fetchFavourites,
    favourites,
    setActiveWorkspace,
    addPage,
  } = useWorkspaceStore();

  const [showWorkspacePicker, setShowWorkspacePicker] = useState(false);
  const [isCreatingPage, setIsCreatingPage] = useState(false);

  const activeWorkspace = workspaces.find((w) => w.id === activeWorkspaceId);
  const pageTree = buildPageTree(pages);

  useEffect(() => {
    if (activeWorkspaceId) {
      fetchPages(activeWorkspaceId);
      fetchFavourites(activeWorkspaceId);
    }
  }, [activeWorkspaceId]);

  const handleNewPage = async () => {
    if (!activeWorkspaceId || isCreatingPage) return;
    setIsCreatingPage(true);
    try {
      const res = await createPage(activeWorkspaceId, { title: 'Untitled' });
      const page = res.data.page;
      addPage(page.to_tree_dict ? page.to_tree_dict() : page);
      navigate(`/page/${page.id}`);
    } catch {
      toast.error('Failed to create page');
    } finally {
      setIsCreatingPage(false);
    }
  };

  const handleLogout = async () => {
    try {
      const { logout: apiLogout } = await import('@/api/auth');
      await apiLogout();
    } catch {}
    logout();
    navigate('/login');
  };

  const navItem = (to, Icon, label) => (
    <NavLink
      to={to}
      className={({ isActive }) =>
        `flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm transition-colors ${
          isActive
            ? 'bg-white/15 text-white font-medium'
            : 'text-sidebar-text hover:bg-white/10 hover:text-white'
        }`
      }
    >
      <Icon size={16} />
      <span>{label}</span>
    </NavLink>
  );

  return (
    <aside className="w-64 flex-shrink-0 bg-[#1a1a2e] flex flex-col h-full overflow-hidden">
      {/* Workspace selector */}
      <div className="px-3 pt-4 pb-2">
        <button
          onClick={() => setShowWorkspacePicker((v) => !v)}
          className="w-full flex items-center gap-2 px-3 py-2.5 rounded-xl bg-white/10 hover:bg-white/15 transition-colors"
        >
          <span className="text-lg">{activeWorkspace?.icon || '📓'}</span>
          <span className="flex-1 text-sm font-semibold text-white text-left truncate">
            {activeWorkspace?.name || 'Select workspace'}
          </span>
          <ChevronDown size={14} className="text-gray-400 flex-shrink-0" />
        </button>

        {showWorkspacePicker && (
          <div className="mt-1 bg-[#0f3460] rounded-xl overflow-hidden shadow-lg border border-white/10">
            {workspaces.map((ws) => (
              <button
                key={ws.id}
                onClick={() => {
                  setActiveWorkspace(ws.id);
                  setShowWorkspacePicker(false);
                }}
                className={`w-full flex items-center gap-2 px-3 py-2.5 text-sm hover:bg-white/10 transition-colors text-left ${
                  ws.id === activeWorkspaceId ? 'text-white' : 'text-sidebar-text'
                }`}
              >
                <span>{ws.icon}</span>
                <span className="truncate">{ws.name}</span>
              </button>
            ))}
            <button
              onClick={() => {
                navigate('/workspace/new');
                setShowWorkspacePicker(false);
              }}
              className="w-full flex items-center gap-2 px-3 py-2.5 text-sm text-indigo-400 hover:bg-white/10 transition-colors border-t border-white/10"
            >
              <Plus size={14} />
              New workspace
            </button>
          </div>
        )}
      </div>

      {/* Nav */}
      <nav className="px-3 py-2 space-y-1">
        {navItem('/dashboard', LayoutDashboard, 'Dashboard')}
        {navItem('/decks', BookOpen, 'Flashcard Decks')}
        {navItem('/stats', BarChart2, 'Statistics')}
      </nav>

      <div className="mx-3 my-1 border-t border-white/10" />

      {/* Pages section */}
      <div className="flex items-center justify-between px-3 py-2">
        <span className="text-xs font-semibold text-gray-500 uppercase tracking-wider">
          Pages
        </span>
        <button
          onClick={handleNewPage}
          disabled={isCreatingPage || !activeWorkspaceId}
          className="p-1 rounded-md hover:bg-white/10 text-gray-400 hover:text-white transition-colors disabled:opacity-40"
          title="New page"
        >
          <Plus size={14} />
        </button>
      </div>

      {/* Favourites */}
      {favourites.length > 0 && (
        <div className="px-3 mb-1">
          <div className="flex items-center gap-1.5 px-2 py-1 text-xs text-gray-500">
            <Star size={11} />
            <span>Favourites</span>
          </div>
          {favourites.map((p) => (
            <NavLink
              key={p.id}
              to={`/page/${p.id}`}
              className={({ isActive }) =>
                `flex items-center gap-1.5 px-2 py-1.5 rounded-md text-xs transition-colors truncate ${
                  isActive ? 'bg-white/15 text-white' : 'text-sidebar-text hover:bg-white/10'
                }`
              }
            >
              <span>{p.icon || '📄'}</span>
              <span className="truncate">{truncate(p.title || 'Untitled', 24)}</span>
            </NavLink>
          ))}
        </div>
      )}

      {/* Pages tree */}
      <div className="flex-1 overflow-y-auto sidebar-scrollbar px-2 pb-2">
        {pageTree.length === 0 && (
          <div className="px-4 py-4 text-center text-xs text-gray-600">
            No pages yet
          </div>
        )}
        {pageTree.map((node) => (
          <PageTreeNode key={node.id} node={node} />
        ))}
      </div>

      <div className="mx-3 border-t border-white/10" />

      {/* Bottom nav */}
      <nav className="px-3 py-2 space-y-1">
        {navItem('/tags', Tag, 'Tags')}
        {navItem('/trash', Trash2, 'Trash')}
      </nav>

      {/* User */}
      <div className="px-3 pb-4 pt-2 flex items-center gap-2">
        <div className="w-7 h-7 rounded-full bg-indigo-600 flex items-center justify-center text-white text-xs font-bold flex-shrink-0">
          {user?.name?.charAt(0)?.toUpperCase() || 'U'}
        </div>
        <div className="flex-1 min-w-0">
          <div className="text-xs font-medium text-white truncate">{user?.name}</div>
          <div className="text-xs text-gray-500 truncate">{user?.email}</div>
        </div>
        <button
          onClick={handleLogout}
          className="p-1 rounded hover:bg-white/10 text-gray-500 hover:text-white transition-colors flex-shrink-0"
          title="Sign out"
        >
          <LogOut size={14} />
        </button>
      </div>
    </aside>
  );
}
