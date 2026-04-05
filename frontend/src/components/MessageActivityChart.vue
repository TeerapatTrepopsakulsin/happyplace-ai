<script setup lang="ts">
import { Chart, registerables } from 'chart.js'
import { Bar } from 'vue-chartjs'
import { computed } from 'vue'

Chart.register(...registerables)

const props = defineProps<{ progress: Array<{ summary_date: string; total_messages: number }> }>()

const labels = computed(() => props.progress.map((entry) => new Date(entry.summary_date).toLocaleDateString()))
const counts = computed(() => props.progress.map((entry) => entry.total_messages))

const chartData = computed(() => ({
  labels: labels.value,
  datasets: [
    {
      label: 'Message count',
      data: counts.value,
      backgroundColor: 'rgba(6, 182, 212, 0.6)',
      borderColor: '#06b6d4',
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
  <div class="bg-slate-800/80 backdrop-blur-md border border-slate-700 rounded-2xl p-5 h-[400px] shadow-xl overflow-hidden flex flex-col">
    <h4 class="font-bold text-slate-200 mb-2 px-1">Message Activity</h4>
    <div v-if="props.progress?.length === 0" class="flex-1 flex items-center justify-center text-slate-500">No progress data yet.</div>
    <div v-else class="flex-1 relative w-full"><Bar :data="chartData" :options="chartOptions" /></div>
  </div>
</template>
