import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import AppShell from '@/components/layout/AppShell';
import LoginPage from '@/pages/LoginPage';
import RegisterPage from '@/pages/RegisterPage';
import WorkspacePage from '@/pages/WorkspacePage';
import NoteEditorPage from '@/pages/NoteEditorPage';
import TrashPage from '@/pages/TrashPage';
import TagsPage from '@/pages/TagsPage';
import DashboardPage from '@/pages/DashboardPage';
import DecksListPage from '@/pages/DecksListPage';
import DeckDetailPage from '@/pages/DeckDetailPage';
import StudySessionPage from '@/pages/StudySessionPage';
import StatsPage from '@/pages/StatsPage';
import { useAuthStore } from '@/store/authStore';

function RequireAuth({ children }) {
  const { isAuthenticated } = useAuthStore();
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }
  return children;
}

export default function App() {
  return (
    <Routes>
      {/* Public */}
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />

      {/* Study session – full screen, no shell */}
      <Route
        path="/study/:deckId"
        element={
          <RequireAuth>
            <StudySessionPage />
          </RequireAuth>
        }
      />

      {/* App shell – authenticated */}
      <Route
        path="/"
        element={
          <RequireAuth>
            <AppShell />
          </RequireAuth>
        }
      >
        <Route index element={<WorkspacePage />} />
        <Route path="page/:pageId" element={<NoteEditorPage />} />
        <Route path="trash" element={<TrashPage />} />
        <Route path="tags" element={<TagsPage />} />
        <Route path="dashboard" element={<DashboardPage />} />
        <Route path="decks" element={<DecksListPage />} />
        <Route path="decks/:deckId" element={<DeckDetailPage />} />
        <Route path="stats" element={<StatsPage />} />
      </Route>

      {/* Catch-all */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
