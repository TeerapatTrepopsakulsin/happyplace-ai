<script setup lang="ts">
import { ref, watch } from 'vue'
import type { Guidelines } from '../types'

const props = defineProps<{ initial: Guidelines | null }>()
const emit = defineEmits<{
  (e: 'save', payload: Guidelines): void
}>()

const responseTone = ref(props.initial?.response_tone ?? '')
const coping = ref(props.initial?.coping_strategies ?? '')
const boundaries = ref(props.initial?.behavioral_boundaries ?? '')
const sensitive = ref((props.initial?.sensitive_topics ?? []).join(', '))

watch(
  () => props.initial,
  (next) => {
    responseTone.value = next?.response_tone ?? ''
    coping.value = next?.coping_strategies ?? ''
    boundaries.value = next?.behavioral_boundaries ?? ''
    sensitive.value = (next?.sensitive_topics ?? []).join(', ')
  },
  { immediate: true }
)

function save() {
  emit('save', {
    response_tone: responseTone.value,
    coping_strategies: coping.value,
    behavioral_boundaries: boundaries.value,
    sensitive_topics: sensitive.value
      .split(',')
      .map((t) => t.trim())
      .filter(Boolean),
  })
}
</script>

<template>
  <div class="bg-white border rounded-lg p-4">
    <h4 class="font-semibold mb-3">Guideline Editor</h4>

    <label class="block text-sm font-medium mt-2">Response Tone</label>
    <input v-model="responseTone" class="w-full border rounded p-2" />

    <label class="block text-sm font-medium mt-2">Coping Strategies</label>
    <textarea v-model="coping" class="w-full border rounded p-2"></textarea>

    <label class="block text-sm font-medium mt-2">Behavioral Boundaries</label>
    <textarea v-model="boundaries" class="w-full border rounded p-2"></textarea>

    <label class="block text-sm font-medium mt-2">Sensitive Topics (comma-separated)</label>
    <textarea v-model="sensitive" class="w-full border rounded p-2"></textarea>

    <button @click="save" class="mt-3 px-4 py-2 bg-blue-600 text-white rounded">Save</button>
  </div>
</template>
