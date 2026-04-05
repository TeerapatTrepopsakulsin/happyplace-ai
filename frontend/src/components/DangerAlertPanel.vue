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
  <div class="bg-slate-800/80 backdrop-blur-md border border-slate-700 rounded-2xl p-6 shadow-xl h-[280px] flex flex-col">
    <div class="flex items-center gap-2 mb-4 shrink-0">
      <div class="w-2 h-2 rounded-full bg-red-500 animate-pulse"></div>
      <h4 class="font-bold text-slate-200">Unresolved Danger Alerts</h4>
    </div>
    <div v-if="!props.alerts?.length" class="text-slate-500 bg-slate-900/30 p-4 rounded-xl text-center border border-slate-700/50 flex-1 flex items-center justify-center">No active danger alerts.</div>
    <ul v-else class="flex-1 overflow-y-auto scrollbar-thin scrollbar-thumb-slate-600 scrollbar-track-transparent space-y-4 pr-2">
      <li v-for="alert in props.alerts" :key="alert.id" class="p-4 bg-red-900/20 border border-red-500/30 rounded-xl relative overflow-hidden group">
        <div class="absolute top-0 left-0 w-1 h-full bg-red-500"></div>
        <div class="text-sm text-red-200 leading-relaxed">{{ alert.snippet }}</div>
        <div class="flex justify-between items-end mt-3">
          <div class="text-xs text-red-400/70">{{ new Date(alert.created_at).toLocaleString() }}</div>
          <button @click="handleResolve(alert)" class="text-xs font-semibold text-white bg-red-600 hover:bg-red-500 px-3 py-1.5 rounded-lg transition-colors shadow-lg shadow-red-900/50 disabled:opacity-50 disabled:cursor-not-allowed" :disabled="!alert.id || alert.id === 'undefined'">
            Resolve
          </button>
        </div>
      </li>
    </ul>
  </div>
</template>
