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
    sessions: JSON.parse(localStorage.getItem('chat_sessions') || '[]'),
    activeSessionId: localStorage.getItem('chat_activeSessionId'),
    messages: JSON.parse(localStorage.getItem('chat_messages') || '[]'),
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
        localStorage.setItem('chat_sessions', JSON.stringify(this.sessions))
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
        localStorage.setItem('chat_sessions', JSON.stringify(this.sessions))
        this.activeSessionId = res.data.id
        localStorage.setItem('chat_activeSessionId', res.data.id)
        this.messages = []
        localStorage.setItem('chat_messages', JSON.stringify(this.messages))
        return res.data
      } catch (err: any) {
        this.error = err.response?.data?.detail || 'Failed to create session'
      } finally {
        this.loading = false
      }
    },
    async selectSession(id: string) {
      this.activeSessionId = id
      localStorage.setItem('chat_activeSessionId', id)
      this.loading = true
      this.error = null
      try {
        const res = await client.get(`/chat/sessions/${id}/messages`)
        this.messages = res.data
        localStorage.setItem('chat_messages', JSON.stringify(this.messages))
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
        sender: 'user',
        content,
        created_at: new Date().toISOString(),
      }
      const tempId = userMessage.id
      this.messages.push(userMessage)
      this.loading = true

      try {
        const res = await client.post(`/chat/sessions/${this.activeSessionId}/messages`, { content })
        if (res.data?.user_message && res.data?.assistant_message) {
          // Replace temp message with actual message from server
          this.messages = this.messages.filter((m) => m.id !== tempId)
          this.messages.push(res.data.user_message)
          this.messages.push(res.data.assistant_message)
        }
        localStorage.setItem('chat_messages', JSON.stringify(this.messages))
      } catch (err: any) {
        this.messages = this.messages.filter((m) => m.id !== tempId)
        this.error = err.response?.data?.detail || 'Failed to send message'
      } finally {
        this.loading = false
      }
    },
    async renameSession(id: string, title: string) {
      this.loading = true
      this.error = null
      try {
        const res = await client.patch(`/chat/sessions/${id}`, { title })
        const index = this.sessions.findIndex((s) => s.id === id)
        if (index !== -1) {
          this.sessions[index] = res.data
        }
        localStorage.setItem('chat_sessions', JSON.stringify(this.sessions))
        return res.data
      } catch (err: any) {
        this.error = err.response?.data?.detail || 'Failed to rename session'
      } finally {
        this.loading = false
      }
    },
    async deleteSession(id: string) {
      this.loading = true
      this.error = null
      try {
        await client.delete(`/chat/sessions/${id}`)
        this.sessions = this.sessions.filter((s) => s.id !== id)
        localStorage.setItem('chat_sessions', JSON.stringify(this.sessions))
        if (this.activeSessionId === id) {
          if (this.sessions.length > 0) {
            await this.selectSession(this.sessions[0]!.id)
          } else {
            this.activeSessionId = null
            localStorage.removeItem('chat_activeSessionId')
            this.messages = []
            localStorage.setItem('chat_messages', '[]')
          }
        }
      } catch (err: any) {
        this.error = err.response?.data?.detail || 'Failed to delete session'
      } finally {
        this.loading = false
      }
    },
  },
})
