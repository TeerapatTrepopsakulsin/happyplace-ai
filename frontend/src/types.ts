export type UserRole = 'regular' | 'therapist' | 'guardian'

export interface User {
  id: string
  email: string
  role: UserRole
  display_name: string
}

export interface Session {
  id: string
  title: string
  created_at: string
  last_active: string
}

export interface Message {
  id: string
  sender: 'user' | 'assistant'
  content: string
  emotion_label?: string | null
  emotion_score?: number | null
  danger_flag?: boolean
  created_at: string
}

export interface PatientSummary {
  mood_trend: 'improving' | 'stable' | 'declining'
  dominant_emotion_last_7d: string
  session_count_last_7d: number
  danger_events_last_7d: number
}

export interface PatientCardModel {
  patient_id: string
  display_name: string
  last_active: string
  latest_emotion: string | null
}

export interface Alert {
  id: string
  patient_id: string
  session_id: string
  message_id: string
  created_at: string
  snippet: string
}

export interface Invitation {
  id: string
  invitee_email: string
  invitee_display_name: string
  role_granted: UserRole
  created_at: string
}

export interface Guidelines {
  response_tone?: string
  coping_strategies?: string
  behavioral_boundaries?: string
  sensitive_topics?: string[]
}
