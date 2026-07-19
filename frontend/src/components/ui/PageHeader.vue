<script setup lang="ts">
defineProps<{ title: string; subtitle?: string }>()
</script>

<template>
  <div class="hdr">
    <div>
      <h1>{{ title }}</h1>
      <p v-if="subtitle" class="muted">{{ subtitle }}</p>
    </div>
    <div class="actions">
      <slot />
    </div>
  </div>
</template>

<style scoped>
.hdr {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 0.85rem;
  flex-wrap: wrap;
  margin-bottom: 1.15rem;
}
h1 {
  font-size: clamp(1.25rem, 2.5vw, 1.75rem);
  font-weight: 800;
  line-height: 1.2;
  word-break: break-word;
}
p {
  margin: 0.2rem 0 0;
  font-size: 0.9rem;
}
.actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.45rem;
  align-items: center;
}
@media (max-width: 640px) {
  .hdr {
    flex-direction: column;
    align-items: stretch;
    gap: 0.65rem;
    margin-bottom: 0.85rem;
  }
  h1 { font-size: 1.28rem; }
  p { font-size: 0.82rem; }
  .actions {
    width: 100%;
  }
  .actions :deep(.p-button) {
    flex: 1 1 auto;
    justify-content: center;
  }
  .actions :deep(.p-select),
  .actions :deep(.p-inputtext) {
    flex: 1 1 100%;
    width: 100% !important;
    max-width: 100%;
  }
}
</style>
