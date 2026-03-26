import { defineStore } from 'pinia'
import client from '../api/client'
import type { Message, Session } from '../types'

interface State {
  sessions: Session[]
  activeSessionId: string | null
  messages: Message[]
  loading: boolean
  error: string | null
}

export const useChatStore = defineStore('chat', {
  state: (): State => ({
    sessions: [],
    activeSessionId: null,
    messages: [],
    loading: false,
    error: null,
  }),
  actions: {
    async fetchSessions() {
      this.loading = true
      this.error = null
      try {
        const res = await client.get('/chat/sessions')
        this.sessions = res.data
        return this.sessions
      } catch (err: any) {
        this.error = err.response?.data?.detail || 'Failed to fetch sessions'
      } finally {
        this.loading = false
      }
    },
    async createSession() {
      this.loading = true
      this.error = null
      try {
        const res = await client.post('/chat/sessions', {})
        this.sessions.unshift(res.data)
        this.activeSessionId = res.data.id
        this.messages = []
        return res.data
      } catch (err: any) {
        this.error = err.response?.data?.detail || 'Failed to create session'
      } finally {
        this.loading = false
      }
    },
    async selectSession(id: string) {
      this.activeSessionId = id
      this.loading = true
      this.error = null
      try {
        const res = await client.get(`/chat/sessions/${id}/messages`)
        this.messages = res.data
        return this.messages
      } catch (err: any) {
        this.error = err.response?.data?.detail || 'Failed to fetch messages'
      } finally {
        this.loading = false
      }
    },
    async sendMessage(content: string) {
      if (!this.activeSessionId) return
      const userMessage: Message = {
        id: `temp-${Date.now()}`,
        role: 'user',
        content,
        created_at: new Date().toISOString(),
      }
      this.messages.push(userMessage)
      this.loading = true

      try {
        const res = await client.post(`/chat/sessions/${this.activeSessionId}/messages`, { content })
        if (res.data?.assistant_message) {
          this.messages.push(res.data.assistant_message)
        }
      } catch (err: any) {
        this.messages = this.messages.filter((m) => m.id !== userMessage.id)
        this.error = err.response?.data?.detail || 'Failed to send message'
      } finally {
        this.loading = false
      }
    },
  },
})
