<script setup lang="ts">
import { Chart, registerables } from 'chart.js'
import { Line } from 'vue-chartjs'
import { computed } from 'vue'

Chart.register(...registerables)

const props = defineProps<{ emotionHistory: Array<{ snapshot_at: string; average_score: number; dominant_emotion: string }> }>()

const labels = computed(() => props.emotionHistory.map((entry) => new Date(entry.snapshot_at).toLocaleDateString()))
const scores = computed(() => props.emotionHistory.map((entry) => entry.average_score))

const chartData = computed(() => ({
  labels: labels.value,
  datasets: [
    {
      label: 'Average Emotion Score',
      data: scores.value,
      borderColor: '#3b82f6',
      backgroundColor: 'rgba(59,130,246,0.2)',
      tension: 0.3,
      fill: true,
    },
  ],
}))

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  scales: {
    y: {
      min: 0,
      max: 1,
    },
  },
}
</script>

<template>
  <div class="bg-white border rounded-lg p-4 min-h-[240px]">
    <h4 class="font-semibold mb-2">Mood Chart</h4>
    <div v-if="props.emotionHistory?.length === 0" class="text-center py-16 text-gray-500">No emotion history yet.</div>
    <Line v-else :data="chartData" :options="chartOptions" />
  </div>
</template>
