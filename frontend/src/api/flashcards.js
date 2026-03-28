import apiClient from './client';

// Decks
export const getDecks = () => apiClient.get('/api/flashcards/decks');
export const createDeck = (data) => apiClient.post('/api/flashcards/decks', data);
export const getDeck = (id) => apiClient.get(`/api/flashcards/decks/${id}`);
export const updateDeck = (id, data) => apiClient.put(`/api/flashcards/decks/${id}`, data);
export const deleteDeck = (id) => apiClient.delete(`/api/flashcards/decks/${id}`);
export const regenerateDeck = (id, data) =>
  apiClient.post(`/api/flashcards/decks/${id}/regenerate`, data);
export const getDeckStats = (id) => apiClient.get(`/api/flashcards/decks/${id}/stats`);

// Cards
export const getDeckCards = (deckId) =>
  apiClient.get(`/api/flashcards/decks/${deckId}/cards`);
export const createCard = (deckId, data) =>
  apiClient.post(`/api/flashcards/decks/${deckId}/cards`, data);
export const updateCard = (id, data) => apiClient.put(`/api/flashcards/cards/${id}`, data);
export const deleteCard = (id) => apiClient.delete(`/api/flashcards/cards/${id}`);
export const suspendCard = (id) => apiClient.post(`/api/flashcards/cards/${id}/suspend`);
export const flagCard = (id) => apiClient.post(`/api/flashcards/cards/${id}/flag`);

// Generation
export const generateFlashcards = (data) =>
  apiClient.post('/api/flashcards/generate', data);

// Due cards
export const getDueCards = () => apiClient.get('/api/flashcards/due');
export const getDeckDueCards = (deckId) =>
  apiClient.get(`/api/flashcards/decks/${deckId}/due`);

// Reviews & sessions
export const submitReview = (data) => apiClient.post('/api/flashcards/review', data);
export const startSession = (data) => apiClient.post('/api/flashcards/sessions/start', data);
export const endSession = (id, data) =>
  apiClient.post(`/api/flashcards/sessions/${id}/end`, data);

// AI
export const askAI = (data) => apiClient.post('/api/flashcards/ask', data);

// Stats
export const getStatsOverview = () => apiClient.get('/api/flashcards/stats/overview');
export const getStatsHistory = (days = 30) =>
  apiClient.get('/api/flashcards/stats/history', { params: { days } });
