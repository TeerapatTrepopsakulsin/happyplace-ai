<script setup lang="ts">
import { ref, watch } from 'vue'
import type { Guidelines } from '../types'

const props = defineProps<{ initial: Guidelines | null }>()
const emit = defineEmits<{
  (e: 'save', payload: Guidelines): void
}>()

const isEditing = ref(false)
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
    isEditing.value = false
  },
  { immediate: true }
)

function toggleEdit() {
  isEditing.value = !isEditing.value
}

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
  // Exit edit mode immediately - the parent will update props and trigger watch
  isEditing.value = false
}

function cancel() {
  responseTone.value = props.initial?.response_tone ?? ''
  coping.value = props.initial?.coping_strategies ?? ''
  boundaries.value = props.initial?.behavioral_boundaries ?? ''
  sensitive.value = (props.initial?.sensitive_topics ?? []).join(', ')
  isEditing.value = false
}
</script>

<template>
  <div class="bg-white border rounded-lg p-4">
    <div class="flex items-center justify-between mb-4">
      <h4 class="font-semibold">Guideline</h4>
      <button
        v-if="!isEditing"
        @click="toggleEdit"
        class="px-3 py-1 bg-blue-600 text-white rounded text-sm hover:bg-blue-700"
      >
        Edit
      </button>
    </div>

    <!-- View Mode -->
    <div v-if="!isEditing" class="space-y-3">
      <div v-if="!props.initial" class="text-gray-500">No guidelines set yet. Click Edit to add guidelines.</div>
      <div v-else>
        <div class="mb-3">
          <label class="block text-sm font-medium text-gray-600">Response Tone</label>
          <p class="mt-1 text-sm text-gray-900">{{ props.initial.response_tone || 'Not set' }}</p>
        </div>
        <div class="mb-3">
          <label class="block text-sm font-medium text-gray-600">Coping Strategies</label>
          <p class="mt-1 text-sm text-gray-900 whitespace-pre-wrap">{{ props.initial.coping_strategies || 'Not set' }}</p>
        </div>
        <div class="mb-3">
          <label class="block text-sm font-medium text-gray-600">Behavioral Boundaries</label>
          <p class="mt-1 text-sm text-gray-900 whitespace-pre-wrap">{{ props.initial.behavioral_boundaries || 'Not set' }}</p>
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-600">Sensitive Topics</label>
          <p class="mt-1 text-sm text-gray-900">{{ (props.initial.sensitive_topics ?? []).join(', ') || 'Not set' }}</p>
        </div>
      </div>
    </div>

    <!-- Edit Mode -->
    <div v-else class="space-y-3">
      <div>
        <label class="block text-sm font-medium mt-2">Response Tone</label>
        <input v-model="responseTone" class="w-full border rounded p-2" />
      </div>

      <div>
        <label class="block text-sm font-medium">Coping Strategies</label>
        <textarea v-model="coping" class="w-full border rounded p-2 h-24"></textarea>
      </div>

      <div>
        <label class="block text-sm font-medium">Behavioral Boundaries</label>
        <textarea v-model="boundaries" class="w-full border rounded p-2 h-24"></textarea>
      </div>

      <div>
        <label class="block text-sm font-medium">Sensitive Topics (comma-separated)</label>
        <textarea v-model="sensitive" class="w-full border rounded p-2 h-20"></textarea>
      </div>

      <div class="flex gap-2 pt-2">
        <button @click="save" class="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700">Save</button>
        <button @click="cancel" class="px-4 py-2 bg-gray-400 text-white rounded hover:bg-gray-500">Cancel</button>
      </div>
    </div>
  </div>
</template>
