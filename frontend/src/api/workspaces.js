import apiClient from './client';

export const getWorkspaces = () => apiClient.get('/api/workspaces');
export const createWorkspace = (data) => apiClient.post('/api/workspaces', data);
export const getWorkspace = (id) => apiClient.get(`/api/workspaces/${id}`);
export const updateWorkspace = (id, data) => apiClient.put(`/api/workspaces/${id}`, data);
export const deleteWorkspace = (id) => apiClient.delete(`/api/workspaces/${id}`);

export const getPages = (workspaceId) =>
  apiClient.get(`/api/workspaces/${workspaceId}/pages`);
export const createPage = (workspaceId, data) =>
  apiClient.post(`/api/workspaces/${workspaceId}/pages`, data);

export const getTags = (workspaceId) =>
  apiClient.get(`/api/workspaces/${workspaceId}/tags`);
export const createTag = (workspaceId, data) =>
  apiClient.post(`/api/workspaces/${workspaceId}/tags`, data);

export const getFavourites = (workspaceId) =>
  apiClient.get('/api/favourites', { params: { workspace_id: workspaceId } });

export const getTrash = (workspaceId) =>
  apiClient.get('/api/trash', { params: { workspace_id: workspaceId } });
