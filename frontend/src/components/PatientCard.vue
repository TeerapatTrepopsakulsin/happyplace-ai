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
      'w-full p-4 text-left border rounded-md mb-2 transition',
      props.active ? 'border-blue-500 bg-blue-50' : 'border-gray-200 bg-white hover:border-blue-300'
    ]"
  >
    <div class="font-semibold">{{ props.patient.display_name }}</div>
    <div class="text-xs text-gray-500">Last active: {{ new Date(props.patient.last_active).toLocaleString() }}</div>
  </button>
</template>
