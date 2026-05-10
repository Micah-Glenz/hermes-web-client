import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { api } from '../services/api'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(null)
  const isAuthenticated = computed(() => !!token.value)

  async function login(username, password) {
    const res = await api.post('/api/auth/login', { username, password })
    token.value = res.access
    localStorage.setItem('jwt', res.access)
  }

  function logout() {
    token.value = null
    localStorage.removeItem('jwt')
  }

  function checkSession() {
    const saved = localStorage.getItem('jwt')
    if (saved) token.value = saved
  }

  return { token, isAuthenticated, login, logout, checkSession }
})
