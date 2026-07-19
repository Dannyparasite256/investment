<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import Accordion from 'primevue/accordion'
import AccordionPanel from 'primevue/accordionpanel'
import AccordionHeader from 'primevue/accordionheader'
import AccordionContent from 'primevue/accordioncontent'
import PageHeader from '@/components/ui/PageHeader.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import { api } from '@/services/api'
import type { FAQItem } from '@/types/api'

const items = ref<FAQItem[]>([])
const loading = ref(true)

const grouped = computed(() => {
  const map = new Map<string, FAQItem[]>()
  for (const f of items.value) {
    const cat = f.category || 'General'
    if (!map.has(cat)) map.set(cat, [])
    map.get(cat)!.push(f)
  }
  return [...map.entries()]
})

onMounted(async () => {
  try {
    const { data } = await api.faq()
    items.value = Array.isArray(data) ? data : []
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div>
    <PageHeader title="FAQ" subtitle="Answers to common questions" />
    <EmptyState v-if="!loading && !items.length" title="No FAQs yet" text="Check back soon or open a support ticket." />
    <div v-for="[cat, list] in grouped" :key="cat" class="block">
      <h3 class="cat">{{ cat }}</h3>
      <div class="glass card">
        <Accordion>
          <AccordionPanel v-for="f in list" :key="f.id" :value="f.id">
            <AccordionHeader>{{ f.question }}</AccordionHeader>
            <AccordionContent>
              <div class="answer">{{ f.answer }}</div>
            </AccordionContent>
          </AccordionPanel>
        </Accordion>
      </div>
    </div>
  </div>
</template>

<style scoped>
.block { margin-bottom: 1.25rem; }
.cat { margin-bottom: 0.5rem; font-size: 0.95rem; color: var(--ci-muted); text-transform: uppercase; letter-spacing: 0.06em; }
.card { padding: 0.35rem 0.5rem; }
.answer { white-space: pre-wrap; color: var(--ci-muted); line-height: 1.55; }
</style>
