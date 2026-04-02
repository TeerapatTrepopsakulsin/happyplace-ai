<script setup lang="ts">
import { useAuthStore } from './stores/auth'
import { storeToRefs } from 'pinia'

const auth = useAuthStore()
const { isAuthenticated, user } = storeToRefs(auth)

function logout() {
  auth.logout()
}
</script>

<template>
  <div class="min-h-screen bg-gray-50 text-gray-800">
    <header class="bg-white border-b border-gray-200 p-4 flex items-center justify-between">
      <div class="flex items-center gap-4">
        <div class="text-xl font-semibold">HappyPlaceAI</div>
        <div v-if="isAuthenticated" class="flex items-center gap-2">
          <template v-if="user?.role === 'regular'">
            <router-link
              to="/chat"
              class="text-sm px-3 py-1 rounded"
              :class="$route.path === '/chat' ? 'bg-gray-900 text-white' : 'text-blue-600 hover:underline'"
            >
              Chat
            </router-link>
            <router-link
              to="/settings"
              class="text-sm px-3 py-1 rounded"
              :class="$route.path === '/settings' ? 'bg-gray-200 text-gray-900' : 'text-blue-600 hover:underline'"
            >
              Invite
            </router-link>
          </template>
          <template v-else>
            <router-link
              to="/dashboard"
              class="text-sm px-3 py-1 rounded"
              :class="$route.path === '/dashboard' ? 'bg-gray-900 text-white' : 'text-blue-600 hover:underline'"
            >
              Dashboard
            </router-link>
          </template>
        </div>
      </div>
      <div class="flex items-center gap-3">
        <span class="text-sm font-medium">{{ (user?.role || 'user').charAt(0).toUpperCase() + (user?.role?.slice(1) || 'User') }}</span>
        <button @click="logout" class="px-3 py-1 rounded bg-red-500 text-white text-sm">Logout</button>
      </div>
    </header>

    <main class="p-4">
      <router-view />
    </main>
  </div>
</template>

<style scoped></style>
