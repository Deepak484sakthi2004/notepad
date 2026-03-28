import apiClient from './client';

export const register = (data) => apiClient.post('/api/auth/register', data);
export const login = (data) => apiClient.post('/api/auth/login', data);
export const logout = () => apiClient.post('/api/auth/logout');
export const refreshToken = () => apiClient.post('/api/auth/refresh');
export const forgotPassword = (email) =>
  apiClient.post('/api/auth/forgot-password', { email });
export const resetPassword = (data) =>
  apiClient.post('/api/auth/reset-password', data);
export const getProfile = () => apiClient.get('/api/user/profile');
export const updateProfile = (data) => apiClient.put('/api/user/profile', data);
