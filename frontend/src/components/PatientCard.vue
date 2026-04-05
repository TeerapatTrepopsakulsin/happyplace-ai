<script setup lang="ts">
import type { PatientCardModel } from '../types'

const props = defineProps<{ patient: PatientCardModel; active: boolean }>()
const emit = defineEmits<{
  (e: 'select', id: string): void
}>()
</script>

<template>
  <button
    @click="emit('select', props.patient.patient_id)"
    :class="[
      'w-full p-5 text-left border rounded-xl mb-3 transition-all duration-200 group',
      props.active
        ? 'border-indigo-500 bg-indigo-500/10 shadow-lg shadow-indigo-500/10'
        : 'border-slate-700 bg-slate-800/50 hover:bg-slate-750 hover:border-slate-600 hover:shadow-md',
    ]"
  >
    <div
      :class="[
        'font-semibold text-lg transition-colors',
        props.active ? 'text-indigo-400' : 'text-slate-200 group-hover:text-white',
      ]"
    >
      {{ props.patient.display_name }}
    </div>
    <div class="text-xs text-slate-400 mt-1">
      Last active: {{ new Date(props.patient.last_active).toLocaleString() }}
    </div>
  </button>
</template>
