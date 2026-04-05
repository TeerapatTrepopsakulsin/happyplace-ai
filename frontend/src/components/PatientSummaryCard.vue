<script setup lang="ts">
import type { PatientSummary } from '../types'

const props = defineProps<{ summary: PatientSummary }>()
</script>

<template>
  <div
    class="bg-slate-800/80 backdrop-blur-md border border-slate-700 rounded-2xl p-6 space-y-3 shadow-xl"
  >
    <div
      class="text-sm font-bold text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 to-cyan-400 mb-2 uppercase tracking-wide"
    >
      Guardian Patient Summary
    </div>
    <div class="text-slate-300">
      <span class="font-medium text-slate-400 mr-2">Trend:</span> {{ props.summary.mood_trend }}
    </div>
    <div class="text-slate-300">
      <span class="font-medium text-slate-400 mr-2">Dominant emotion (7d):</span>
      {{ props.summary.dominant_emotion_last_7d }}
    </div>
    <div class="text-slate-300">
      <span class="font-medium text-slate-400 mr-2">Sessions (7d):</span>
      {{ props.summary.session_count_last_7d }}
    </div>
    <div class="text-slate-300">
      <span class="font-medium text-slate-400 mr-2">Danger events (7d):</span>
      <span :class="props.summary.danger_events_last_7d > 0 ? 'text-red-400 font-bold' : ''">{{
        props.summary.danger_events_last_7d
      }}</span>
    </div>
  </div>
</template>
