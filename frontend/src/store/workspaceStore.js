import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import * as workspaceApi from '@/api/workspaces';

export const useWorkspaceStore = create(
  persist(
    (set, get) => ({
      workspaces: [],
      activeWorkspaceId: null,
      pages: [],
      tags: [],
      favourites: [],
      isLoading: false,

      get activeWorkspace() {
        return get().workspaces.find((w) => w.id === get().activeWorkspaceId) || null;
      },

      setActiveWorkspace: (id) => set({ activeWorkspaceId: id }),

      fetchWorkspaces: async () => {
        set({ isLoading: true });
        try {
          const res = await workspaceApi.getWorkspaces();
          const workspaces = res.data.workspaces;
          set({ workspaces });
          // Auto-select first if none selected
          if (!get().activeWorkspaceId && workspaces.length > 0) {
            set({ activeWorkspaceId: workspaces[0].id });
          }
          return workspaces;
        } finally {
          set({ isLoading: false });
        }
      },

      createWorkspace: async (data) => {
        const res = await workspaceApi.createWorkspace(data);
        const workspace = res.data.workspace;
        set((state) => ({ workspaces: [...state.workspaces, workspace] }));
        return workspace;
      },

      updateWorkspace: async (id, data) => {
        const res = await workspaceApi.updateWorkspace(id, data);
        const updated = res.data.workspace;
        set((state) => ({
          workspaces: state.workspaces.map((w) => (w.id === id ? updated : w)),
        }));
        return updated;
      },

      deleteWorkspace: async (id) => {
        await workspaceApi.deleteWorkspace(id);
        set((state) => {
          const remaining = state.workspaces.filter((w) => w.id !== id);
          const newActive =
            state.activeWorkspaceId === id
              ? remaining[0]?.id || null
              : state.activeWorkspaceId;
          return { workspaces: remaining, activeWorkspaceId: newActive };
        });
      },

      fetchPages: async (workspaceId) => {
        const res = await workspaceApi.getPages(workspaceId);
        set({ pages: res.data.pages });
        return res.data.pages;
      },

      addPage: (page) => {
        set((state) => ({ pages: [...state.pages, page] }));
      },

      updatePageInList: (pageId, updates) => {
        set((state) => ({
          pages: state.pages.map((p) => (p.id === pageId ? { ...p, ...updates } : p)),
        }));
      },

      removePageFromList: (pageId) => {
        set((state) => ({
          pages: state.pages.filter((p) => p.id !== pageId),
        }));
      },

      fetchTags: async (workspaceId) => {
        const res = await workspaceApi.getTags(workspaceId);
        set({ tags: res.data.tags });
        return res.data.tags;
      },

      addTag: (tag) => {
        set((state) => ({ tags: [...state.tags, tag] }));
      },

      fetchFavourites: async (workspaceId) => {
        const res = await workspaceApi.getFavourites(workspaceId);
        set({ favourites: res.data.pages });
        return res.data.pages;
      },

      reset: () =>
        set({
          workspaces: [],
          activeWorkspaceId: null,
          pages: [],
          tags: [],
          favourites: [],
        }),
    }),
    {
      name: 'notespace-workspace',
      partialize: (state) => ({
        activeWorkspaceId: state.activeWorkspaceId,
      }),
    }
  )
);
