<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import Password from 'primevue/password'
import { api } from '@/services/api'
import { useAuthStore } from '@/stores/auth'
import { useUiStore } from '@/stores/ui'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const ui = useUiStore()

const form = ref({
  email: '',
  password: '',
  first_name: '',
  last_name: '',
  referral_code: '',
})
const loading = ref(false)
const error = ref('')

onMounted(() => {
  const refCode = String(route.query.ref || '')
  if (refCode) form.value.referral_code = refCode
})

async function submit() {
  error.value = ''
  if (!form.value.email || form.value.password.length < 8) {
    error.value = 'Valid email and password (8+ chars) required'
    return
  }
  loading.value = true
  try {
    const { data } = await api.register(form.value)
    auth.token = data.token
    localStorage.setItem('ci_token', data.token)
    auth.user = data.user
    await auth.fetchMe()
    ui.toast('Welcome', 'Account created', 'success')
    router.push('/dashboard')
  } catch (e: any) {
    error.value = e?.response?.data?.email?.[0]
      || e?.response?.data?.detail
      || e?.response?.data?.password?.[0]
      || 'Registration failed'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="auth">
    <form class="card glass" @submit.prevent="submit">
      <div class="mark">C</div>
      <h1 class="gradient-text">Create account</h1>
      <p class="muted">Start investing in minutes</p>
      <div class="row">
        <InputText v-model="form.first_name" placeholder="First name" class="w-full" />
        <InputText v-model="form.last_name" placeholder="Last name" class="w-full" />
      </div>
      <InputText v-model="form.email" type="email" placeholder="Email" class="w-full" required />
      <Password v-model="form.password" placeholder="Password" toggle-mask class="w-full" input-class="w-full" />
      <InputText v-model="form.referral_code" placeholder="Referral code (optional)" class="w-full" />
      <p v-if="error" class="err">{{ error }}</p>
      <Button type="submit" label="Create account" icon="pi pi-user-plus" class="w-full" :loading="loading" />
      <RouterLink to="/login" class="back">Already have an account? Log in</RouterLink>
    </form>
  </div>
</template>

<style scoped>
.auth { min-height: 100dvh; display: grid; place-items: center; padding: 1.5rem; }
.card {
  width: min(440px, 100%);
  padding: 2rem 1.75rem;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  text-align: center;
}
.mark {
  width: 52px; height: 52px; margin: 0 auto;
  border-radius: 16px; display: flex; align-items: center; justify-content: center;
  font-weight: 800; color: #fff;
  background: linear-gradient(135deg, #3B82F6, #7C3AED);
}
h1 { font-size: 1.4rem; font-weight: 800; margin: 0; }
p { margin: 0; font-size: 0.92rem; }
.row { display: grid; grid-template-columns: 1fr 1fr; gap: 0.5rem; }
.w-full { width: 100%; }
.err { color: #F87171; font-size: 0.88rem; }
.back { color: #60A5FA; font-weight: 600; font-size: 0.9rem; margin-top: 0.25rem; }
:deep(.p-password) { width: 100%; }
</style>
