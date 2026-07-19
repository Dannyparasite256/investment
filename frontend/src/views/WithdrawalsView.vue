<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Tag from 'primevue/tag'
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import Select from 'primevue/select'
import InputNumber from 'primevue/inputnumber'
import InputText from 'primevue/inputtext'
import Message from 'primevue/message'
import PageHeader from '@/components/ui/PageHeader.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import CryptoIcon from '@/components/ui/CryptoIcon.vue'
import CryptoLabel from '@/components/ui/CryptoLabel.vue'
import { api, unwrapList } from '@/services/api'
import { formatMoney, shortDate, statusSeverity } from '@/utils/money'
import type { Cryptocurrency, Withdrawal } from '@/types/api'
import { useAuthStore } from '@/stores/auth'
import { useUiStore } from '@/stores/ui'

const auth = useAuthStore()
const ui = useUiStore()
const router = useRouter()
const rows = ref<Withdrawal[]>([])
const cryptos = ref<Cryptocurrency[]>([])
const loading = ref(true)
const open = ref(false)
const cryptoId = ref<number | null>(null)
const amount = ref<number | null>(null)
const address = ref('')
const submitting = ref(false)
const error = ref('')

async function load() {
  loading.value = true
  try {
    const [w, c] = await Promise.all([api.withdrawals(), api.cryptocurrencies()])
    rows.value = unwrapList(w.data)
    cryptos.value = unwrapList(c.data as any)
  } finally {
    loading.value = false
  }
}

async function submit() {
  if (!cryptoId.value || !amount.value || !address.value) return
  submitting.value = true
  error.value = ''
  try {
    await api.createWithdrawal({
      cryptocurrency: cryptoId.value,
      amount: amount.value,
      wallet_address: address.value,
    })
    await auth.refreshWallet()
    ui.toast('Withdrawal requested', 'Pending admin review.', 'success')
    open.value = false
    amount.value = null
    address.value = ''
    await load()
  } catch (e: any) {
    error.value = e?.response?.data?.detail || 'Could not submit withdrawal'
  } finally {
    submitting.value = false
  }
}

onMounted(load)
</script>

<template>
  <div>
    <PageHeader title="Withdrawals" :subtitle="`Available ${formatMoney(auth.wallet?.available_balance ?? 0)}`">
      <Button label="New withdrawal" icon="pi pi-plus" @click="open = true" />
    </PageHeader>
    <div class="glass panel">
      <DataTable v-if="rows.length" :value="rows" paginator :rows="10" :loading="loading">
        <Column field="created_at" header="Date">
          <template #body="{ data }">{{ shortDate(data.created_at) }}</template>
        </Column>
        <Column field="crypto_symbol" header="Asset">
          <template #body="{ data }">
            <CryptoLabel :symbol="data.crypto_symbol" size="sm" />
          </template>
        </Column>
        <Column field="amount" header="Amount">
          <template #body="{ data }"><span class="mono">{{ formatMoney(data.amount) }}</span></template>
        </Column>
        <Column field="wallet_address" header="Address">
          <template #body="{ data }"><span class="mono small muted">{{ data.wallet_address?.slice(0, 14) }}…</span></template>
        </Column>
        <Column field="status" header="Status">
          <template #body="{ data }"><Tag :value="data.status" :severity="statusSeverity(data.status)" /></template>
        </Column>
        <Column header="" style="width:6rem">
          <template #body="{ data }">
            <Button label="Receipt" size="small" text icon="pi pi-file" @click="router.push(`/receipts/withdrawal/${data.id}`)" />
          </template>
        </Column>
      </DataTable>
      <EmptyState v-else-if="!loading" title="No withdrawals yet" text="Request a payout to your external wallet.">
        <Button label="New withdrawal" icon="pi pi-plus" @click="open = true" />
      </EmptyState>
    </div>

    <Dialog v-model:visible="open" modal header="New withdrawal" :style="{ width: 'min(440px, 95vw)' }">
      <Message v-if="error" severity="error" class="mb" :closable="false">{{ error }}</Message>
      <div class="form">
        <label>
          <span>Cryptocurrency</span>
          <Select v-model="cryptoId" :options="cryptos" option-label="symbol" option-value="id" placeholder="Select asset" class="w-full">
            <template #value="{ value }">
              <span v-if="value" class="asset-cell">
                <CryptoIcon
                  :symbol="cryptos.find((c) => c.id === value)?.symbol"
                  :icon="cryptos.find((c) => c.id === value)?.icon"
                  size="sm"
                />
                <span>{{ cryptos.find((c) => c.id === value)?.symbol || value }}</span>
              </span>
              <span v-else class="muted">Select asset</span>
            </template>
            <template #option="{ option }">
              <span class="asset-cell">
                <CryptoIcon :symbol="option.symbol" :icon="option.icon" size="sm" />
                <span>{{ option.symbol }}</span>
                <span class="muted net">{{ option.network }}</span>
              </span>
            </template>
          </Select>
        </label>
        <label>
          <span>Amount (platform units)</span>
          <InputNumber v-model="amount" mode="decimal" :min-fraction-digits="2" :max-fraction-digits="8" fluid />
        </label>
        <label>
          <span>Wallet address</span>
          <InputText v-model="address" class="w-full" placeholder="Destination address" />
        </label>
        <Button label="Request withdrawal" icon="pi pi-check" class="w-full" :loading="submitting" @click="submit" />
      </div>
    </Dialog>
  </div>
</template>

<style scoped>
.panel { padding: 0.75rem; }
.form { display: grid; gap: 0.85rem; }
.form label { display: grid; gap: 0.35rem; }
.form > label > span { font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.04em; color: var(--ci-muted); font-weight: 600; }
.asset-cell {
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
}
.asset-cell .net { font-size: 0.75rem; margin-left: 0.1rem; }
.w-full { width: 100%; }
.mb { margin-bottom: 0.75rem; }
.small { font-size: 0.78rem; }
</style>
