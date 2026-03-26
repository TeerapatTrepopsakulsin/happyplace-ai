<script setup lang="ts">
import { ref } from 'vue'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const email = ref('')
const password = ref('')
const display_name = ref('')
const role = ref<'regular' | 'therapist' | 'guardian'>('regular')
const error = ref('')

async function submit() {
  error.value = ''
  try {
    await auth.register(email.value, password.value, display_name.value, role.value)
  } catch (err: any) {
    error.value = auth.authError || 'Registration failed'
  }
}
</script>

<template>
  <div class="max-w-md mx-auto mt-12 bg-white p-8 rounded-lg shadow">
    <h1 class="text-xl font-semibold mb-4">Register</h1>
    <label class="block mb-2 text-sm">Display Name</label>
    <input v-model="display_name" class="w-full border rounded p-2 mb-3" />

    <label class="block mb-2 text-sm">Email</label>
    <input v-model="email" type="email" class="w-full border rounded p-2 mb-3" />

    <label class="block mb-2 text-sm">Password</label>
    <input v-model="password" type="password" class="w-full border rounded p-2 mb-3" />

    <label class="block mb-2 text-sm">Role</label>
    <select v-model="role" class="w-full border rounded p-2 mb-3">
      <option value="regular">Regular</option>
      <option value="therapist">Therapist</option>
      <option value="guardian">Guardian</option>
    </select>

    <button @click="submit" class="w-full bg-blue-500 text-white py-2 rounded">Register</button>

    <p v-if="error" class="text-red-600 mt-3 text-sm">{{ error }}</p>

    <p class="text-sm mt-4">
      Already have account? <router-link to="/login" class="text-blue-500">Login</router-link>
    </p>
  </div>
</template>
