
import { create } from 'zustand';
import type { Project, Conversation, Message, Workplan, Task, ProcessingIndicator } from '@/types';

interface AppState {
  currentProject: Project | null;
  setCurrentProject: (project: Project | null) => void;

  currentConversation: Conversation | null;
  setCurrentConversation: (conversation: Conversation | null) => void;

  messages: Message[];
  addMessage: (message: Message) => void;
  setMessages: (messages: Message[]) => void;

  workplans: Workplan[];
  setWorkplans: (workplans: Workplan[]) => void;

  tasks: Task[];
  setTasks: (tasks: Task[]) => void;

  processingIndicators: ProcessingIndicator[];
  addProcessingIndicator: (indicator: ProcessingIndicator) => void;
  updateProcessingIndicator: (stage: string, updates: Partial<ProcessingIndicator>) => void;
  clearProcessingIndicators: () => void;

  isLoading: boolean;
  setIsLoading: (loading: boolean) => void;

  error: string | null;
  setError: (error: string | null) => void;
}

export const useAppStore = create<AppState>((set) => ({
  currentProject: null,
  setCurrentProject: (project) => set({ currentProject: project }),

  currentConversation: null,
  setCurrentConversation: (conversation) => set({ currentConversation: conversation }),

  messages: [],
  addMessage: (message) =>
    set((state) => ({
      messages: [...state.messages, message],
    })),
  setMessages: (messages) => set({ messages }),

  workplans: [],
  setWorkplans: (workplans) => set({ workplans }),

  tasks: [],
  setTasks: (tasks) => set({ tasks }),

  processingIndicators: [],
  addProcessingIndicator: (indicator) =>
    set((state) => ({
      processingIndicators: [...state.processingIndicators, indicator],
    })),
  updateProcessingIndicator: (stage, updates) =>
    set((state) => ({
      processingIndicators: state.processingIndicators.map((ind) =>
        ind.stage === stage ? { ...ind, ...updates } : ind
      ),
    })),
  clearProcessingIndicators: () => set({ processingIndicators: [] }),

  isLoading: false,
  setIsLoading: (loading) => set({ isLoading: loading }),

  error: null,
  setError: (error) => set({ error }),
}));
