<script setup lang="ts">
import { ref } from 'vue'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const email = ref('')
const password = ref('')
const error = ref('')

async function submit() {
  error.value = ''
  try {
    await auth.login(email.value, password.value)
  } catch {
    error.value = auth.authError || 'Login failed'
  }
}
</script>

<template>
  <div
    class="max-w-md mx-auto mt-12 bg-slate-800/80 backdrop-blur-md p-8 rounded-2xl shadow-2xl border border-slate-700/50"
  >
    <h1
      class="text-2xl font-bold mb-6 text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 to-cyan-400"
    >
      Login
    </h1>

    <label class="block mb-2 text-sm font-medium text-slate-300">Email</label>
    <input
      v-model="email"
      type="email"
      class="w-full bg-slate-900/50 border border-slate-600 text-slate-200 rounded-lg p-3 mb-4 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none transition-all duration-200 placeholder-slate-500"
      placeholder="Enter your email"
    />

    <label class="block mb-2 text-sm font-medium text-slate-300">Password</label>
    <input
      v-model="password"
      type="password"
      class="w-full bg-slate-900/50 border border-slate-600 text-slate-200 rounded-lg p-3 mb-6 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none transition-all duration-200 placeholder-slate-500"
      placeholder="••••••••"
    />

    <button
      @click="submit"
      class="w-full bg-indigo-600 hover:bg-indigo-500 text-white font-medium py-3 rounded-lg shadow-lg shadow-indigo-500/25 transition-all duration-200 transform hover:-translate-y-0.5"
    >
      Log In
    </button>

    <p
      v-if="error"
      class="text-red-400 mt-4 text-sm bg-red-900/20 border border-red-500/20 p-3 rounded-lg"
    >
      {{ error }}
    </p>

    <p class="text-sm mt-6 text-slate-400 text-center">
      Don’t have an account?
      <router-link
        to="/register"
        class="text-cyan-400 hover:text-cyan-300 hover:underline font-medium transition-colors"
        >Register</router-link
      >
    </p>
  </div>
</template>
