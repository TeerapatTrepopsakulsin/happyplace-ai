<script setup lang="ts">
import { Chart, registerables } from 'chart.js'
import { Line } from 'vue-chartjs'
import { computed } from 'vue'

Chart.register(...registerables)

const props = defineProps<{ progressData: Array<{ summary_date: string; avg_emotion_score: number | null; dominant_emotion: string | null }> }>()

const labels = computed(() => props.progressData.map((entry) => new Date(entry.summary_date).toLocaleDateString()))
const scores = computed(() => props.progressData.map((entry) => entry.avg_emotion_score || 0))

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
    x: {
      ticks: {
        maxRotation: 45,
        minRotation: 0,
        autoSkipPadding: 30,
      },
    },
    y: {
      min: 0,
      max: 1,
    },
  },
}
</script>

<template>
  <div class="bg-white border rounded-lg p-4 h-[240px] overflow-hidden">
    <h4 class="font-semibold mb-2">Mood Chart</h4>
    <div v-if="props.progressData?.length === 0" class="text-center py-16 text-gray-500">No progress data yet.</div>
    <Line v-else :data="chartData" :options="chartOptions" />
  </div>
</template>
