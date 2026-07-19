<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import Button from 'primevue/button'
import Select from 'primevue/select'
import PageHeader from '@/components/ui/PageHeader.vue'
import StatCard from '@/components/ui/StatCard.vue'
import CryptoIcon from '@/components/ui/CryptoIcon.vue'
import CryptoLabel from '@/components/ui/CryptoLabel.vue'
import { useAuthStore } from '@/stores/auth'
import { useCurrencyStore } from '@/stores/currency'
import { formatDisplay, formatMoney } from '@/utils/money'
import { useUiStore } from '@/stores/ui'
import { api, unwrapList } from '@/services/api'
import type { Cryptocurrency } from '@/types/api'

const auth = useAuthStore()
const currency = useCurrencyStore()
const router = useRouter()
const ui = useUiStore()

const cryptos = ref<Cryptocurrency[]>([])
const selectedId = ref<number | null>(null)
const loadingCrypto = ref(true)
const copied = ref(false)

const selected = computed(() =>
  cryptos.value.find((c) => c.id === selectedId.value) || null,
)

const depositAssets = computed(() =>
  cryptos.value.filter((c) => c.is_active && (c.deposit_address || '').trim()),
)

onMounted(async () => {
  await auth.refreshWallet()
  if (!currency.options.length) await currency.init()
  else await currency.refreshBalances()
  try {
    const { data } = await api.cryptocurrencies()
    cryptos.value = unwrapList(data as any)
    if (depositAssets.value.length) {
      selectedId.value = depositAssets.value[0].id
    }
  } finally {
    loadingCrypto.value = false
  }
})

async function onCurrency(code: string) {
  const ok = await currency.setCurrency(code)
  if (ok) ui.toast('Currency', `Showing balances in ${code}`, 'success')
}

async function copyAddress() {
  const addr = selected.value?.deposit_address
  if (!addr) return
  try {
    await navigator.clipboard.writeText(addr)
    copied.value = true
    ui.toast('Copied', 'Deposit address copied', 'success')
    setTimeout(() => { copied.value = false }, 1800)
  } catch {
    ui.toast('Copy failed', 'Select the address and copy manually', 'warn')
  }
}
</script>

<template>
  <div>
    <PageHeader title="Wallet" subtitle="Balances in your display currency (live rates)">
      <Select
        :model-value="currency.code"
        :options="currency.options"
        option-label="label"
        option-value="code"
        placeholder="Currency"
        class="fx"
        :loading="currency.switching"
        @update:model-value="onCurrency"
      >
        <template #value="{ value }">
          <span v-if="value" class="opt-row">
            <CryptoIcon :symbol="value" size="sm" />
            <span>{{ currency.options.find((o) => o.code === value)?.label || value }}</span>
          </span>
          <span v-else class="muted">Currency</span>
        </template>
        <template #option="{ option }">
          <span class="opt-row">
            <CryptoIcon :symbol="option.code" size="sm" />
            <span>{{ option.label }}</span>
          </span>
        </template>
      </Select>
      <Button label="Deposit" icon="pi pi-download" @click="router.push('/deposits')" />
      <Button label="Withdraw" icon="pi pi-upload" outlined @click="router.push('/withdrawals')" />
    </PageHeader>
    <div class="grid-stats">
      <StatCard label="Balance" :value="formatDisplay(currency.balances?.balance)" icon="pi pi-wallet" />
      <StatCard label="Available" :value="formatDisplay(currency.balances?.available)" icon="pi pi-check-circle" tone="success" />
      <StatCard label="Locked" :value="formatDisplay(currency.balances?.locked)" icon="pi pi-lock" />
      <StatCard label="Profit" :value="formatDisplay(currency.balances?.profit)" icon="pi pi-chart-line" tone="gold" />
    </div>

    <div class="glass panel qr-panel">
      <div class="qr-head">
        <div>
          <h3>Deposit QR</h3>
          <p class="muted small">Scan to send crypto to the platform wallet for the selected asset.</p>
        </div>
        <Select
          v-if="depositAssets.length"
          v-model="selectedId"
          :options="depositAssets"
          option-label="symbol"
          option-value="id"
          placeholder="Asset"
          class="asset-select"
          :loading="loadingCrypto"
        >
          <template #value="{ value }">
            <CryptoLabel
              v-if="value"
              :symbol="depositAssets.find((c) => c.id === value)?.symbol"
              :icon="depositAssets.find((c) => c.id === value)?.icon"
              size="sm"
            />
            <span v-else class="muted">Asset</span>
          </template>
          <template #option="{ option }">
            <CryptoLabel
              :symbol="option.symbol"
              :icon="option.icon"
              :network="option.network"
              size="sm"
              show-network
            />
          </template>
        </Select>
      </div>

      <div v-if="selected" class="qr-body">
        <div class="qr-frame">
          <img
            v-if="selected.qr"
            :src="selected.qr"
            :alt="`${selected.symbol} deposit QR`"
            class="qr-img"
          />
          <div v-else class="qr-fallback">
            <i class="pi pi-qrcode" />
            <span class="muted">QR unavailable</span>
          </div>
        </div>
        <div class="qr-meta">
          <div class="asset-line">
            <div class="asset-title">
              <CryptoIcon :symbol="selected.symbol" :icon="selected.icon" size="lg" />
              <div>
                <strong>{{ selected.symbol }}</strong>
                <span class="muted">{{ selected.name }} · {{ selected.network }}</span>
              </div>
            </div>
          </div>
          <p class="addr mono">{{ selected.deposit_address }}</p>
          <div class="qr-actions">
            <Button
              :label="copied ? 'Copied' : 'Copy address'"
              :icon="copied ? 'pi pi-check' : 'pi pi-copy'"
              size="small"
              @click="copyAddress"
            />
            <Button
              label="New deposit"
              icon="pi pi-plus"
              size="small"
              outlined
              @click="router.push('/deposits')"
            />
          </div>
          <p class="muted tiny">
            Min deposit {{ selected.min_deposit }} {{ selected.symbol }}. Only send on the
            {{ selected.network }} network.
          </p>
        </div>
      </div>
      <p v-else-if="!loadingCrypto" class="muted">No deposit addresses configured yet.</p>
    </div>

    <div class="glass panel">
      <h3>Summary · {{ currency.code || 'USD' }}</h3>
      <p class="muted small">
        Converted with live rates. Platform ledger is USD-equivalent.
        <span v-if="currency.balances?.available?.usd_equivalent">
          Available ≈ ${{ currency.balances.available.usd_equivalent }} USD
        </span>
      </p>
      <ul>
        <li>
          <span>Active capital</span>
          <strong class="mono">{{ formatDisplay((currency.balances as any)?.active_investments?.capital || currency.balances?.active_capital) }}</strong>
        </li>
        <li>
          <span>Referral earnings</span>
          <strong class="mono success">{{ formatDisplay(currency.balances?.referral) }}</strong>
        </li>
        <li>
          <span>Total deposited (platform)</span>
          <strong class="mono">{{ formatMoney(auth.wallet?.total_deposited ?? 0) }} USD-eq</strong>
        </li>
        <li>
          <span>Total withdrawn (platform)</span>
          <strong class="mono">{{ formatMoney(auth.wallet?.total_withdrawn ?? 0) }} USD-eq</strong>
        </li>
      </ul>
    </div>
  </div>
