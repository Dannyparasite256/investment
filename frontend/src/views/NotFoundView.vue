<script setup lang="ts">
import Button from 'primevue/button'
import { useRouter } from 'vue-router'
const router = useRouter()
</script>

<template>
  <div class="wrap">
    <div class="glass card">
      <h1 class="gradient-text">404</h1>
      <p class="muted">This page doesn’t exist in the app shell.</p>
      <Button label="Go to dashboard" icon="pi pi-home" @click="router.push('/dashboard')" />
    </div>
  </div>
</template>

<style scoped>
.wrap {
  min-height: 100dvh;
  display: grid;
  place-items: center;
  padding: 1.5rem;
}
.card {
  padding: 2rem;
  text-align: center;
  width: min(400px, 100%);
}
h1 {
  font-size: 3rem;
  font-weight: 900;
  margin-bottom: 0.5rem;
}
p { margin: 0 0 1.25rem; }
</style>
