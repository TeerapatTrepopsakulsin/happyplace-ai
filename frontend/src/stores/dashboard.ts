import { defineStore } from 'pinia'
import client from '../api/client'
import type { Alert, Guidelines, Invitation, PatientCardModel, PatientSummary, Session, Message } from '../types'

interface State {
  patients: PatientCardModel[]
  selectedPatientId: string | null
  alerts: Alert[]
  loading: boolean
  error: string | null
  summary: PatientSummary | null
  guidelines: Guidelines | null
  invitations: Invitation[]
  emotionHistory: Array<{ snapshot_at: string; dominant_emotion: string; average_score: number }>
  progress: Array<{ metric_date: string; session_count: number; avg_emotion_score?: number; dominant_emotion?: string; danger_event_count?: number }>
}

export const useDashboardStore = defineStore('dashboard', {
  state: (): State => ({
    patients: [],
    selectedPatientId: null,
    alerts: [],
    loading: false,
    error: null,
    summary: null,
    guidelines: null,
    invitations: [],
    emotionHistory: [],
    progress: [],
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
      } catch (err: any) {
        this.error = err.response?.data?.detail || 'Failed to fetch patients'
      } finally {
        this.loading = false
      }
    },
    selectPatient(id: string) {
      this.selectedPatientId = id
      this.summary = null
      this.guidelines = null
    },
    clearSelection() {
      this.selectedPatientId = null
      this.summary = null
      this.guidelines = null
    },
    async fetchAlerts() {
      this.loading = true
      this.error = null
      try {
        const res = await client.get('/dashboard/alerts')
        this.alerts = res.data
      } catch (err: any) {
        this.error = err.response?.data?.detail || 'Failed to fetch alerts'
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
      } catch (err: any) {
        this.error = err.response?.data?.detail || 'Failed to resolve alert'
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
      } catch (err: any) {
        this.error = err.response?.data?.detail || 'Failed to fetch patient summary'
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
      } catch (err: any) {
        this.error = err.response?.data?.detail || 'Failed to fetch emotion history'
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
      } catch (err: any) {
        this.error = err.response?.data?.detail || 'Failed to fetch progress data'
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
      } catch (err: any) {
        if (err.response?.status === 404) {
          this.guidelines = null
        } else {
          this.error = err.response?.data?.detail || 'Failed to fetch guidelines'
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
      } catch (err: any) {
        this.error = err.response?.data?.detail || 'Failed to update guidelines'
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
      } catch (err: any) {
        this.error = err.response?.data?.detail || 'Failed to fetch invitations'
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
      } catch (err: any) {
        this.error = err.response?.data?.detail || 'Failed to send invite'
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
      } catch (err: any) {
        this.error = err.response?.data?.detail || 'Failed to revoke invitation'
      } finally {
        this.loading = false
      }
    },
  },
})
