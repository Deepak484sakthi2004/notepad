import apiClient from './client';

export const getPage = (id) => apiClient.get(`/api/pages/${id}`);
export const updatePage = (id, data) => apiClient.put(`/api/pages/${id}`, data);
export const updatePageContent = (id, data) =>
  apiClient.put(`/api/pages/${id}/content`, data);
export const deletePage = (id) => apiClient.delete(`/api/pages/${id}`);
export const restorePage = (id) => apiClient.post(`/api/pages/${id}/restore`);
export const permanentDeletePage = (id) =>
  apiClient.delete(`/api/pages/${id}/permanent`);
export const duplicatePage = (id) => apiClient.post(`/api/pages/${id}/duplicate`);
export const movePage = (id, data) => apiClient.post(`/api/pages/${id}/move`, data);
export const exportPage = (id, format) =>
  apiClient.get(`/api/pages/${id}/export`, {
    params: { format },
    responseType: 'blob',
  });
export const addFavourite = (id) => apiClient.put(`/api/pages/${id}/favourite`);
export const removeFavourite = (id) => apiClient.delete(`/api/pages/${id}/favourite`);
export const addTag = (pageId, tagId) =>
  apiClient.post(`/api/pages/${pageId}/tags`, { tag_id: tagId });
export const removeTag = (pageId, tagId) =>
  apiClient.delete(`/api/pages/${pageId}/tags/${tagId}`);
export const uploadImage = (pageId, formData) =>
  apiClient.post(`/api/pages/${pageId}/upload-image`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
