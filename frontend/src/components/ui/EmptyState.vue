<script setup lang="ts">
defineProps<{ title: string; text?: string; icon?: string }>()
</script>

<template>
  <div class="empty">
    <div class="icon"><i :class="icon || 'pi pi-inbox'" /></div>
    <h3>{{ title }}</h3>
    <p v-if="text" class="muted">{{ text }}</p>
    <div class="actions"><slot /></div>
  </div>
</template>

<style scoped>
.empty {
  text-align: center;
  padding: 2.5rem 1rem;
}
.icon {
  width: 56px;
  height: 56px;
  margin: 0 auto 0.85rem;
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(59, 130, 246, 0.12);
  color: #60A5FA;
  font-size: 1.35rem;
}
h3 {
  font-size: 1.05rem;
  margin-bottom: 0.35rem;
}
p {
  font-size: 0.9rem;
  max-width: 28rem;
  margin: 0 auto;
}
.actions {
  margin-top: 1rem;
  display: flex;
  justify-content: center;
  gap: 0.5rem;
  flex-wrap: wrap;
}
</style>
