<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{ emotion_label?: string | null }>()

const color = computed(() => {
  switch (props.emotion_label) {
    case 'happy':
      return 'bg-green-100 text-green-800'
    case 'sad':
      return 'bg-blue-100 text-blue-800'
    case 'anxious':
      return 'bg-yellow-100 text-yellow-800'
    case 'angry':
    case 'distressed':
      return 'bg-red-100 text-red-800'
    case 'neutral':
      return 'bg-gray-100 text-gray-700'
    default:
      return 'hidden'
  }
})
</script>

<template>
  <span v-if="props.emotion_label" :class="['text-xs font-semibold px-2 py-1 rounded-full', color]">
    {{ props.emotion_label }}
  </span>
</template>
