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
    
  } catch (err: any) {
    error.value = auth.authError || 'Login failed'
  }
}
</script>

<template>
  <div class="max-w-md mx-auto mt-12 bg-white p-8 rounded-lg shadow">
    <h1 class="text-xl font-semibold mb-4">Login</h1>
    <label class="block mb-2 text-sm">Email</label>
    <input v-model="email" type="email" class="w-full border rounded p-2 mb-3" />

    <label class="block mb-2 text-sm">Password</label>
    <input v-model="password" type="password" class="w-full border rounded p-2 mb-3" />

    <button @click="submit" class="w-full bg-blue-500 text-white py-2 rounded">Log In</button>

    <p v-if="error" class="text-red-600 mt-3 text-sm">{{ error }}</p>

    <p class="text-sm mt-4">
      Don’t have an account? <router-link to="/register" class="text-blue-500">Register</router-link>
    </p>
  </div>
</template>
