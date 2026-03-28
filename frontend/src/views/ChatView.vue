<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useChatStore } from '../stores/chat'
import { useAuthStore } from '../stores/auth'
import MessageBubble from '../components/MessageBubble.vue'
import EmotionBadge from '../components/EmotionBadge.vue'

const chat = useChatStore()
const auth = useAuthStore()
const newMessage = ref('')

async function select(sessionId: string) {
  await chat.selectSession(sessionId)
}

async function createConversation() {
  await chat.createSession()
}

async function send() {
  if (!newMessage.value.trim()) return
  try {
    await chat.sendMessage(newMessage.value.trim())
    newMessage.value = ''
  } catch (e) {
    // error displayed via store
  }
}

onMounted(async () => {
  if (!auth.isRegular) return
  await chat.fetchSessions()
  if (chat.sessions.length > 0) {
    await select(chat.sessions[0]!.id)
  }
})
</script>

<template>
  <div class="grid grid-cols-1 lg:grid-cols-4 gap-4">
    <aside class="lg:col-span-1 bg-white border rounded-lg p-4">
      <div class="flex justify-between items-center mb-3">
        <h2 class="text-lg font-semibold">Sessions</h2>
        <button @click="createConversation" class="px-2 py-1 bg-blue-500 text-white rounded text-sm">New</button>
      </div>
      <div v-if="chat.loading" class="text-gray-500">Loading...</div>
      <div v-if="!chat.sessions.length" class="text-gray-500">No sessions yet.</div>
      <ul class="space-y-2">
        <li
          v-for="sess in chat.sessions"
          :key="sess.id"
          @click="select(sess.id)"
          :class="['cursor-pointer p-2 rounded', chat.activeSessionId === sess.id ? 'bg-blue-100' : 'hover:bg-gray-100']"
        >
          <div class="font-medium">{{ sess.title || 'Conversation' }}</div>
          <div class="text-xs text-gray-500">{{ new Date(sess.last_active).toLocaleString() }}</div>
        </li>
      </ul>
    </aside>

    <section class="lg:col-span-3 bg-white border rounded-lg p-4 flex flex-col h-[75vh]">
      <h2 class="text-lg font-semibold mb-3">Chat</h2>
      <div class="flex-1 overflow-auto space-y-2 mb-4">
        <div v-if="!chat.activeSessionId" class="text-gray-500 mt-10">Select or create a session to start chatting.</div>
        <div v-else-if="chat.messages.length === 0" class="text-gray-500 mt-10">No messages yet.</div>
        <div v-else class="space-y-1">
          <MessageBubble
            v-for="msg in chat.messages"
            :key="msg.id"
            :sender="msg.sender"
            :content="msg.content"
            :emotion_label="msg.emotion_label"
          />
        </div>
      </div>
      <div class="border-t pt-3">
        <div class="flex items-center gap-2">
          <input
            v-model="newMessage"
            @keyup.enter="send"
            placeholder="Type a message"
            class="flex-1 border rounded px-3 py-2"
          />
          <button @click="send" class="px-4 py-2 bg-blue-500 text-white rounded">Send</button>
        </div>
        <p v-if="chat.error" class="text-red-600 mt-2">{{ chat.error }}</p>
      </div>
    </section>
  </div>
</template>
