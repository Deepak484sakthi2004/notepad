import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export const useAuthStore = create(
  persist(
    (set, get) => ({
      user: null,
      accessToken: null,
      isAuthenticated: false,

      setUser: (user) => set({ user, isAuthenticated: !!user }),
      setAccessToken: (token) => set({ accessToken: token }),

      login: (user, token) => {
        set({ user, accessToken: token, isAuthenticated: true });
      },

      logout: () => {
        set({ user: null, accessToken: null, isAuthenticated: false });
      },

      updateUser: (updates) => {
        const current = get().user;
        if (current) {
          set({ user: { ...current, ...updates } });
        }
      },
    }),
    {
      name: 'notespace-auth',
      partialize: (state) => ({
        user: state.user,
        isAuthenticated: state.isAuthenticated,
        // Do NOT persist accessToken – store in memory only for security
      }),
    }
  )
);
