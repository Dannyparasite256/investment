<script setup lang="ts">
import { onMounted, ref } from 'vue'
import Button from 'primevue/button'
import Select from 'primevue/select'
import PageHeader from '@/components/ui/PageHeader.vue'
import { api } from '@/services/api'
import { useAuthStore } from '@/stores/auth'
import { useUiStore } from '@/stores/ui'

const auth = useAuthStore()
const ui = useUiStore()
const questions = ref<any[]>([])
const answers = ref<Record<string, number>>({})
const result = ref<{ score: number; profile: string; tip: string } | null>(null)
const loading = ref(false)

onMounted(async () => {
  const { data } = await api.riskQuiz()
  questions.value = data.questions || []
})

async function submit() {
  loading.value = true
  try {
    const { data } = await api.submitRiskQuiz(answers.value)
    result.value = data as any
    await auth.fetchMe()
    ui.toast('Saved', `Risk profile: ${(data as any).profile}`, 'success')
  } catch {
    ui.toast('Failed', 'Could not save quiz', 'error')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div>
    <PageHeader title="Risk profile" subtitle="Help us tailor plan suggestions" />
    <div class="glass card">
      <p class="muted">Current score: <strong>{{ auth.user?.risk_score ?? 0 }}</strong></p>
      <div v-for="q in questions" :key="q.id" class="q">
        <div class="q-text">{{ q.text }}</div>
        <Select
          v-model="answers[q.id]"
          :options="q.options"
          option-label="label"
          option-value="value"
          placeholder="Select…"
          class="w-full"
        />
      </div>
      <Button label="Calculate profile" icon="pi pi-check" class="mt" :loading="loading" @click="submit" />
      <div v-if="result" class="result">
        <h3>{{ result.profile }} · {{ result.score }}</h3>
        <p class="muted">{{ result.tip }}</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.card { padding: 1.15rem; max-width: 640px; }
.q { margin-top: 1rem; }
.q-text { font-weight: 650; margin-bottom: 0.4rem; }
.mt { margin-top: 1.15rem; }
.result {
  margin-top: 1.15rem;
  padding: 1rem;
  border-radius: 14px;
  background: rgba(59, 130, 246, 0.1);
  border: 1px solid rgba(59, 130, 246, 0.25);
}
</style>
