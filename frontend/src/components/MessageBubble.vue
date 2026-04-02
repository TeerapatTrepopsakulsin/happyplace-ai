<script setup lang="ts">
type Sender = 'user' | 'assistant'

const props = defineProps<{ sender: Sender; content: string; emotion_label?: string | null }>()
</script>

<template>
  <div :class="['flex mb-2', sender === 'user' ? 'justify-end' : 'justify-start']">
    <div
      :class="[
        'max-w-[80%] p-3 rounded-lg shadow-sm',
        sender === 'user' ? 'bg-blue-500 text-white rounded-br-none' : 'bg-white text-gray-900 rounded-tl-none'
      ]"
    >
      <p class="whitespace-pre-wrap text-sm">{{ content }}</p>
    </div>
  </div>
</template>
