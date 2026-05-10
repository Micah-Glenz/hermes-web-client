<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useAuthStore } from '../stores/auth'
import { createGateway } from '../services/gateway'
import Button from 'primevue/button'

const auth = useAuthStore()
const events = ref([])
const connected = ref(false)
let gw = null

onMounted(() => {
  if (!auth.isAuthenticated) return

  gw = createGateway(auth.token, {
    auth_ok: () => { connected.value = true },
    pong: (data) => { events.value.push(data) },
    onclose: () => { connected.value = false },
  })
})

onUnmounted(() => {
  if (gw) gw.socket.close()
})
</script>

<template>
  <div class="layout">
    <header class="topbar">
      <span>Hermes Web Client</span>
      <span :class="connected ? 'connected' : 'disconnected'">
        {{ connected ? 'Connected' : 'Disconnected' }}
      </span>
      <Button label="Logout" @click="auth.logout()" />
    </header>
    <main>
      <p>Gateway connected. Sessions will appear here.</p>
      <pre>{{ events }}</pre>
    </main>
  </div>
</template>

<style scoped>
.topbar { display: flex; justify-content: space-between; padding: 1rem; border-bottom: 1px solid #ccc; }
.connected { color: green; }
.disconnected { color: red; }
</style>
