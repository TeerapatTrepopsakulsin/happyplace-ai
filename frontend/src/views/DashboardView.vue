<script setup lang="ts">
import { onMounted, onUnmounted, watch, computed, ref } from 'vue'
import { useDashboardStore } from '../stores/dashboard'
import { useAuthStore } from '../stores/auth'
import PatientCard from '../components/PatientCard.vue'
import PatientSummaryCard from '../components/PatientSummaryCard.vue'
import MoodChart from '../components/MoodChart.vue'
import SessionActivityChart from '../components/SessionActivityChart.vue'
import MessageActivityChart from '../components/MessageActivityChart.vue'
import DangerAlertPanel from '../components/DangerAlertPanel.vue'
import GuidelineEditor from '../components/GuidelineEditor.vue'
import type { Guidelines } from '../types'

const dashboard = useDashboardStore()
const auth = useAuthStore()
const notification = ref<{ message: string; type: 'success' | 'error' } | null>(null)
const isRefreshing = ref(false)

let refreshInterval: number | null = null
let notificationTimeout: number | null = null

onMounted(async () => {
  await dashboard.fetchPatients()
  await dashboard.fetchAlerts()
  if (dashboard.selectedPatientId) {
    dashboard.selectPatient(dashboard.selectedPatientId)
    await refreshData()
  }

  // Refresh data every 30 seconds if a patient is selected
  refreshInterval = setInterval(() => {
    if (dashboard.selectedPatientId) {
      refreshData()
    }
  }, 30000)
})

onUnmounted(() => {
  if (refreshInterval) {
    clearInterval(refreshInterval)
  }
  if (notificationTimeout) {
    clearTimeout(notificationTimeout)
  }
})

const showNotification = (message: string, type: 'success' | 'error' = 'success') => {
  notification.value = { message, type }
  if (notificationTimeout) {
    clearTimeout(notificationTimeout)
  }
  notificationTimeout = window.setTimeout(() => {
    notification.value = null
  }, 3000)
}

const selected = computed(() => dashboard.selectedPatient)

watch(
  () => dashboard.selectedPatientId,
  async (id) => {
    if (!id) return
    if (auth.isGuardian) {
      await dashboard.fetchSummary(id)
    }
    await dashboard.fetchEmotionHistory(id)
    await dashboard.fetchProgress(id)
    if (auth.isTherapist) {
      await dashboard.fetchGuidelines(id)
      await dashboard.fetchSessions(id)
    }
  },
  { immediate: true },
)

function selectPatient(id: string) {
  dashboard.selectPatient(id)
}

function clearSelection() {
  dashboard.clearSelection()
}

async function resolveAlert(alertId: string) {
  if (!alertId || alertId === 'undefined') {
    showNotification('Invalid alert ID', 'error')
    return
  }
  await dashboard.resolveAlert(alertId)
}

async function saveGuidelines(data: Guidelines) {
  if (!dashboard.selectedPatientId) return
  try {
    await dashboard.updateGuidelines(dashboard.selectedPatientId, data)
    await dashboard.fetchGuidelines(dashboard.selectedPatientId)
    // Ensure immediate update in case of shallow binding issues
    dashboard.guidelines = {
      ...dashboard.guidelines,
      ...data,
      updated_at: new Date().toISOString(),
    }
    showNotification('Guidelines saved successfully!', 'success')
  } catch {
    showNotification('Failed to save guidelines', 'error')
  }
}

async function refreshData() {
  if (!dashboard.selectedPatientId || isRefreshing.value) return
  isRefreshing.value = true
  showNotification('Refreshing data...', 'success')
  try {
    if (auth.isGuardian) {
      await dashboard.fetchSummary(dashboard.selectedPatientId)
    }
    await dashboard.fetchEmotionHistory(dashboard.selectedPatientId)
    await dashboard.fetchProgress(dashboard.selectedPatientId)
    if (auth.isTherapist) {
      await dashboard.fetchGuidelines(dashboard.selectedPatientId)
      await dashboard.fetchSessions(dashboard.selectedPatientId)
    }
    showNotification('Data refreshed successfully!', 'success')
  } catch {
    showNotification('Failed to refresh data', 'error')
  } finally {
    isRefreshing.value = false
  }
}

async function selectSession(sessionId: string) {
  await dashboard.selectSession(sessionId)
}
</script>

