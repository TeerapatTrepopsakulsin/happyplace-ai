<script setup lang="ts">
type Sender = 'user' | 'assistant'

const props = defineProps<{ sender: Sender; content: string; emotion_label?: string | null }>()
</script>

<template>
  <div :class="['flex mb-4 transition-all duration-300', sender === 'user' ? 'justify-end' : 'justify-start']">
    <div
      :class="[
        'max-w-[80%] p-4 rounded-2xl shadow-lg relative group',
        sender === 'user' ? 'bg-indigo-600 text-slate-100 rounded-br-sm shadow-indigo-900/20' : 'bg-slate-800 text-slate-200 rounded-tl-sm hover:bg-slate-750 border border-slate-700/50 shadow-slate-900/20'
      ]"
    >
      <p class="whitespace-pre-wrap text-sm leading-relaxed">{{ content }}</p>
    </div>
  </div>
</template>
