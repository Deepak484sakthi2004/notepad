import { create } from 'zustand';
import * as flashcardApi from '@/api/flashcards';

export const useFlashcardStore = create((set, get) => ({
  decks: [],
  currentDeck: null,
  currentCards: [],
  dueCards: [],
  stats: null,
  history: [],
  isLoading: false,

  // Study session state
  session: null,
  sessionCards: [],
  currentCardIndex: 0,
  isFlipped: false,
  sessionStats: { reviewed: 0, correct: 0 },

  fetchDecks: async () => {
    set({ isLoading: true });
    try {
      const res = await flashcardApi.getDecks();
      set({ decks: res.data.decks });
      return res.data.decks;
    } finally {
      set({ isLoading: false });
    }
  },

  fetchDeck: async (id) => {
    const res = await flashcardApi.getDeck(id);
    set({ currentDeck: res.data.deck });
    return res.data.deck;
  },

  fetchCards: async (deckId) => {
    const res = await flashcardApi.getDeckCards(deckId);
    set({ currentCards: res.data.cards });
    return res.data.cards;
  },

  fetchDueCards: async (deckId) => {
    const res = deckId
      ? await flashcardApi.getDeckDueCards(deckId)
      : await flashcardApi.getDueCards();
    set({ dueCards: res.data.cards });
    return res.data.cards;
  },

  fetchStats: async () => {
    const res = await flashcardApi.getStatsOverview();
    set({ stats: res.data });
    return res.data;
  },

  fetchHistory: async (days) => {
    const res = await flashcardApi.getStatsHistory(days);
    set({ history: res.data.history });
    return res.data.history;
  },

  // Study session management
  startStudySession: async (deckId) => {
    const res = await flashcardApi.startSession({ deck_id: deckId });
    const session = res.data.session;
    const dueRes = await flashcardApi.getDeckDueCards(deckId);
    const cards = dueRes.data.cards;

    set({
      session,
      sessionCards: cards,
      currentCardIndex: 0,
      isFlipped: false,
      sessionStats: { reviewed: 0, correct: 0 },
    });
    return { session, cards };
  },

  flipCard: () => set((s) => ({ isFlipped: !s.isFlipped })),

  rateCard: async (quality) => {
    const { session, sessionCards, currentCardIndex, sessionStats } = get();
    const card = sessionCards[currentCardIndex];
    if (!card) return;

    await flashcardApi.submitReview({
      card_id: card.id,
      quality,
      session_id: session?.id,
    });

    const newStats = {
      reviewed: sessionStats.reviewed + 1,
      correct: quality >= 3 ? sessionStats.correct + 1 : sessionStats.correct,
    };

    const nextIndex = currentCardIndex + 1;
    set({
      currentCardIndex: nextIndex,
      isFlipped: false,
      sessionStats: newStats,
    });

    return nextIndex >= sessionCards.length;
  },

  endStudySession: async () => {
    const { session, sessionStats } = get();
    if (session) {
      await flashcardApi.endSession(session.id, {
        cards_reviewed: sessionStats.reviewed,
        cards_correct: sessionStats.correct,
      });
    }
    set({ session: null, sessionCards: [], currentCardIndex: 0 });
  },

  addDeck: (deck) => set((s) => ({ decks: [deck, ...s.decks] })),
  removeDeck: (id) =>
    set((s) => ({ decks: s.decks.filter((d) => d.id !== id) })),
  updateDeckInList: (id, updates) =>
    set((s) => ({
      decks: s.decks.map((d) => (d.id === id ? { ...d, ...updates } : d)),
    })),
}));