<template>
  <div>
    <!-- Notification toast -->
    <div
      v-if="notification"
      :class="[
        'fixed top-4 right-4 px-6 py-3 rounded-xl shadow-2xl text-white z-50 transition-all duration-300',
        notification.type === 'success'
          ? 'bg-indigo-600 shadow-indigo-500/20'
          : 'bg-red-600 shadow-red-500/20',
      ]"
    >
      {{ notification.message }}
    </div>

    <div v-if="!dashboard.hasSelection">
      <div
        v-if="dashboard.patients.length === 0"
        class="flex flex-col items-center justify-center p-12 mt-8 bg-slate-800/30 border border-slate-700 border-dashed rounded-3xl max-w-2xl mx-auto shadow-sm"
      >
        <svg
          class="w-16 h-16 text-slate-600 mb-4"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="1"
            d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z"
          ></path>
        </svg>
        <h3 class="text-xl font-bold text-slate-300 mb-2">No Profiles Found</h3>
        <p class="text-slate-500 text-center max-w-sm">
          You don't have any associated patients or guardianees yet. Please ask them to invite you.
        </p>
      </div>
      <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <PatientCard
          v-for="patient in dashboard.patients"
          :key="patient.patient_id"
          :patient="patient"
          :active="false"
          @select="selectPatient"
        />
      </div>
    </div>

    <div v-else class="space-y-6">
      <button
        @click="clearSelection"
        class="text-sm font-medium text-cyan-400 hover:text-cyan-300 transition-colors flex items-center gap-1 group"
      >
        <svg
          class="w-4 h-4 transform group-hover:-translate-x-1 transition-transform"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M10 19l-7-7m0 0l7-7m-7 7h18"
          ></path>
        </svg>
        Back to patients
      </button>

      <div
        class="bg-slate-800/80 backdrop-blur-md p-6 rounded-2xl border border-slate-700 shadow-xl flex flex-col sm:flex-row sm:items-center justify-between gap-4"
      >
        <div>
          <h2
            class="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-indigo-400 to-cyan-400"
          >
            {{ selected?.display_name }}
          </h2>
          <p class="text-sm text-slate-400 mt-1">
            Last active:
            {{ selected?.last_active ? new Date(selected.last_active).toLocaleString() : 'Never' }}
          </p>
        </div>
        <div class="flex items-center gap-4">
          <div class="text-sm text-slate-400 font-medium hidden sm:block">
            {{ new Date().toLocaleString([], { dateStyle: 'short', timeStyle: 'short' }) }}
          </div>
          <button
            @click="refreshData"
            :disabled="isRefreshing"
            class="px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm font-medium hover:bg-indigo-500 disabled:bg-slate-700 disabled:text-slate-500 disabled:cursor-not-allowed transition-colors shadow-lg shadow-indigo-500/20 flex items-center gap-2"
          >
            <svg
              :class="['w-4 h-4', isRefreshing ? 'animate-spin' : '']"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
              ></path>
            </svg>
            {{ isRefreshing ? 'Refreshing...' : 'Refresh' }}
          </button>
        </div>
      </div>

      <div v-if="auth.isGuardian">
        <PatientSummaryCard v-if="dashboard.summary" :summary="dashboard.summary" />
      </div>

      <div v-if="auth.isTherapist" class="mt-8">
        <h3 class="text-xl font-bold text-slate-200 mb-4 flex items-center gap-2">
          <svg
            class="w-6 h-6 text-indigo-400"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
            ></path>
          </svg>
          Mood & Danger
        </h3>
        <div class="grid grid-cols-1 xl:grid-cols-2 gap-6">
          <div>
            <MoodChart :progressData="dashboard.progress" />
          </div>
          <div>
            <DangerAlertPanel
              :alerts="dashboard.alerts.filter((a) => a.patient_id === dashboard.selectedPatientId)"
              @resolve="resolveAlert"
            />
          </div>
        </div>
      </div>

      <div class="mt-8">
        <h3 class="text-xl font-bold text-slate-200 mb-4 flex items-center gap-2">
          <svg class="w-6 h-6 text-cyan-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
            ></path>
          </svg>
          Usage and Chat Log
        </h3>

        <!-- Row 1: Charts -->
        <div class="grid grid-cols-1 xl:grid-cols-2 gap-6 mb-6">
          <div>
            <SessionActivityChart :progress="dashboard.progress" />
          </div>
          <div>
            <MessageActivityChart :progress="dashboard.progress" />
          </div>
        </div>

        <!-- Row 2: Sessions and Chat Log -->
        <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div class="lg:col-span-1">
            <div
              class="bg-slate-800/80 backdrop-blur-md border border-slate-700 rounded-2xl p-5 h-[400px] flex flex-col shadow-xl"
            >
              <h4
                class="font-bold text-slate-200 mb-4 px-1 pb-3 border-b border-slate-700/50 flex items-center justify-between"
              >
                Sessions
                <span
                  class="text-xs font-normal text-slate-500 bg-slate-900/50 px-2 py-1 rounded-md"
                  >{{ dashboard.sessions.length }} Total</span
                >
              </h4>
              <div
                v-if="dashboard.loading"
                class="flex-1 flex items-center justify-center text-slate-500"
              >
                <svg
                  class="w-6 h-6 animate-spin text-indigo-500"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                  ></path>
                </svg>
              </div>
              <div
                v-else-if="dashboard.sessions.length === 0"
                class="flex-1 flex items-center justify-center text-slate-500"
              >
                No sessions yet.
              </div>
              <ul
                v-else
                class="flex-1 overflow-y-auto scrollbar-thin scrollbar-thumb-slate-600 scrollbar-track-transparent space-y-2 pr-2"
              >
                <li
                  v-for="sess in dashboard.sessions"
                  :key="sess.id"
                  @click="selectSession(sess.id)"
                  :class="[
                    'cursor-pointer p-3 rounded-xl border transition-all duration-200 group',
                    dashboard.selectedSessionId === sess.id
                      ? 'bg-indigo-600/20 border-indigo-500/50 shadow-inner'
                      : 'bg-slate-900/30 border-transparent hover:bg-slate-700/50 hover:border-slate-600',
                  ]"
                >
                  <div
                    :class="[
                      'font-medium text-sm transition-colors',
                      dashboard.selectedSessionId === sess.id
                        ? 'text-indigo-300'
                        : 'text-slate-300 group-hover:text-slate-200',
                    ]"
                  >
                    {{ sess.title || 'Chat Session' }}
                  </div>
                  <div class="text-xs text-slate-500 mt-1 flex items-center gap-1">
                    <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        stroke-width="2"
                        d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
                      ></path>
                    </svg>
                    {{ sess.last_active ? new Date(sess.last_active).toLocaleString() : 'Never' }}
                  </div>
                </li>
              </ul>
            </div>
          </div>
          <div class="lg:col-span-2">
            <div
              class="bg-slate-800/80 backdrop-blur-md border border-slate-700 rounded-2xl p-5 h-[400px] flex flex-col shadow-xl"
            >
              <h4 class="font-bold text-slate-200 mb-4 px-1 pb-3 border-b border-slate-700/50">
                Chat Log
              </h4>
              <div
                v-if="!dashboard.selectedSessionId"
                class="flex-1 flex items-center justify-center text-slate-500"
              >
                Select a session to view messages.
              </div>
              <div
                v-else-if="dashboard.messages.length === 0"
                class="flex-1 flex items-center justify-center text-slate-500"
              >
                No messages in this session.
              </div>
              <div
                v-else
                class="flex-1 overflow-y-auto scrollbar-thin scrollbar-thumb-slate-600 scrollbar-track-transparent space-y-3 pr-2"
              >
                <div
                  v-for="msg in dashboard.messages"
                  :key="msg.id"
                  :class="[
                    'p-3 rounded-xl shadow-sm border border-slate-700/50 group',
                    msg.sender === 'user'
                      ? 'bg-indigo-600/20 border-indigo-500/30 ml-4'
                      : 'bg-slate-700/30 mr-4',
                  ]"
                >
                  <div
                    class="font-bold text-xs uppercase tracking-wider mb-1 flex items-center justify-between"
                  >
                    <span :class="msg.sender === 'user' ? 'text-indigo-400' : 'text-cyan-400'">{{
                      msg.sender === 'user' ? 'User' : 'Assistant'
                    }}</span>
                  </div>
                  <p class="wrap-break-words text-sm text-slate-200 mb-2 leading-relaxed">
                    {{ msg.content.substring(0, 100) }}{{ msg.content.length > 100 ? '...' : '' }}
                  </p>
                  <div
                    v-if="msg.emotion_label && msg.emotion_label !== 'None'"
                    class="inline-flex items-center gap-1 text-xs px-2 py-1 rounded-md bg-slate-900/50 border border-slate-700/50"
                  >
                    <span class="text-slate-400">Emotion:</span>
                    <span class="font-semibold text-slate-200">{{ msg.emotion_label }}</span>
                    <span v-if="msg.emotion_score" class="text-slate-400"
                      >({{ (msg.emotion_score * 100).toFixed(0) }}%)</span
                    >
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div
        v-if="auth.isTherapist && dashboard.hasSelection"
        class="mt-12 pt-8 border-t border-slate-700/50"
      >
        <h3 class="text-xl font-bold text-slate-200 mb-6 flex items-center gap-2">
          <svg
            class="w-6 h-6 text-indigo-400"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"
            ></path>
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
            ></path>
          </svg>
          Settings
        </h3>
        <GuidelineEditor
          :key="
            dashboard.selectedPatientId
              ? dashboard.selectedPatientId + '-' + (dashboard.guidelines?.updated_at ?? '')
              : 'guideline-editor'
          "
          :initial="dashboard.guidelines"
          @save="saveGuidelines"
        />
      </div>
    </div>
  </div>
</template>
