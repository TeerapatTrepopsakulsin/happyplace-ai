import { defineStore } from 'pinia'
import client from '../api/client'
import type {
  Alert,
  Guidelines,
  Invitation,
  PatientCardModel,
  PatientSummary,
  Session,
  Message,
} from '../types'
import axios from 'axios'

export const useDashboardStore = defineStore('dashboard', {
  state: () => ({
    patients: [] as PatientCardModel[],
    selectedPatientId: (localStorage.getItem('dashboard_selectedPatientId') || null) as
      | string
      | null,
    alerts: [] as Alert[],
    loading: false,
    error: null as string | null,
    summary: null as PatientSummary | null,
    guidelines: JSON.parse(
      localStorage.getItem('dashboard_guidelines') || 'null',
    ) as Guidelines | null,
    invitations: [] as Invitation[],
    emotionHistory: [] as Array<{
      snapshot_at: string
      dominant_emotion: string
      average_score: number
    }>,
    progress: [] as Array<{
      summary_date: string
      session_count: number
      avg_emotion_score: number | null
      dominant_emotion: string | null
      danger_event_count: number
      total_messages: number
    }>,
    sessions: [] as Session[],
    selectedSessionId: null as string | null,
    messages: [] as Message[],
  }),
  getters: {
    selectedPatient(state) {
      return state.patients.find((p) => p.patient_id === state.selectedPatientId) || null
    },
    hasSelection(state) {
      return !!state.selectedPatientId
    },
  },
  actions: {
    async fetchPatients() {
      this.loading = true
      this.error = null
      try {
        const res = await client.get('/dashboard/patients')
        this.patients = res.data
      } catch (err: unknown) {
        if (axios.isAxiosError(err)) {
          this.error = err.response?.data?.detail || 'Failed to fetch patients'
        } else {
          this.error = 'An unexpected error occurred'
        }
      } finally {
        this.loading = false
      }
    },
    selectPatient(id: string) {
      this.selectedPatientId = id
      localStorage.setItem('dashboard_selectedPatientId', id)
      this.summary = null
      this.guidelines = null
    },
    clearSelection() {
      this.selectedPatientId = null
      localStorage.removeItem('dashboard_selectedPatientId')
      this.summary = null
      this.guidelines = null
    },
    async fetchAlerts() {
      this.loading = true
      this.error = null
      try {
        const res = await client.get('/dashboard/alerts')
        this.alerts = res.data
      } catch (err: unknown) {
        if (axios.isAxiosError(err)) {
          this.error = err.response?.data?.detail || 'Failed to fetch alerts'
        } else {
          this.error = 'An unexpected error occurred'
        }
      } finally {
        this.loading = false
      }
    },
    async resolveAlert(id: string) {
      this.loading = true
      this.error = null
      try {
        await client.patch(`/dashboard/alerts/${id}`)
        this.alerts = this.alerts.filter((a) => a.id !== id)
      } catch (err: unknown) {
        if (axios.isAxiosError(err)) {
          this.error = err.response?.data?.detail || 'Failed to resolve alert'
        } else {
          this.error = 'An unexpected error occurred'
        }
      } finally {
        this.loading = false
      }
    },
    async fetchSummary(patientId: string) {
      if (!patientId) return
      this.loading = true
      this.error = null
      try {
        const res = await client.get(`/dashboard/patients/${patientId}/summary`)
        this.summary = res.data
      } catch (err: unknown) {
        if (axios.isAxiosError(err)) {
          this.error = err.response?.data?.detail || 'Failed to fetch patient summary'
        } else {
          this.error = 'An unexpected error occurred'
        }
      } finally {
        this.loading = false
      }
    },
    async fetchEmotionHistory(patientId: string) {
      if (!patientId) return
      this.loading = true
      this.error = null
      try {
        const res = await client.get(`/patients/${patientId}/emotion-history`)
        this.emotionHistory = res.data
      } catch (err: unknown) {
        if (axios.isAxiosError(err)) {
          this.error = err.response?.data?.detail || 'Failed to fetch emotion history'
        } else {
          this.error = 'An unexpected error occurred'
        }
      } finally {
        this.loading = false
      }
    },
    async fetchProgress(patientId: string) {
      if (!patientId) return
      this.loading = true
      this.error = null
      try {
        const res = await client.get(`/patients/${patientId}/progress`)
        this.progress = res.data
      } catch (err: unknown) {
        if (axios.isAxiosError(err)) {
          this.error = err.response?.data?.detail || 'Failed to fetch progress data'
        } else {
          this.error = 'An unexpected error occurred'
        }
      } finally {
        this.loading = false
      }
    },
    async fetchGuidelines(patientId: string) {
      if (!patientId) return
      this.loading = true
      this.error = null
      try {
        const res = await client.get(`/guidelines/${patientId}`)
        this.guidelines = res.data
        localStorage.setItem('dashboard_guidelines', JSON.stringify(this.guidelines))
      } catch (err: unknown) {
        if (axios.isAxiosError(err)) {
          if (err.response?.status === 404) {
            this.guidelines = {
              response_tone: '',
              coping_strategies: '',
              behavioral_boundaries: '',
              sensitive_topics: [],
              updated_at: new Date().toISOString(),
            }
            localStorage.removeItem('dashboard_guidelines')
          } else {
            this.error = err.response?.data?.detail || 'Failed to fetch guidelines'
          }
        }
      } finally {
        this.loading = false
      }
    },
    async updateGuidelines(patientId: string, payload: Guidelines) {
      if (!patientId) return
      this.loading = true
      this.error = null
      try {
        const res = await client.put(`/guidelines/${patientId}`, payload)
        this.guidelines = res.data
        localStorage.setItem('dashboard_guidelines', JSON.stringify(this.guidelines))
      } catch (err: unknown) {
        if (axios.isAxiosError(err)) {
          this.error = err.response?.data?.detail || 'Failed to update guidelines'
        } else {
          this.error = 'An unexpected error occurred'
        }
      } finally {
        this.loading = false
      }
    },
    async fetchSessions(patientId: string) {
      if (!patientId) return
      this.loading = true
      this.error = null
      try {
        const res = await client.get(`/chat/patients/${patientId}/sessions`)
        this.sessions = res.data
      } catch (err: unknown) {
        if (axios.isAxiosError(err)) {
          this.error = err.response?.data?.detail || 'Failed to fetch sessions'
        } else {
          this.error = 'An unexpected error occurred'
        }
      } finally {
        this.loading = false
      }
    },
    async selectSession(sessionId: string) {
      this.selectedSessionId = sessionId
      this.messages = []
      await this.fetchMessages(sessionId)
    },
    async fetchMessages(sessionId: string) {
      if (!sessionId) return
      this.loading = true
      this.error = null
      try {
        const res = await client.get(`/chat/sessions/${sessionId}/messages`)
        this.messages = res.data
      } catch (err: unknown) {
        if (axios.isAxiosError(err)) {
          this.error = err.response?.data?.detail || 'Failed to fetch messages'
        } else {
          this.error = 'An unexpected error occurred'
        }
      } finally {
        this.loading = false
      }
    },
    async fetchInvitations() {
      this.loading = true
      this.error = null
      try {
        const res = await client.get('/invitations')
        this.invitations = res.data
      } catch (err: unknown) {
        if (axios.isAxiosError(err)) {
          this.error = err.response?.data?.detail || 'Failed to fetch invitations'
        } else {
          this.error = 'An unexpected error occurred'
        }
      } finally {
        this.loading = false
      }
    },
    async invite(email: string) {
      this.loading = true
      this.error = null
      try {
        const res = await client.post('/invitations', { invitee_email: email })
        this.invitations.push(res.data)
      } catch (err: unknown) {
        if (axios.isAxiosError(err)) {
          this.error = err.response?.data?.detail || 'Failed to send invite'
        } else {
          this.error = 'An unexpected error occurred'
        }
        throw err
      } finally {
        this.loading = false
      }
    },
    async revokeInvitation(id: string) {
      this.loading = true
      this.error = null
      try {
        await client.delete(`/invitations/${id}`)
        this.invitations = this.invitations.filter((inv) => inv.id !== id)
      } catch (err: unknown) {
        if (axios.isAxiosError(err)) {
          this.error = err.response?.data?.detail || 'Failed to revoke invitation'
        } else {
          this.error = 'An unexpected error occurred'
        }
        throw err
      } finally {
        this.loading = false
      }
    },
  },
})
