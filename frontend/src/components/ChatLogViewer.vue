<script setup lang="ts">
import type { Session, Message } from '../types'
import MessageBubble from './MessageBubble.vue'

const props = defineProps<{
  sessions: Session[]
  activeSessionId: string | null
  messages: Message[]
  onSessionSelect: (id: string) => void
}>()
</script>

<template>
  <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
    <div
      class="col-span-1 bg-slate-800/80 backdrop-blur-md border border-slate-700 rounded-2xl p-4 shadow-xl max-h-[60vh] overflow-hidden flex flex-col"
    >
      <h4 class="font-bold text-slate-200 mb-4 px-2">Sessions</h4>
      <ul
        class="flex-1 overflow-y-auto scrollbar-thin scrollbar-thumb-slate-600 scrollbar-track-transparent space-y-2 pr-2"
      >
        <li
          v-for="sess in props.sessions"
          :key="sess.id"
          class="cursor-pointer p-3 rounded-xl transition-all duration-200 border"
          :class="
            props.activeSessionId === sess.id
              ? 'bg-indigo-600/20 border-indigo-500/50 shadow-inner'
              : 'bg-slate-800/50 border-transparent hover:bg-slate-700/50 hover:border-slate-600'
          "
          @click="props.onSessionSelect(sess.id)"
        >
          <div
            :class="[
              'font-medium text-sm truncate mb-1',
              props.activeSessionId === sess.id ? 'text-indigo-300' : 'text-slate-300',
            ]"
          >
            {{ sess.title || 'Session' }}
          </div>
          <div class="text-xs text-slate-500 bg-slate-900/50 inline-block px-2 py-0.5 rounded-md">
            {{ sess.last_active ? new Date(sess.last_active).toLocaleDateString() : 'Never' }}
          </div>
        </li>
      </ul>
    </div>
    <div
      class="col-span-2 bg-slate-800/80 backdrop-blur-md border border-slate-700 rounded-2xl p-4 shadow-xl max-h-[60vh] flex flex-col"
    >
      <h4 class="font-bold text-slate-200 mb-4 px-2 pb-3 border-b border-slate-700/50">Chat Log</h4>
      <div
        class="flex-1 overflow-y-auto scrollbar-thin scrollbar-thumb-slate-600 scrollbar-track-transparent pr-2 space-y-4"
      >
        <div
          v-if="!props.activeSessionId"
          class="text-slate-500 h-full flex items-center justify-center flex-col gap-2"
        >
          Select a session to view messages.
        </div>
        <div
          v-else-if="props.messages.length === 0"
          class="text-slate-500 h-full flex items-center justify-center flex-col gap-2"
        >
          No messages yet.
        </div>
        <div v-else class="space-y-4 py-2">
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
  </div>
</template>
