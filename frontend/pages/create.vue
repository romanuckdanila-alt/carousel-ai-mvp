<script setup lang="ts">
import type { Carousel, CarouselLanguage, CarouselSourceType, GenerationResult } from "~/composables/useApi"
import { mapGenerationStatus, wait } from "~/composables/useApi"

const { api } = useApi()
const { t } = useLanguage()

const method = ref<CarouselSourceType | "links">("text")
const loading = ref(false)
const generationStep = ref<"idle" | "queued" | "running" | "done" | "failed">("idle")
const error = ref("")

const form = reactive({
  title: "",
  slidesCount: 7,
  language: "EN" as CarouselLanguage,
  styleHint: "",
  sourceInput: ""
})

const methodCards = computed(() => [
  { id: "text", title: t("methodFromText"), hint: t("methodFromTextHint") },
  { id: "video", title: t("methodFromVideo"), hint: t("methodFromVideoHint") },
  { id: "links", title: t("methodFromLinks"), hint: t("methodFromLinksHint") }
])

const generationStepLabel = computed(() => {
  if (generationStep.value === "queued") return t("statusQueued")
  if (generationStep.value === "running") return t("statusRunning")
  if (generationStep.value === "done") return t("statusDone")
  if (generationStep.value === "failed") return t("statusFailed")
  return t("statusDraft")
})

const generationMessage = computed(() => {
  if (generationStep.value === "queued") return t("generationQueued")
  if (generationStep.value === "running") return t("generationRunning")
  if (generationStep.value === "done") return t("generationCompleted")
  if (generationStep.value === "failed") return t("generationFailed")
  return ""
})

const estimatedTokens = computed(() => {
  const sourceWeight = Math.ceil(Math.min(form.sourceInput.length, 2400) / 4)
  return form.slidesCount * 220 + sourceWeight + 180
})

const buildPayload = () => {
  if (method.value === "video") {
    return { source_type: "video", source_payload: { video_url: form.sourceInput } }
  }

  if (method.value === "links") {
    const links = form.sourceInput.split(/\n|,|\s+/).map((part) => part.trim()).filter(Boolean)
    return { source_type: "text", source_payload: { links, text: links.join("\n") } }
  }

  return { source_type: "text", source_payload: { text: form.sourceInput } }
}

const waitForGeneration = async (generationId: string) => {
  for (let attempt = 0; attempt < 120; attempt += 1) {
    const state = await api<GenerationResult>(`/generations/${generationId}`)
    const mapped = mapGenerationStatus(state.status)
    generationStep.value = mapped as typeof generationStep.value

    if (mapped === "done") return
    if (mapped === "failed") throw new Error(t("generationFailed"))
    await wait(1000)
  }

  throw new Error(t("generationTimeout"))
}

const submit = async () => {
  loading.value = true
  error.value = ""
  generationStep.value = "queued"

  try {
    const source = buildPayload()

    const carousel = await api<Carousel>("/carousels", {
      method: "POST",
      body: {
        title: form.title,
        source_type: source.source_type,
        source_payload: source.source_payload,
        slides_count: form.slidesCount,
        language: form.language,
        style_hint: form.styleHint || null
      }
    })

    const generation = await api<GenerationResult>("/generations", {
      method: "POST",
      body: { carousel_id: carousel.id }
    })

    await waitForGeneration(generation.id)
    await navigateTo(`/preview/${carousel.id}`)
  } catch (err: any) {
    generationStep.value = "failed"
    error.value = err?.data?.detail || err?.message || t("failedToCreateCarousel")
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <section class="space-y-8">
    <div class="panel p-6">
      <p class="meta-label">{{ t("step1") }}</p>
      <h1 class="page-title font-display">{{ t("createCarousel") }}</h1>
      <p class="body-copy mt-2 max-w-[65ch]">{{ t("createCarouselDescription") }}</p>

      <div class="mt-6 grid gap-3 md:grid-cols-3">
        <button
          v-for="item in methodCards"
          :key="item.id"
          type="button"
          class="slide-card rounded-[20px] border p-4 text-left transition"
          :class="item.id === method ? 'border-ink bg-ink/5 shadow-[var(--shadow-soft)]' : 'border-slate-200 bg-white hover:border-slate-300'"
          @click="method = item.id"
        >
          <p class="section-title font-display">{{ item.title }}</p>
          <p class="meta-copy mt-1 max-w-prose">{{ item.hint }}</p>
        </button>
      </div>
    </div>

    <form class="panel space-y-4 p-6" @submit.prevent="submit">
      <div class="grid gap-4 md:grid-cols-2">
        <label class="block">
          <span class="form-label">{{ t("titleLabel") }}</span>
          <input v-model="form.title" class="field" :placeholder="t('titlePlaceholder')" required />
        </label>

        <label class="block">
          <span class="form-label">{{ t("slidesCountLabel") }}</span>
          <input v-model.number="form.slidesCount" class="field" type="number" min="6" max="10" />
        </label>
      </div>

      <div class="grid gap-4 md:grid-cols-2">
        <label class="block">
          <span class="form-label">{{ t("languageLabel") }}</span>
          <select v-model="form.language" class="field">
            <option value="RU">RU</option>
            <option value="EN">EN</option>
          </select>
        </label>

        <label class="block">
          <span class="form-label">{{ t("styleHintLabel") }}</span>
          <input v-model="form.styleHint" class="field" :placeholder="t('styleHintPlaceholder')" />
        </label>
      </div>

      <label class="block">
        <span class="form-label">
          {{ method === 'video' ? t('sourceVideoLabel') : method === 'links' ? t('sourceLinksLabel') : t('sourceTextLabel') }}
        </span>
        <textarea
          v-model="form.sourceInput"
          class="field min-h-36"
          :placeholder="method === 'video' ? t('sourceVideoPlaceholder') : method === 'links' ? t('sourceLinksPlaceholder') : t('sourceTextPlaceholder')"
          required
        />
      </label>

      <div class="rounded-[16px] border border-slate-200 bg-slate-50/60 p-3">
        <p class="meta-copy">{{ t("tokenEstimatePrefix") }} <strong class="text-slate-700">{{ estimatedTokens }}</strong> {{ t("tokenEstimateSuffix") }}</p>
      </div>

      <div v-if="generationStep !== 'idle'" class="rounded-[16px] border border-slate-200 bg-white p-3">
        <div class="flex items-center gap-2 text-sm font-medium">
          <span v-if="generationStep === 'queued' || generationStep === 'running'" class="loader-dot text-amber-500" />
          <span v-if="generationStep === 'done'" class="h-2 w-2 rounded-full bg-emerald-500" />
          <span v-if="generationStep === 'failed'" class="h-2 w-2 rounded-full bg-rose-500" />
          <span>{{ t("generationStatus") }} <span class="capitalize">{{ generationStepLabel }}</span></span>
        </div>
        <p class="meta-copy">{{ generationMessage }}</p>
      </div>

      <p v-if="error" class="rounded-xl bg-rose-50 p-3 text-sm text-rose-700">{{ error }}</p>

      <div class="stable-actions-row">
        <button class="btn-primary min-w-[140px] justify-center" :disabled="loading">
          <span v-if="loading" class="loader-dot" />
          {{ loading ? t("generating") : t("generate") }}
        </button>
        <NuxtLink to="/" class="btn-secondary min-w-[110px] justify-center">{{ t("cancel") }}</NuxtLink>
      </div>
    </form>
  </section>
</template>
