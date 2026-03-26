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
    <header class="bg-white border-b border-gray-200 p-4 flex justify-between items-center">
      <div class="text-xl font-semibold">HappyPlaceAI</div>
      <div v-if="isAuthenticated" class="flex items-center gap-3">
        <span class="text-sm">{{ user?.role || 'user' }}</span>
        <button @click="logout" class="px-3 py-1 rounded bg-red-500 text-white text-sm">Logout</button>
      </div>
    </header>

    <main class="p-4">
      <router-view />
    </main>
  </div>
</template>

<style scoped></style>
