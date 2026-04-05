<script setup lang="ts">
import { ref, watch } from 'vue'
import type { Guidelines } from '../types'

const props = defineProps<{ 
  initial: Guidelines | null;
  title?: string;
}>()
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
  <div class="bg-slate-800/80 backdrop-blur-md border border-slate-700 rounded-2xl p-6 shadow-xl">
    <div class="flex items-center justify-between mb-6 pb-4 border-b border-slate-700/50">
      <h4 class="font-bold text-slate-200">{{ props.title || 'Guidelines Configuration' }}</h4>
      <button
        v-if="!isEditing"
        @click="toggleEdit"
        class="px-4 py-2 bg-slate-700 text-slate-200 rounded-lg text-sm font-medium hover:bg-slate-600 transition-colors border border-slate-600"
      >
        Edit Guidelines
      </button>
    </div>

    <!-- View Mode -->
    <div v-if="!isEditing" class="space-y-4">
      <div v-if="!props.initial" class="text-slate-500 bg-slate-900/30 p-6 rounded-xl text-center border border-slate-700/50 flex flex-col items-center justify-center gap-2">
        <svg class="w-8 h-8 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path></svg>
        No guidelines set yet. Click Edit to configure.
      </div>
      <div v-else class="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div class="bg-slate-900/50 p-4 rounded-xl border border-slate-700/50">
          <label class="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Response Tone</label>
          <p class="text-sm text-slate-200">{{ props.initial.response_tone || 'Not set' }}</p>
        </div>
        <div class="bg-slate-900/50 p-4 rounded-xl border border-slate-700/50">
          <label class="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Sensitive Topics</label>
          <div class="flex flex-wrap gap-2">
            <span v-if="!(props.initial.sensitive_topics?.length)" class="text-sm text-slate-500">Not set</span>
            <span v-for="topic in props.initial.sensitive_topics" :key="topic" class="text-xs px-2.5 py-1 bg-slate-800 text-slate-300 rounded-md border border-slate-700">{{ topic }}</span>
          </div>
        </div>
        <div class="bg-slate-900/50 p-4 rounded-xl border border-slate-700/50 md:col-span-2">
          <label class="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Coping Strategies</label>
          <p class="text-sm text-slate-200 whitespace-pre-wrap leading-relaxed">{{ props.initial.coping_strategies || 'Not set' }}</p>
        </div>
        <div class="bg-slate-900/50 p-4 rounded-xl border border-slate-700/50 md:col-span-2">
          <label class="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Behavioral Boundaries</label>
          <p class="text-sm text-slate-200 whitespace-pre-wrap leading-relaxed">{{ props.initial.behavioral_boundaries || 'Not set' }}</p>
        </div>
      </div>
    </div>

    <!-- Edit Mode -->
    <div v-else class="space-y-5">
      <div>
        <label class="block text-sm font-medium text-slate-300 mb-2">Response Tone</label>
        <input v-model="responseTone" class="w-full bg-slate-900/50 border border-slate-600 text-slate-200 rounded-lg p-3 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none transition-colors" placeholder="e.g. Empathetic, Direct" />
      </div>

      <div>
        <label class="block text-sm font-medium text-slate-300 mb-2">Coping Strategies</label>
        <textarea v-model="coping" class="w-full bg-slate-900/50 border border-slate-600 text-slate-200 rounded-lg p-3 h-24 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none transition-colors resize-none scrollbar-thin scrollbar-thumb-slate-600"></textarea>
      </div>

      <div>
        <label class="block text-sm font-medium text-slate-300 mb-2">Behavioral Boundaries</label>
        <textarea v-model="boundaries" class="w-full bg-slate-900/50 border border-slate-600 text-slate-200 rounded-lg p-3 h-24 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none transition-colors resize-none scrollbar-thin scrollbar-thumb-slate-600"></textarea>
      </div>

      <div>
        <label class="block text-sm font-medium text-slate-300 mb-2">Sensitive Topics (comma-separated)</label>
        <textarea v-model="sensitive" class="w-full bg-slate-900/50 border border-slate-600 text-slate-200 rounded-lg p-3 h-20 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none transition-colors resize-none scrollbar-thin scrollbar-thumb-slate-600"></textarea>
      </div>

      <div class="flex gap-3 pt-4 border-t border-slate-700/50">
        <button @click="save" class="px-6 py-2 bg-indigo-600 font-medium text-white rounded-lg hover:bg-indigo-500 transition-colors shadow-lg shadow-indigo-500/25">Save Changes</button>
        <button @click="cancel" class="px-6 py-2 bg-slate-700 font-medium text-slate-300 rounded-lg hover:bg-slate-600 hover:text-white transition-colors">Cancel</button>
      </div>
    </div>
  </div>
</template>
