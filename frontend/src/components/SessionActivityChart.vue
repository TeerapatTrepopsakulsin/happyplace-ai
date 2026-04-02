<script setup lang="ts">
import { Chart, registerables } from 'chart.js'
import { Bar } from 'vue-chartjs'
import { computed } from 'vue'

Chart.register(...registerables)

const props = defineProps<{ progress: Array<{ summary_date: string; session_count: number }> }>()

const labels = computed(() => props.progress.map((entry) => new Date(entry.summary_date).toLocaleDateString()))
const counts = computed(() => props.progress.map((entry) => entry.session_count))

const chartData = computed(() => ({
  labels: labels.value,
  datasets: [
    {
      label: 'Session count',
      data: counts.value,
      backgroundColor: 'rgba(59, 130, 246, 0.6)',
      borderColor: '#3b82f6',
      borderWidth: 1,
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
      beginAtZero: true,
    },
  },
}
</script>

<template>
  <div class="bg-white border rounded-lg p-4 h-[240px] overflow-hidden">
    <h4 class="font-semibold mb-2">Session Activity</h4>
    <div v-if="props.progress?.length === 0" class="text-center py-16 text-gray-500">No progress data yet.</div>
    <Bar v-else :data="chartData" :options="chartOptions" />
  </div>
</template>
