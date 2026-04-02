<script setup lang="ts">
import type { Alert } from '../types'

const props = defineProps<{ alerts: Alert[] }>()
const emit = defineEmits<{
  (e: 'resolve', id: string): void
}>()

function handleResolve(alert: Alert) {
  console.log('Resolving alert:', alert)
  if (!alert.id || alert.id === 'undefined') {
    console.error('Invalid alert ID:', alert.id)
    return
  }
  emit('resolve', alert.id)
}</script>

<template>
  <div class="bg-white border rounded-lg p-4">
    <h4 class="font-semibold mb-3">Unresolved Danger Alerts</h4>
    <div v-if="!props.alerts?.length" class="text-gray-500">No active danger alerts.</div>
    <ul v-else class="space-y-3">
      <li v-for="alert in props.alerts" :key="alert.id" class="p-3 bg-red-50 rounded">
        <div class="text-sm text-red-800">{{ alert.snippet }}</div>
        <div class="text-xs text-gray-500 mt-1">{{ new Date(alert.created_at).toLocaleString() }}</div>
        <button @click="handleResolve(alert)" class="mt-2 text-xs text-white bg-red-500 px-2 py-1 rounded" :disabled="!alert.id || alert.id === 'undefined'">
          Resolve
        </button>
      </li>
    </ul>
  </div>
</template>
