<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import InputText from 'primevue/inputtext'
import Password from 'primevue/password'
import Button from 'primevue/button'

const auth = useAuthStore()
const router = useRouter()
const username = ref('')
const password = ref('')
const error = ref('')

async function handleLogin() {
  try {
    error.value = ''
    await auth.login(username.value, password.value)
    router.push('/')
  } catch (e) {
    error.value = e.message
  }
}
</script>

<template>
  <div class="login-container">
    <div class="login-card">
      <h1>Hermes Web Client</h1>
      <form @submit.prevent="handleLogin">
        <div class="field">
          <InputText v-model="username" placeholder="Username" />
        </div>
        <div class="field">
          <Password v-model="password" placeholder="Password" :feedback="false" />
        </div>
        <Button type="submit" label="Log in" />
      </form>
      <p v-if="error" class="error">{{ error }}</p>
    </div>
  </div>
</template>

<style scoped>
.login-container { display: flex; justify-content: center; align-items: center; height: 100vh; }
.login-card { width: 320px; text-align: center; }
.field { margin-bottom: 1rem; }
.error { color: red; }
</style>
