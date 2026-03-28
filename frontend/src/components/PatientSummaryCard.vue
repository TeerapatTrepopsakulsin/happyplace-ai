<script setup lang="ts">
import type { PatientSummary } from '../types'

const props = defineProps<{ summary: PatientSummary }>()
</script>

<template>
  <div class="bg-white border rounded-lg p-4 space-y-2">
    <div class="text-sm font-semibold">Guardian Patient Summary</div>
    <div>Trend: {{ props.summary.mood_trend }}</div>
    <div>Dominant emotion (all sessions): {{ props.summary.dominant_emotion_last_7d }}</div>
    <div>Sessions (all sessions): {{ props.summary.session_count_last_7d }}</div>
    <div>Danger events (all sessions): {{ props.summary.danger_events_last_7d }}</div>
  </div>
</template>
