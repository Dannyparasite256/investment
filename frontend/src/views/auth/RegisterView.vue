<script setup lang="ts">
import Button from 'primevue/button'
</script>

<template>
  <div class="auth">
    <div class="card glass">
      <div class="mark">C</div>
      <h1 class="gradient-text">Create account</h1>
      <p class="muted">
        Registration uses the secure Django form to preserve email verification, KYC, and referral logic.
      </p>
      <div class="actions">
        <Button as="a" href="/accounts/register/" label="Continue to register" icon="pi pi-user-plus" class="w-full" />
        <RouterLink to="/login" class="back">Back to login</RouterLink>
      </div>
    </div>
  </div>
</template>

<style scoped>
.auth {
  min-height: 100dvh;
  display: grid;
  place-items: center;
  padding: 1.5rem;
}
.card {
  width: min(420px, 100%);
  padding: 2rem 1.75rem;
  text-align: center;
}
.mark {
  width: 52px;
  height: 52px;
  margin: 0 auto 0.75rem;
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 800;
  color: #fff;
  background: linear-gradient(135deg, #3B82F6, #7C3AED);
}
h1 { font-size: 1.4rem; font-weight: 800; margin-bottom: 0.5rem; }
p { margin: 0 0 1.25rem; font-size: 0.92rem; line-height: 1.5; }
.actions { display: grid; gap: 0.75rem; }
.w-full { width: 100%; }
.back {
  text-align: center;
  color: #60A5FA;
  font-weight: 600;
  font-size: 0.9rem;
}
</style>
