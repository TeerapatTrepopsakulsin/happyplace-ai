<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { useDashboardStore } from '../stores/dashboard'
import { useChatStore } from '../stores/chat'
import { useAuthStore } from '../stores/auth'

const dashboard = useDashboardStore()
const chat = useChatStore()
const auth = useAuthStore()
const inviteEmail = ref('')
const inviteError = ref('')
const sensitiveTopics = ref('')

onMounted(async () => {
  const patientId = auth.user?.id ?? ''
  if (patientId) {
    await dashboard.fetchGuidelines(patientId).catch(() => {})
    sensitiveTopics.value = (dashboard.guidelines?.sensitive_topics ?? []).join(', ')
  }
  await dashboard.fetchInvitations()
})

watch(
  () => dashboard.guidelines,
  (next) => {
    sensitiveTopics.value = (next?.sensitive_topics ?? []).join(', ')
  },
  { deep: true }
)

async function saveGuidelines() {
  const patientId = auth.user?.id ?? ''
  if (!patientId) return
  await dashboard.updateGuidelines(patientId, {
    ...dashboard.guidelines,
    sensitive_topics: sensitiveTopics.value
      .split(',')
      .map((s) => s.trim())
      .filter(Boolean),
  })
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
  <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
    <section class="bg-white border rounded-lg p-4">
      <h2 class="text-lg font-semibold mb-3">Chatbot Preferences</h2>
      <label class="block text-sm font-medium">Sensitive topics</label>
      <textarea
        v-model="sensitiveTopics"
        placeholder="e.g. stress, anxiety"
        class="w-full border rounded p-2 mb-3"
      ></textarea>
      <button class="px-4 py-2 bg-blue-500 text-white rounded" @click="saveGuidelines">Save</button>
      <p v-if="dashboard.error" class="text-red-600 mt-2">{{ dashboard.error }}</p>
    </section>

    <section class="bg-white border rounded-lg p-4">
      <h2 class="text-lg font-semibold mb-3">Collaboration</h2>
      <div class="flex gap-2 mb-3">
        <input
          v-model="inviteEmail"
          type="email"
          placeholder="Invite by email"
          class="flex-1 border rounded p-2"
        />
        <button class="px-4 py-2 bg-green-500 text-white rounded" @click="addInvite">Invite</button>
      </div>
      <p v-if="inviteError" class="text-red-600 text-sm mb-2">{{ inviteError }}</p>
      <ul class="space-y-2">
        <li v-for="invite in dashboard.invitations" :key="invite.id" class="flex justify-between items-center p-2 border rounded">
          <div>
            <div class="font-semibold">{{ invite.invitee_display_name }}</div>
            <div class="text-xs text-gray-500">{{ invite.invitee_email }} • {{ invite.role_granted }}</div>
          </div>
          <button class="text-red-600 text-xs" @click="revoke(invite.id)">Revoke</button>
        </li>
      </ul>
    </section>
  </div>
</template>
