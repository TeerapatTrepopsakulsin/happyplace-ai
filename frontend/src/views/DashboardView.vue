<script setup lang="ts">
import { onMounted, watch, computed } from 'vue'
import { useDashboardStore } from '../stores/dashboard'
import { useAuthStore } from '../stores/auth'
import PatientCard from '../components/PatientCard.vue'
import PatientSummaryCard from '../components/PatientSummaryCard.vue'
import MoodChart from '../components/MoodChart.vue'
import SessionActivityChart from '../components/SessionActivityChart.vue'
import DangerAlertPanel from '../components/DangerAlertPanel.vue'
import GuidelineEditor from '../components/GuidelineEditor.vue'
import ChatLogViewer from '../components/ChatLogViewer.vue'

const dashboard = useDashboardStore()
const auth = useAuthStore()

onMounted(async () => {
  await dashboard.fetchPatients()
  await dashboard.fetchAlerts()
})

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
    }
  }
)

function selectPatient(id: string) {
  dashboard.selectPatient(id)
}

function clearSelection() {
  dashboard.clearSelection()
}

async function resolveAlert(alertId: string) {
  await dashboard.resolveAlert(alertId)
}

async function saveGuidelines(data: any) {
  if (!dashboard.selectedPatientId) return
  await dashboard.updateGuidelines(dashboard.selectedPatientId, data)
}
</script>

<template>
  <div>
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
          <h2 class="text-lg font-semibold">{{ selected?.display_name }}</h2>
          <span class="text-sm text-gray-500">Last active: {{ new Date(selected?.last_active ?? '').toLocaleString() }}</span>
        </div>
      </div>

      <div v-if="auth.isGuardian">
        <PatientSummaryCard v-if="dashboard.summary" :summary="dashboard.summary" />
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <MoodChart :emotionHistory="dashboard.emotionHistory" />
        <SessionActivityChart :progress="dashboard.progress" />
      </div>

      <div v-if="auth.isTherapist" class="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div>
          <DangerAlertPanel :alerts="dashboard.alerts.filter((a) => a.patient_id === dashboard.selectedPatientId)" @resolve="resolveAlert" />
        </div>
        <div>
          <GuidelineEditor :initial="dashboard.guidelines" @save="saveGuidelines" />
        </div>
      </div>

      <div v-if="auth.isTherapist" class="mt-4">
        <ChatLogViewer
          :sessions="[]"
          :activeSessionId="null"
          :messages="[]"
          :onSessionSelect="() => {}"
        />
      </div>
    </div>
  </div>
</template>
