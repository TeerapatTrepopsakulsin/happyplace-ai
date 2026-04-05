<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useDashboardStore } from '../stores/dashboard'
import { useChatStore } from '../stores/chat'
import { useAuthStore } from '../stores/auth'
import GuidelineEditor from '../components/GuidelineEditor.vue'
import type { Guidelines } from '../types'

const dashboard = useDashboardStore()
const chat = useChatStore()
const auth = useAuthStore()
const inviteEmail = ref('')
const inviteError = ref('')

onMounted(async () => {
  const patientId = auth.user?.id ?? ''
  if (patientId) {
    await dashboard.fetchGuidelines(patientId).catch(() => {})
  }
  await dashboard.fetchInvitations()
})

async function saveGuidelines(data: Guidelines) {
  const patientId = auth.user?.id ?? ''
  if (!patientId) return
  await dashboard.updateGuidelines(patientId, data)
}

async function addInvite() {
  inviteError.value = ''
  try {
    await dashboard.invite(inviteEmail.value)
    inviteEmail.value = ''
  } catch (err: any) {
    inviteError.value = dashboard.error || 'Invite failed'
  }
}

function revoke(id: string) {
  dashboard.revokeInvitation(id)
}
</script>

<template>
  <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
    <GuidelineEditor
      title="Chatbot Preferences"
      :initial="dashboard.guidelines"
      class="h-max"
      @save="saveGuidelines"
    />

    <section class="bg-slate-800/80 backdrop-blur-md border border-slate-700 rounded-2xl p-6 shadow-xl flex flex-col">
      <h2 class="text-xl font-bold mb-4 text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 to-cyan-400">Collaboration</h2>
      <div class="flex gap-3 mb-4">
        <input
          v-model="inviteEmail"
          type="email"
          placeholder="Invite by email"
          class="flex-1 bg-slate-900/50 border border-slate-600 text-slate-200 rounded-lg p-3 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none transition-all duration-200 placeholder-slate-500"
        />
        <button class="px-6 py-2.5 bg-cyan-600 hover:bg-cyan-500 text-white font-medium rounded-lg shadow-lg shadow-cyan-500/25 transition-all duration-200 transform hover:-translate-y-0.5" @click="addInvite">Invite</button>
      </div>
      <p v-if="inviteError" class="text-red-400 text-sm mb-4 bg-red-900/20 border border-red-500/20 p-2 rounded-lg">{{ inviteError }}</p>
      
      <div class="flex-1 overflow-hidden flex flex-col">
        <h3 class="text-sm font-semibold text-slate-400 mb-3 uppercase tracking-wider">Active Invitations</h3>
        <ul class="space-y-3 overflow-y-auto scrollbar-thin scrollbar-thumb-slate-600 pr-2">
          <li v-for="invite in dashboard.invitations" :key="invite.id" class="flex justify-between items-center p-3 bg-slate-900/30 border border-slate-700/50 rounded-xl hover:bg-slate-700/30 transition-colors">
            <div>
              <div class="font-bold text-slate-200">{{ invite.invitee_display_name }}</div>
              <div class="text-xs text-slate-400 mt-1 flex items-center gap-2">
                <span>{{ invite.invitee_email }}</span>
                <span class="w-1 h-1 rounded-full bg-slate-600"></span>
                <span class="text-cyan-400 font-medium">{{ invite.role_granted }}</span>
              </div>
            </div>
            <button class="w-8 h-8 flex items-center justify-center text-slate-400 hover:text-red-400 hover:bg-red-400/10 rounded-full transition-colors" @click="revoke(invite.id)" title="Revoke invitation" aria-label="Revoke invitation">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>
            </button>
          </li>
          <li v-if="dashboard.invitations.length === 0" class="text-slate-500 text-sm py-4 text-center">
            No active invitations.
          </li>
        </ul>
      </div>
    </section>
  </div>
</template>
