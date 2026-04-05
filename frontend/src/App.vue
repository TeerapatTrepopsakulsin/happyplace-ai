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
  <div class="min-h-screen bg-gradient-to-b from-slate-900 to-gray-900 text-slate-200 font-sans selection:bg-indigo-500/30">
    <header class="bg-slate-900/80 backdrop-blur-md border-b border-slate-800 p-4 flex items-center justify-between sticky top-0 z-50 shadow-sm">
      <div class="flex items-center gap-6">
        <div class="flex items-center gap-2 text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-indigo-400 to-cyan-400">
          <img src="/happyplacelogo-bw.png" alt="Happy Place Logo" class="w-7 h-7 object-contain" />
          HappyPlaceAI
        </div>
        <div v-if="isAuthenticated" class="flex items-center gap-3">
          <template v-if="user?.role === 'regular'">
            <router-link
              to="/chat"
              class="text-sm px-4 py-2 rounded-lg font-medium transition-all duration-200 flex items-center gap-2"
              :class="$route.path === '/chat' ? 'bg-slate-700 text-white shadow-md' : 'text-slate-300 hover:text-white hover:bg-slate-800'"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"></path></svg>
              Chat
            </router-link>
            <router-link
              to="/settings"
              class="text-sm px-4 py-2 rounded-lg font-medium transition-all duration-200 flex items-center gap-2"
              :class="$route.path === '/settings' ? 'bg-slate-700 text-white shadow-md' : 'text-slate-300 hover:text-white hover:bg-slate-800'"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z"></path></svg>
              Invite
            </router-link>
          </template>
          <template v-else>
            <router-link
              to="/dashboard"
              class="text-sm px-4 py-2 rounded-lg font-medium transition-all duration-200 flex items-center gap-2"
              :class="$route.path === '/dashboard' ? 'bg-slate-700 text-white shadow-md' : 'text-slate-300 hover:text-white hover:bg-slate-800'"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"></path></svg>
              Dashboard
            </router-link>
          </template>
        </div>
      </div>
      <div v-if="isAuthenticated" class="flex items-center">
        <button @click="logout" class="px-4 py-2 rounded-lg bg-red-500/10 text-red-400 hover:bg-red-500 hover:text-white border border-red-500/20 hover:border-transparent transition-all duration-200 text-sm font-medium focus:ring-2 focus:ring-red-500/50 outline-none flex items-center gap-2">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"></path></svg>
          Logout
        </button>
      </div>
    </header>

    <main class="p-4 md:p-6 lg:p-8 max-w-screen-2xl mx-auto">
      <router-view />
    </main>
  </div>
</template>

<style scoped></style>
