<script setup lang="ts">
import { onMounted, ref, nextTick, computed, watch } from 'vue'
import { useChatStore } from '../stores/chat'
import { useAuthStore } from '../stores/auth'
import MessageBubble from '../components/MessageBubble.vue'
import type { Session } from '../types'

const chat = useChatStore()
const auth = useAuthStore()
const newMessage = ref('')
const messagesContainer = ref<HTMLElement>()
const sidebarOpen = ref(true)

const editingSessionId = ref<string | null>(null)
const editingTitle = ref('')

const vFocus = {
  mounted: (el: HTMLElement) => el.focus(),
}

const containerClass = computed(() =>
  sidebarOpen.value ? 'grid grid-cols-1 lg:grid-cols-4 gap-4' : 'grid grid-cols-1 gap-4',
)
const sidebarClass = computed(() => (sidebarOpen.value ? 'block' : 'hidden'))

function toggleSidebar() {
  sidebarOpen.value = !sidebarOpen.value
}

async function select(sessionId: string) {
  if (editingSessionId.value) return // Prevent selection while editing
  await chat.selectSession(sessionId)
}

async function createConversation() {
  await chat.createSession()
}

function startEditing(sess: Session, event: Event) {
  event.stopPropagation()
  editingSessionId.value = sess.id
  editingTitle.value = sess.title || 'Conversation'
}

async function saveTitle(sess: Session) {
  if (editingSessionId.value === sess.id) {
    editingSessionId.value = null
    const newTitle = editingTitle.value.trim()
    if (newTitle && newTitle !== sess.title) {
      await chat.renameSession(sess.id, newTitle)
    }
  }
}

async function deleteSession(id: string, event: Event) {
  event.stopPropagation()
  if (confirm('Are you sure you want to delete this session?')) {
    await chat.deleteSession(id)
  }
}

async function send() {
  if (!newMessage.value.trim()) return
  const message = newMessage.value.trim()
  newMessage.value = ''
  try {
    await chat.sendMessage(message)
  } catch {
    newMessage.value = message // restore on error
  }
}

watch(
  () => chat.messages,
  async () => {
    await nextTick()
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  },
  { deep: true },
)

onMounted(async () => {
  if (!auth.isRegular) return
  await chat.fetchSessions()
  if (chat.sessions.length === 0) {
    await createConversation()
  } else {
    await select(chat.sessions[0]!.id)
  }
})
</script>

