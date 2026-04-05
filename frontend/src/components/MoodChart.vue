<script setup lang="ts">
import { Chart, registerables } from 'chart.js'
import { Line } from 'vue-chartjs'
import { computed } from 'vue'

Chart.register(...registerables)

const props = defineProps<{
  progressData: Array<{
    summary_date: string
    avg_emotion_score: number | null
    dominant_emotion: string | null
  }>
}>()

const labels = computed(() =>
  props.progressData.map((entry) => new Date(entry.summary_date).toLocaleDateString()),
)
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
  <div
    class="bg-slate-800/80 backdrop-blur-md border border-slate-700 rounded-2xl p-5 h-[280px] shadow-xl overflow-hidden flex flex-col"
  >
    <h4 class="font-bold text-slate-200 mb-2 px-1">Mood Chart</h4>
    <div
      v-if="props.progressData?.length === 0"
      class="flex-1 flex items-center justify-center text-slate-500"
    >
      No progress data yet.
    </div>
    <div v-else class="flex-1 relative w-full">
      <Line :data="chartData" :options="chartOptions" />
    </div>
  </div>
</template>
