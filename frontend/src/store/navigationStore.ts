import { create } from 'zustand'

export type PanelKey =
  'config' | 'mcp' | 'library' | 'dashboard' | 'canvas' | 'activity' | 'comparator' | 'filesystem'

interface NavigationState {
  activePanel: PanelKey
  selectedProjectPath: string | null
  setActivePanel: (panel: PanelKey) => void
  setSelectedProjectPath: (path: string | null) => void
}

export const useNavigationStore = create<NavigationState>((set) => ({
  activePanel: 'config',
  selectedProjectPath: null,
  setActivePanel: (panel) => set({ activePanel: panel }),
  setSelectedProjectPath: (path) => set({ selectedProjectPath: path }),
}))
