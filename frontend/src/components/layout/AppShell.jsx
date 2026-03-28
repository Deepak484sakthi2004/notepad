import React, { useEffect } from 'react';
import { Outlet, useNavigate } from 'react-router-dom';
import Sidebar from './Sidebar';
import { useAuthStore } from '@/store/authStore';
import { useWorkspaceStore } from '@/store/workspaceStore';

export default function AppShell() {
  const navigate = useNavigate();
  const { isAuthenticated } = useAuthStore();
  const { fetchWorkspaces } = useWorkspaceStore();

  useEffect(() => {
    if (!isAuthenticated) {
      navigate('/login', { replace: true });
      return;
    }
    fetchWorkspaces().catch(() => {});
  }, [isAuthenticated]);

  if (!isAuthenticated) return null;

  return (
    <div className="flex h-screen overflow-hidden bg-white">
      <Sidebar />
      <main className="flex-1 flex flex-col overflow-hidden">
        <Outlet />
      </main>
    </div>
  );
}
