<script setup lang="ts">
import type { Session, Message } from '../types'
import MessageBubble from './MessageBubble.vue'

const props = defineProps<{ sessions: Session[]; activeSessionId: string | null; messages: Message[]; onSessionSelect: (id: string) => void }>()
</script>

<template>
  <div class="grid grid-cols-1 lg:grid-cols-3 gap-4">
    <div class="col-span-1 bg-white border rounded-lg p-3 max-h-[60vh] overflow-auto">
      <h4 class="font-semibold mb-2">Sessions</h4>
      <ul>
        <li
          v-for="sess in props.sessions"
          :key="sess.id"
          class="cursor-pointer p-2 rounded hover:bg-blue-50"
          :class="props.activeSessionId === sess.id ? 'bg-blue-100' : ''"
          @click="props.onSessionSelect(sess.id)"
        >
          <div class="text-sm font-medium">{{ sess.title || 'Session' }}</div>
          <div class="text-xs text-gray-500">{{ sess.last_active ? new Date(sess.last_active).toLocaleDateString() : 'Never' }}</div>
        </li>
      </ul>
    </div>
    <div class="col-span-2 bg-white border rounded-lg p-3 max-h-[60vh] overflow-auto">
      <h4 class="font-semibold mb-2">Chat Log</h4>
      <div v-if="!props.activeSessionId" class="text-gray-500">Select a session to view messages.</div>
      <div v-else-if="props.messages.length === 0" class="text-gray-500">No messages yet.</div>
      <div v-else class="space-y-2">
        <MessageBubble
          v-for="msg in props.messages"
          :key="msg.id"
          :sender="msg.sender"
          :content="msg.content"
          :emotion_label="msg.emotion_label"
        />
      </div>
    </div>
  </div>
</template>
