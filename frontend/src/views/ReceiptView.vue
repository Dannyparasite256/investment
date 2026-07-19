<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import Button from 'primevue/button'
import Tag from 'primevue/tag'
import Skeleton from 'primevue/skeleton'
import PageHeader from '@/components/ui/PageHeader.vue'
import { api } from '@/services/api'
import { statusSeverity } from '@/utils/money'
import type { ReceiptData } from '@/types/api'

const route = useRoute()
const router = useRouter()
const loading = ref(true)
const receipt = ref<ReceiptData | null>(null)
const error = ref('')

const kind = computed(() => String(route.params.kind || 'deposit'))
const id = computed(() => String(route.params.id || ''))

async function load() {
  loading.value = true
  error.value = ''
  try {
    let data: ReceiptData
    const k = kind.value
    if (k === 'withdrawal') data = (await api.withdrawalReceipt(id.value)).data
    else if (k === 'transaction') data = (await api.transactionReceipt(id.value)).data
    else if (k === 'investment') data = (await api.investmentReceipt(id.value)).data
    else if (k === 'earning' || k === 'profit') data = (await api.earningReceipt(id.value)).data
    else if (k === 'referral') data = (await api.referralReceipt(id.value)).data
    else data = (await api.depositReceipt(id.value)).data
    receipt.value = data
  } catch {
    error.value = 'Receipt not found'
    receipt.value = null
  } finally {
    loading.value = false
  }
}

function print() {
  if (receipt.value?.print_url) {
    window.open(receipt.value.print_url, '_blank')
    return
  }
  window.print()
}

onMounted(load)
watch(() => [route.params.kind, route.params.id], load)
</script>

<template>
  <div class="receipt-page">
    <PageHeader :title="receipt?.title || 'Receipt'" :subtitle="receipt ? `Display · ${receipt.display_currency}` : ''">
      <Button label="Back" icon="pi pi-arrow-left" text @click="router.back()" />
      <Button label="Print / PDF" icon="pi pi-print" outlined @click="print" />
    </PageHeader>

    <Skeleton v-if="loading" height="360px" border-radius="18px" />
    <div v-else-if="error" class="glass card err">{{ error }}</div>
    <div v-else-if="receipt" class="glass card receipt" id="receipt-print">
      <div class="head">
        <div>
          <div class="brand gradient-text">CryptoInvest</div>
          <div class="muted small">Official receipt</div>
        </div>
        <Tag :value="receipt.status_label" :severity="statusSeverity(receipt.status)" />
      </div>
      <div class="amount mono">{{ receipt.amount?.label }}</div>
      <div class="muted center">{{ receipt.kind }} · {{ receipt.id }}</div>
      <table>
        <tbody>
          <tr v-for="(r, i) in receipt.rows" :key="i">
            <th>{{ r.label }}</th>
            <td>{{ r.value }}</td>
          </tr>
        </tbody>
      </table>
      <p class="muted small foot">
        Amounts shown in {{ receipt.display_currency }} using live rates at time of viewing.
        Platform ledger is USD-equivalent.
      </p>
    </div>
  </div>
</template>

<style scoped>
.card { padding: 1.5rem; max-width: 560px; }
.receipt { margin: 0 auto; }
.head { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 1rem; }
.brand { font-size: 1.25rem; font-weight: 800; }
.amount {
  font-size: clamp(1.6rem, 4vw, 2.1rem);
  font-weight: 800;
  text-align: center;
  margin: 0.5rem 0 0.25rem;
}
.center { text-align: center; margin-bottom: 1.25rem; font-size: 0.85rem; word-break: break-all; }
table { width: 100%; border-collapse: collapse; }
th, td {
  padding: 0.55rem 0.25rem;
  border-bottom: 1px solid var(--ci-border);
  font-size: 0.9rem;
  text-align: left;
  vertical-align: top;
}
th { color: var(--ci-muted); font-weight: 600; width: 38%; }
.foot { margin-top: 1rem; }
.err { color: #F87171; }
.small { font-size: 0.82rem; }
@media print {
  .receipt-page :deep(.hdr),
  .receipt-page :deep(.actions) { display: none !important; }
  .receipt { box-shadow: none; border: 1px solid #ddd; }
}
</style>
