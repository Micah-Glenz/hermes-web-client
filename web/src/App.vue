<script setup>
import { onMounted } from 'vue'
import { useAuthStore } from './stores/auth'
import Toast from 'primevue/toast'
import ToastService from 'primevue/toastservice'

const auth = useAuthStore()

onMounted(() => {
  auth.checkSession()
})
</script>

<template>
  <ToastService>
    <Toast />
    <router-view />
  </ToastService>
</template>
