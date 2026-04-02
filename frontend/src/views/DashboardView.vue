<script setup lang="ts">
import { onMounted, onUnmounted, watch, computed, ref } from 'vue'
import { useDashboardStore } from '../stores/dashboard'
import { useAuthStore } from '../stores/auth'
import PatientCard from '../components/PatientCard.vue'
import PatientSummaryCard from '../components/PatientSummaryCard.vue'
import MoodChart from '../components/MoodChart.vue'
import SessionActivityChart from '../components/SessionActivityChart.vue'
import DangerAlertPanel from '../components/DangerAlertPanel.vue'
import GuidelineEditor from '../components/GuidelineEditor.vue'

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
  { immediate: true }
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

async function saveGuidelines(data: any) {
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
  } catch (err) {
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
  } catch (err) {
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
    <div v-if="notification" :class="['fixed top-4 right-4 px-6 py-3 rounded-lg shadow-lg text-white z-50', notification.type === 'success' ? 'bg-green-500' : 'bg-red-500']">
      {{ notification.message }}
    </div>

    <div v-if="!dashboard.hasSelection" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <PatientCard
        v-for="patient in dashboard.patients"
        :key="patient.patient_id"
        :patient="patient"
        :active="false"
        @select="selectPatient"
      />
    </div>

    <div v-else class="space-y-4">
      <button @click="clearSelection" class="text-sm text-blue-600">← Back to patients</button>
      <div class="bg-white p-4 rounded-lg border">
        <div class="flex items-center justify-between">
          <div class="text-sm text-gray-500">Date: {{ new Date().toLocaleString() }}</div>
          <button 
            @click="refreshData" 
            :disabled="isRefreshing"
            class="px-3 py-1 bg-blue-500 text-white rounded text-sm hover:bg-blue-600 disabled:bg-gray-300 disabled:cursor-not-allowed"
          >
            {{ isRefreshing ? 'Refreshing...' : 'Refresh' }}
          </button>
        </div>
      </div>
      <div class="bg-white p-4 rounded-lg border mt-3">
        <h2 class="text-lg font-semibold">{{ selected?.display_name }}</h2>
        <p class="text-sm text-gray-500">Last active: {{ selected?.last_active ? new Date(selected.last_active).toLocaleString() : 'Never' }}</p>
      </div>

      <div v-if="auth.isGuardian">
        <PatientSummaryCard v-if="dashboard.summary" :summary="dashboard.summary" />
      </div>

      <div v-if="auth.isTherapist" class="mt-6">
        <h3 class="text-xl font-semibold mb-4">Mood & Danger</h3>
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <div>
            <MoodChart :progressData="dashboard.progress" />
          </div>
          <div>
            <DangerAlertPanel :alerts="dashboard.alerts.filter((a) => a.patient_id === dashboard.selectedPatientId)" @resolve="resolveAlert" />
          </div>
        </div>
      </div>

      <div class="mt-6">
        <h3 class="text-xl font-semibold mb-4">Usage and Chat Log</h3>
        <div class="grid grid-cols-1 lg:grid-cols-3 gap-4">
          <div>
            <SessionActivityChart :progress="dashboard.progress" />
          </div>
          <div class="lg:col-span-2">
            <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
              <div>
                <div class="bg-white border rounded-lg p-4 h-[400px] flex flex-col">
                  <h4 class="font-semibold mb-3">Sessions</h4>
                  <div v-if="dashboard.loading" class="flex-1 flex items-center justify-center text-gray-500">Loading...</div>
                  <div v-else-if="dashboard.sessions.length === 0" class="flex-1 flex items-center justify-center text-gray-500">No sessions yet.</div>
                  <ul v-else class="flex-1 overflow-auto space-y-2">
                    <li
                      v-for="sess in dashboard.sessions"
                      :key="sess.id"
                      @click="selectSession(sess.id)"
                      :class="['cursor-pointer p-2 rounded border', dashboard.selectedSessionId === sess.id ? 'bg-blue-100 border-blue-500' : 'hover:bg-gray-100 border-transparent']"
                    >
                      <div class="font-medium text-sm">{{ sess.title || 'Chat Session' }}</div>
                      <div class="text-xs text-gray-500">{{ sess.last_active ? new Date(sess.last_active).toLocaleString() : 'Never' }}</div>
                    </li>
                  </ul>
                </div>
              </div>
              <div>
                <div class="bg-white border rounded-lg p-4 h-[400px] flex flex-col">
                  <h4 class="font-semibold mb-3">Chat Log</h4>
                  <div v-if="!dashboard.selectedSessionId" class="flex-1 flex items-center justify-center text-gray-500">Select a session to view messages.</div>
                  <div v-else-if="dashboard.messages.length === 0" class="flex-1 flex items-center justify-center text-gray-500">No messages in this session.</div>
                  <div v-else class="flex-1 overflow-auto space-y-2">
                    <div
                      v-for="msg in dashboard.messages"
                      :key="msg.id"
                      :class="['p-2 rounded text-sm', msg.sender === 'user' ? 'bg-blue-100' : 'bg-gray-100']"
                    >
                      <div class="font-medium text-xs opacity-70 mb-1">{{ msg.sender === 'user' ? 'User' : 'Assistant' }}</div>
                      <p class="break-words text-xs mb-1">{{ msg.content.substring(0, 100) }}{{ msg.content.length > 100 ? '...' : '' }}</p>
                      <div v-if="msg.emotion_label && msg.emotion_label !== 'None'" class="text-xs text-blue-700 font-medium">
                        Emotion: {{ msg.emotion_label }}{{ msg.emotion_score ? ` (${(msg.emotion_score * 100).toFixed(0)}%)` : '' }}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
        </div>
      </div>

      <div v-if="auth.isTherapist && dashboard.hasSelection" class="mt-6">
        <GuidelineEditor
          :key="dashboard.selectedPatientId ? dashboard.selectedPatientId + '-' + (dashboard.guidelines?.updated_at ?? '') : 'guideline-editor'"
          :initial="dashboard.guidelines"
          @save="saveGuidelines"
        />
      </div>
    
</template>