<template>
  <div :class="containerClass">
    <aside
      :class="[
        sidebarClass,
        'lg:col-span-1 bg-slate-800/80 backdrop-blur-md border border-slate-700 rounded-2xl p-5 shadow-xl flex flex-col h-[80vh] md:h-auto overflow-hidden',
      ]"
    >
      <div class="flex justify-between items-center mb-5 pb-4 border-b border-slate-700/50">
        <div class="flex items-center gap-3">
          <button
            @click="toggleSidebar"
            class="p-1.5 bg-slate-700 hover:bg-slate-600 text-slate-300 rounded-lg transition-colors flex items-center justify-center lg:hidden"
            aria-label="Close session sidebar"
          >
            <span class="w-5 h-5 flex items-center justify-center">‹</span>
          </button>
          <h2 class="text-lg font-bold text-slate-200">Sessions</h2>
        </div>
        <button
          @click="createConversation"
          class="px-3 py-1.5 bg-cyan-500 hover:bg-cyan-400 text-slate-900 font-semibold rounded-lg shadow-lg shadow-cyan-500/20 transition-all duration-200 text-sm flex items-center gap-1"
        >
          <span class="text-lg leading-none">+</span> New
        </button>
      </div>

      <div
        v-if="!chat.sessions.length"
        class="text-slate-500 text-sm flex-1 flex justify-center items-center"
      >
        No sessions yet.
      </div>
      <ul
        class="space-y-2 flex-1 overflow-y-auto scrollbar-thin scrollbar-thumb-slate-600 scrollbar-track-transparent pr-2"
      >
        <li
          v-for="sess in chat.sessions"
          :key="sess.id"
          @click="select(sess.id)"
          :class="[
            'relative cursor-pointer p-3 rounded-xl border transition-all duration-200 group flex items-start justify-between min-h-[4rem]',
            chat.activeSessionId === sess.id
              ? 'bg-indigo-600/20 border-indigo-500/50 shadow-inner'
              : 'bg-slate-800/50 border-transparent hover:bg-slate-700/50 hover:border-slate-600',
          ]"
        >
          <div class="flex-1 min-w-0 pr-8">
            <template v-if="editingSessionId === sess.id">
              <input
                type="text"
                v-model="editingTitle"
                @blur="saveTitle(sess)"
                @keyup.enter="saveTitle(sess)"
                @click.stop
                v-focus
                class="w-full bg-slate-900/80 border border-indigo-500/50 text-slate-200 rounded px-2 py-1 mb-1 text-sm outline-none focus:border-indigo-400"
              />
            </template>
            <template v-else>
              <div
                @click="startEditing(sess, $event)"
                :class="[
                  'font-medium truncate mb-1 transition-colors outline-none cursor-text',
                  chat.activeSessionId === sess.id
                    ? 'text-indigo-300'
                    : 'text-slate-300 group-hover:text-slate-200',
                ]"
              >
                {{ sess.title || 'Conversation' }}
              </div>
            </template>
            <div class="text-xs text-slate-500 bg-slate-900/50 inline-block px-2 py-0.5 rounded-md">
              {{ sess.last_active ? new Date(sess.last_active).toLocaleString() : 'Never' }}
            </div>
          </div>
          <button
            @click="deleteSession(sess.id, $event)"
            class="absolute right-3 top-3 p-1.5 text-slate-500 hover:text-red-400 hover:bg-slate-700 rounded-lg opacity-0 group-hover:opacity-100 transition-all duration-200 -mt-0.5 lg:hover:opacity-100 sm:opacity-100 md:opacity-0 focus:opacity-100"
            title="Delete session"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
              ></path>
            </svg>
          </button>
        </li>
      </ul>
    </aside>

    <section
      class="lg:col-span-3 bg-slate-800/80 backdrop-blur-md border border-slate-700 rounded-2xl p-0 flex flex-col h-[80vh] shadow-xl overflow-hidden relative"
    >
      <div
        class="p-5 pb-3 border-b border-slate-700/50 bg-slate-800/90 sticky top-0 z-10 flex items-center gap-4"
      >
        <button
          v-if="!sidebarOpen"
          @click="toggleSidebar"
          class="p-2 bg-slate-700/50 hover:bg-slate-600 border border-slate-600 text-slate-300 rounded-lg transition-colors flex items-center justify-center"
          title="Open Sessions"
        >
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M4 6h16M4 12h8m-8 6h16"
            ></path>
          </svg>
        </button>
        <button
          v-if="sidebarOpen"
          @click="toggleSidebar"
          class="hidden lg:flex p-2 bg-slate-700/50 hover:bg-slate-600 border border-slate-600 text-slate-300 rounded-lg transition-colors items-center justify-center"
          title="Close Sessions"
        >
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M15 19l-7-7 7-7"
            ></path>
          </svg>
        </button>
        <h2 class="text-lg font-bold text-slate-200 flex items-center gap-2">
          <span class="w-2 h-2 rounded-full bg-green-400 animate-pulse"></span>
          Chat
        </h2>
      </div>
      <div
        ref="messagesContainer"
        class="flex-1 overflow-y-auto scrollbar-thin scrollbar-thumb-slate-600 scrollbar-track-transparent p-5 space-y-4"
      >
        <div
          v-if="!chat.activeSessionId"
          class="text-slate-500 mt-10 h-full flex items-center justify-center flex-col gap-3"
        >
          <svg class="w-12 h-12 opacity-20" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
            ></path>
          </svg>
          Select or create a session to start chatting.
        </div>
        <div
          v-else-if="chat.messages.length === 0"
          class="text-slate-500 mt-10 h-full flex items-center justify-center flex-col gap-3"
        >
          <svg class="w-12 h-12 opacity-20" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
            ></path>
          </svg>
          No messages yet.
        </div>
        <div v-else class="space-y-4 pb-2">
          <MessageBubble
            v-for="msg in chat.messages"
            :key="msg.id"
            :sender="msg.sender"
            :content="msg.content"
            :emotion_label="msg.emotion_label"
          />
        </div>
        <div
          v-if="chat.loading"
          class="text-slate-400 text-sm flex justify-center py-2 animate-pulse w-full"
        >
          Loading...
        </div>
      </div>
      <div class="p-4 bg-slate-900/40 backdrop-blur-md border-t border-slate-700/50">
        <div class="flex items-end gap-3 max-w-4xl mx-auto">
          <div class="flex-1 relative group">
            <textarea
              v-model="newMessage"
              @keyup.enter.prevent="send"
              placeholder="Type your message..."
              class="w-full bg-slate-800/70 border border-slate-600 text-slate-200 rounded-xl px-4 py-3 focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500 outline-none transition-all duration-200 resize-none h-[52px] max-h-32 scrollbar-thin scrollbar-thumb-slate-600"
              rows="1"
            ></textarea>
            <div
              class="absolute inset-x-0 bottom-0 h-1 bg-gradient-to-r from-indigo-500 to-cyan-400 rounded-b-xl opacity-0 group-focus-within:opacity-100 transition-opacity"
            ></div>
          </div>
          <button
            @click="send"
            class="h-[52px] px-6 bg-indigo-600 hover:bg-indigo-500 text-white font-medium rounded-xl shadow-lg shadow-indigo-500/25 transition-all duration-200 transform hover:-translate-y-0.5 flex items-center justify-center gap-2"
          >
            <span class="hidden sm:inline">Send</span>
            <svg
              class="w-4 h-4 transform rotate-45 -mt-1"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"
              ></path>
            </svg>
          </button>
        </div>
        <p v-if="chat.error" class="text-red-400 mt-2 text-sm text-center">{{ chat.error }}</p>
      </div>
    </section>
  </div>
</template>
