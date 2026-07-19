<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
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
import type { Cryptocurrency, Deposit } from '@/types/api'
import { useUiStore } from '@/stores/ui'

const router = useRouter()
const ui = useUiStore()
const rows = ref<Deposit[]>([])
const cryptos = ref<Cryptocurrency[]>([])
const loading = ref(true)
const open = ref(false)
const cryptoId = ref<number | null>(null)
const amount = ref<number | null>(null)
const txHash = ref('')
const promo = ref('')
const promoHint = ref('')
const submitting = ref(false)
const error = ref('')
const copied = ref(false)

const selectedCrypto = computed(() =>
  cryptos.value.find((c) => c.id === cryptoId.value) || null,
)

async function load() {
  loading.value = true
  try {
    const [d, c] = await Promise.all([api.deposits(), api.cryptocurrencies()])
    rows.value = unwrapList(d.data)
    cryptos.value = unwrapList(c.data as any)
  } finally {
    loading.value = false
  }
}

async function copyDepositAddr() {
  const addr = selectedCrypto.value?.deposit_address
  if (!addr) return
  try {
    await navigator.clipboard.writeText(addr)
    copied.value = true
    ui.toast('Copied', 'Deposit address copied', 'success')
    setTimeout(() => { copied.value = false }, 1600)
  } catch {
    ui.toast('Copy failed', 'Select the address manually', 'warn')
  }
}

async function checkPromo() {
  promoHint.value = ''
  if (!promo.value.trim() || !amount.value) return
  try {
    const { data } = await api.validatePromo(promo.value.trim(), amount.value)
    if (data.ok) promoHint.value = `Bonus ≈ ${data.bonus_amount}`
    else promoHint.value = data.detail || 'Invalid code'
  } catch (e: any) {
    promoHint.value = e?.response?.data?.detail || 'Invalid code'
  }
}

async function submit() {
  if (!cryptoId.value || !amount.value) return
  submitting.value = true
  error.value = ''
  try {
    const fd = new FormData()
    fd.append('cryptocurrency', String(cryptoId.value))
    fd.append('amount', String(amount.value))
    if (txHash.value) fd.append('transaction_hash', txHash.value)
    if (promo.value.trim()) fd.append('promo_code', promo.value.trim().toUpperCase())
    await api.createDeposit(fd)
    ui.toast('Deposit submitted', 'Awaiting admin approval.', 'success')
    open.value = false
    amount.value = null
    txHash.value = ''
    promo.value = ''
    promoHint.value = ''
    await load()
  } catch (e: any) {
    error.value = e?.response?.data?.detail || 'Could not submit deposit'
  } finally {
    submitting.value = false
  }
}

onMounted(load)
</script>

<template>
  <div>
    <PageHeader title="Deposits" subtitle="Crypto deposits credit after admin approval">
      <Button label="New deposit" icon="pi pi-plus" @click="open = true" />
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
          <template #body="{ data }"><span class="mono">{{ formatMoney(data.amount, 8) }} {{ data.crypto_symbol }}</span></template>
        </Column>
        <Column field="status" header="Status">
          <template #body="{ data }"><Tag :value="data.status" :severity="statusSeverity(data.status)" /></template>
        </Column>
        <Column field="transaction_hash" header="Tx hash">
          <template #body="{ data }"><span class="mono muted small">{{ data.transaction_hash || '—' }}</span></template>
        </Column>
        <Column header="" style="width:6rem">
          <template #body="{ data }">
            <Button
              label="Receipt"
              size="small"
              text
              icon="pi pi-file"
              @click="router.push(`/receipts/deposit/${data.id}`)"
            />
          </template>
        </Column>
      </DataTable>
      <EmptyState v-else-if="!loading" title="No deposits yet" text="Submit a crypto deposit to fund your wallet.">
        <Button label="New deposit" icon="pi pi-plus" @click="open = true" />
      </EmptyState>
    </div>

    <Dialog v-model:visible="open" modal header="New deposit" :style="{ width: 'min(440px, 95vw)' }">
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
        <div v-if="selectedCrypto?.deposit_address" class="dep-qr">
          <div class="dep-qr-frame">
            <img
              v-if="selectedCrypto.qr"
              :src="selectedCrypto.qr"
              :alt="`${selectedCrypto.symbol} QR`"
              class="dep-qr-img"
            />
            <i v-else class="pi pi-qrcode muted" />
          </div>
          <div class="dep-qr-meta">
            <strong class="asset-cell">
              <CryptoIcon :symbol="selectedCrypto.symbol" :icon="selectedCrypto.icon" size="sm" />
              {{ selectedCrypto.symbol }} · {{ selectedCrypto.network }}
            </strong>
            <p class="mono addr">{{ selectedCrypto.deposit_address }}</p>
            <Button
              :label="copied ? 'Copied' : 'Copy address'"
              :icon="copied ? 'pi pi-check' : 'pi pi-copy'"
              size="small"
              text
              @click="copyDepositAddr"
            />
          </div>
        </div>
        <label>
          <span>Amount</span>
          <InputNumber v-model="amount" mode="decimal" :min-fraction-digits="2" :max-fraction-digits="8" fluid />
        </label>
        <label>
          <span>Transaction hash (optional)</span>
          <InputText v-model="txHash" class="w-full" placeholder="0x… / on-chain hash" />
        </label>
        <label>
          <span>Promo code (optional)</span>
          <InputText v-model="promo" class="w-full" placeholder="WELCOME10" @blur="checkPromo" />
          <small v-if="promoHint" class="hint">{{ promoHint }}</small>
        </label>
        <Button label="Submit deposit" icon="pi pi-check" class="w-full" :loading="submitting" @click="submit" />
      </div>
    </Dialog>
  </div>
</template>

<style scoped>
.panel { padding: 0.75rem; }
.form { display: grid; gap: 0.85rem; }
.form label { display: grid; gap: 0.35rem; }
.form > label > span { font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.04em; color: var(--ci-muted); font-weight: 600; }
.w-full { width: 100%; }
.mb { margin-bottom: 0.75rem; }
.small { font-size: 0.78rem; }
.hint { color: var(--ci-success); font-size: 0.8rem; }
.asset-cell {
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
}
.asset-cell .net { font-size: 0.75rem; margin-left: 0.1rem; }
.dep-qr {
  display: grid;
  grid-template-columns: 96px 1fr;
  gap: 0.75rem;
  align-items: center;
  padding: 0.65rem;
  border-radius: 12px;
  border: 1px solid var(--ci-border);
  background: rgba(255,255,255,0.03);
}
.dep-qr-frame {
  width: 96px;
  height: 96px;
  border-radius: 10px;
  background: #fff;
  display: grid;
  place-items: center;
  padding: 6px;
}
.dep-qr-img { width: 100%; height: 100%; object-fit: contain; }
.dep-qr-meta strong { font-size: 0.9rem; }
.addr {
  word-break: break-all;
  font-size: 0.78rem;
  margin: 0.35rem 0 0.15rem;
  color: var(--ci-muted);
}
</style>
