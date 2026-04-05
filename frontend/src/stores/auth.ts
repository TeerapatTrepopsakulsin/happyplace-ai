import { defineStore } from 'pinia'
import client from '../api/client'
import router from '../router'
import type { User } from '../types'
import axios from 'axios'

function decodeJwt(token: string): User | null {
  try {
    const payload = token.split('.')[1]
    if (!payload) return null
    const decoded = atob(payload.replace(/-/g, '+').replace(/_/g, '/'))
    const parsed = JSON.parse(decodeURIComponent(escape(decoded)))
    return {
      id: parsed.sub || parsed.id,
      email: parsed.email,
      role: parsed.role,
      display_name: parsed.display_name || parsed.name || '',
    }
  } catch {
    return null
  }
}

interface State {
  token: string | null
  user: User | null
  authError: string | null
}

export const useAuthStore = defineStore('auth', {
  state: (): State => ({
    token: null,
    user: null,
    authError: null,
  }),
  getters: {
    isAuthenticated(state): boolean {
      return !!state.token && !!state.user
    },
    isRegular(state): boolean {
      return state.user?.role === 'regular'
    },
    isTherapist(state): boolean {
      return state.user?.role === 'therapist'
    },
    isGuardian(state): boolean {
      return state.user?.role === 'guardian'
    },
  },
  actions: {
    async login(email: string, password: string) {
      this.authError = null
      try {
        const res = await client.post('/auth/login', { email, password })
        this.token = res.data.access_token
        if (!this.token) throw new Error('No token received')
        const parsed = decodeJwt(this.token)
        if (!parsed) throw new Error('Invalid token')
        this.user = parsed
        const postLoginRoute = this.user.role === 'regular' ? '/chat' : '/dashboard'
        await router.push(postLoginRoute)
      } catch (err: unknown) {
        if (axios.isAxiosError(err)) {
          if (err.response?.status === 401) {
            this.authError = 'Invalid credentials'
          } else {
            this.authError = err.response?.data?.detail || 'Login failed'
          }
        } else {
          this.authError = 'An unexpected error occurred'
        }
        this.token = null
        this.user = null
        throw err
      }
    },
    async register(email: string, password: string, display_name: string, role: string) {
      this.authError = null
      try {
        await client.post('/auth/register', { email, password, display_name, role })
        await router.push('/login')
      } catch (err: unknown) {
        if (axios.isAxiosError(err)) {
          this.authError = err.response?.data?.detail || 'Registration failed'
        } else {
          this.authError = 'An unexpected error occurred'
        }
        throw err
      }
    },
    logout() {
      this.token = null
      this.user = null
      this.authError = null
      router.push('/login')
    },
  },
})
