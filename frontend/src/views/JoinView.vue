<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import Button from 'primevue/button'
import { api, unwrapList } from '@/services/api'
import { formatMoney } from '@/utils/money'

const route = useRoute()
const router = useRouter()
const plans = ref<any[]>([])
const code = computed(() => String(route.query.ref || route.params.code || ''))

onMounted(async () => {
  try {
    const { data } = await api.plans()
    plans.value = unwrapList(data).slice(0, 3)
  } catch { /* may require auth */ }
  if (code.value) localStorage.setItem('ci_ref', code.value)
})
</script>

<template>
  <div class="join">
    <div class="hero glass">
      <h1>Invest with CryptoInvest</h1>
      <p class="muted">
        Join via referral <strong>{{ code || 'link' }}</strong> and start growing with flexible plans.
      </p>
      <div class="actions">
        <Button
          label="Create account"
          icon="pi pi-user-plus"
          @click="router.push({ path: '/register', query: code ? { ref: code } : {} })"
        />
        <Button label="Log in" text @click="router.push('/login')" />
      </div>
    </div>
    <div class="plans">
      <div v-for="p in plans" :key="p.id" class="glass plan">
        <h3>{{ p.name }}</h3>
        <p class="muted">From {{ formatMoney(p.min_deposit) }} · {{ p.duration_days }} days</p>
        <p>{{ p.short_description || p.expected_return }}</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.join { max-width: 720px; margin: 0 auto; padding: 1.5rem; }
.hero { padding: 1.5rem; border-radius: 18px; margin-bottom: 1rem; text-align: center; }
.actions { display: flex; gap: 0.5rem; justify-content: center; margin-top: 1rem; flex-wrap: wrap; }
.plans { display: grid; gap: 0.75rem; }
.plan { padding: 1rem; border-radius: 14px; }
</style>
