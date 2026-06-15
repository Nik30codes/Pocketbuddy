import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  agent?: string
  suggestions?: string[]
  actions?: string[]
  image?: string
  timestamp: number
}

interface ChatState {
  messages: Message[]
  addMessage: (msg: Omit<Message, 'timestamp'>) => void
  clearMessages: () => void
}

export const useChatStore = create<ChatState>()(
  persist(
    (set) => ({
      messages: [
        {
          id: '0',
          role: 'assistant',
          content:
            "Hey! I'm your PocketBuddy AI companion. I can help you with finances, wellness, routines, or just chat about how you're doing. What's on your mind?",
          agent: 'life_coach',
          suggestions: [
            "How's my budget looking?",
            "I'm feeling stressed today",
            "Generate a daily routine",
          ],
          timestamp: Date.now(),
        },
      ],
      addMessage: (msg) =>
        set((state) => ({
          messages: [...state.messages, { ...msg, timestamp: Date.now() }],
        })),
      clearMessages: () =>
        set({
          messages: [
            {
              id: '0',
              role: 'assistant',
              content:
                "Hey! I'm your PocketBuddy AI companion. I can help you with finances, wellness, routines, or just chat about how you're doing. What's on your mind?",
              agent: 'life_coach',
              suggestions: [
                "How's my budget looking?",
                "I'm feeling stressed today",
                "Generate a daily routine",
              ],
              timestamp: Date.now(),
            },
          ],
        }),
    }),
    {
      name: 'pocketbuddy-chat',
    }
  )
)
