import apiClient from './client';

export const searchPages = (query, workspaceId) =>
  apiClient.get('/api/search', { params: { q: query, workspace_id: workspaceId } });