</template>

<style scoped>
.fx { min-width: 10rem; }
.grid-stats {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 0.75rem;
}
@media (max-width: 900px) { .grid-stats { grid-template-columns: 1fr 1fr; } }
.panel { margin-top: 1rem; padding: 1.15rem; }
h3 { margin-bottom: 0.35rem; font-size: 1rem; }
.small { font-size: 0.85rem; margin-bottom: 0.75rem; }
.tiny { font-size: 0.78rem; margin-top: 0.65rem; }
ul { list-style: none; padding: 0; margin: 0; display: grid; gap: 0.45rem; }
li {
  display: flex;
  justify-content: space-between;
  gap: 0.75rem;
  padding: 0.65rem 0.75rem;
  border-radius: 12px;
  background: rgba(255,255,255,0.03);
  border: 1px solid var(--ci-border);
}
li span { color: var(--ci-muted); }
.success { color: var(--ci-success); }

.qr-panel { margin-top: 1rem; }
.qr-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 1rem;
  flex-wrap: wrap;
  margin-bottom: 1rem;
}
.asset-select { min-width: 10rem; }
.opt-row {
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
}
.tiny-opt { font-size: 0.75rem; margin-left: 0.15rem; }
.qr-body {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 1.25rem;
  align-items: center;
}
@media (max-width: 640px) {
  .qr-body { grid-template-columns: 1fr; justify-items: center; text-align: center; }
  .qr-actions { justify-content: center; }
  .asset-title { justify-content: center; }
}
.qr-frame {
  width: 168px;
  height: 168px;
  border-radius: 16px;
  background: #fff;
  display: grid;
  place-items: center;
  padding: 10px;
  box-shadow: 0 8px 24px rgba(0,0,0,0.2);
}
.qr-img {
  width: 100%;
  height: 100%;
  object-fit: contain;
}
.qr-fallback {
  display: grid;
  place-items: center;
  gap: 0.35rem;
  color: #64748b;
  font-size: 0.8rem;
}
.qr-fallback i { font-size: 2rem; }
.asset-line { margin-bottom: 0.5rem; }
.asset-title {
  display: flex;
  align-items: center;
  gap: 0.65rem;
}
.asset-title > div {
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
}
.addr {
  word-break: break-all;
  font-size: 0.88rem;
  padding: 0.55rem 0.7rem;
  border-radius: 10px;
  background: rgba(255,255,255,0.04);
  border: 1px solid var(--ci-border);
  margin: 0 0 0.75rem;
}
.qr-actions { display: flex; flex-wrap: wrap; gap: 0.45rem; }
</style>
