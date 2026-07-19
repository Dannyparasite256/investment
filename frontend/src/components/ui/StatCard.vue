<script setup lang="ts">
defineProps<{
  label: string
  value: string
  hint?: string
  icon?: string
  tone?: 'default' | 'success' | 'danger' | 'gold'
}>()
</script>

<template>
  <div class="card glass" :class="tone || 'default'">
    <div class="row">
      <div>
        <div class="stat-label">{{ label }}</div>
        <div class="value mono">{{ value }}</div>
        <div v-if="hint" class="hint muted">{{ hint }}</div>
      </div>
      <div v-if="icon" class="icon"><i :class="icon" /></div>
    </div>
  </div>
</template>

<style scoped>
.card {
  padding: 1.15rem 1.2rem;
  transition: transform 0.2s ease, border-color 0.2s ease;
}
.card:hover {
  transform: translateY(-3px);
  border-color: rgba(59, 130, 246, 0.35);
}
.row {
  display: flex;
  justify-content: space-between;
  gap: 0.75rem;
  align-items: flex-start;
}
.value {
  font-size: clamp(1.25rem, 2.2vw, 1.6rem);
  font-weight: 750;
  letter-spacing: -0.04em;
  margin-top: 0.35rem;
}
.hint {
  font-size: 0.78rem;
  margin-top: 0.25rem;
}
.icon {
  width: 42px;
  height: 42px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(59, 130, 246, 0.12);
  color: #60A5FA;
  border: 1px solid rgba(96, 165, 250, 0.2);
}
.success .value { color: var(--ci-success); }
.danger .value { color: var(--ci-danger); }
.gold .value { color: var(--ci-gold); }
@media (max-width: 640px) {
  .card { padding: 0.85rem 0.8rem; }
  .value { font-size: 1.15rem; word-break: break-word; }
  .icon { width: 36px; height: 36px; border-radius: 10px; }
  .icon i { font-size: 0.95rem; }
  .card:hover { transform: none; }
}
</style>
