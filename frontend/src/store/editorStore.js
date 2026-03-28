import { create } from 'zustand';

export const useEditorStore = create((set, get) => ({
  currentPage: null,
  isSaving: false,
  saveError: null,
  lastSavedAt: null,
  showAIPanel: false,
  showFlashcardPanel: true,

  setCurrentPage: (page) => set({ currentPage: page, saveError: null }),

  updateCurrentPage: (updates) => {
    const page = get().currentPage;
    if (page) {
      set({ currentPage: { ...page, ...updates } });
    }
  },

  setSaving: (isSaving) => set({ isSaving }),
  setSaveError: (error) => set({ saveError: error }),
  setLastSavedAt: (date) => set({ lastSavedAt: date }),

  toggleAIPanel: () => set((s) => ({ showAIPanel: !s.showAIPanel })),
  toggleFlashcardPanel: () =>
    set((s) => ({ showFlashcardPanel: !s.showFlashcardPanel })),

  reset: () =>
    set({
      currentPage: null,
      isSaving: false,
      saveError: null,
      lastSavedAt: null,
      showAIPanel: false,
    }),
}));
