<script setup lang="ts">
import type { Carousel, GenerationResult, Slide } from "~/composables/useApi"
import { mapGenerationStatus, wait } from "~/composables/useApi"

const route = useRoute()
const { api } = useApi()

const carousel = ref<Carousel | null>(null)
const slides = ref<Slide[]>([])
const index = ref(0)
const loading = ref(true)
const regenerating = ref(false)
const error = ref("")
const generationState = ref<"idle" | "queued" | "running" | "done" | "failed">("idle")

const carouselId = computed(() => String(route.params.id))
const currentSlide = computed(() => slides.value[index.value] || null)

const canPrev = computed(() => index.value > 0)
const canNext = computed(() => index.value < slides.value.length - 1)

const load = async () => {
  loading.value = true
  error.value = ""

  try {
    carousel.value = await api<Carousel>(`/carousels/${carouselId.value}`)
    slides.value = await api<Slide[]>(`/carousels/${carouselId.value}/slides`)
    index.value = 0
  } catch (err: any) {
    error.value = err?.data?.detail || err?.message || "Failed to load preview"
  } finally {
    loading.value = false
  }
}

const pollGeneration = async (generationId: string) => {
  for (let i = 0; i < 120; i += 1) {
    const state = await api<GenerationResult>(`/generations/${generationId}`)
    generationState.value = mapGenerationStatus(state.status) as typeof generationState.value
    if (generationState.value === "done") return
    if (generationState.value === "failed") throw new Error("Generation failed")
    await wait(1000)
  }
  throw new Error("Generation timeout")
}

const regenerate = async () => {
  regenerating.value = true
  error.value = ""

  try {
    generationState.value = "queued"
    const generation = await api<GenerationResult>(`/generations`, {
      method: "POST",
      body: { carousel_id: carouselId.value }
    })
    await pollGeneration(generation.id)
    await load()
  } catch (err: any) {
    generationState.value = "failed"
    error.value = err?.data?.detail || err?.message || "Failed to regenerate"
  } finally {
    regenerating.value = false
  }
}

onMounted(load)
</script>

<template>
  <section class="space-y-5">
    <div class="panel p-5">
      <div class="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p class="text-xs uppercase tracking-[0.2em] text-slate">Step 3</p>
          <h1 class="font-display text-3xl">Slides Preview</h1>
          <p class="text-sm text-slate">Review generated slides before opening the full editor.</p>
        </div>

        <div class="flex gap-2">
          <button class="btn-secondary" :disabled="regenerating" @click="regenerate">
            {{ regenerating ? 'Regenerating...' : 'Regenerate' }}
          </button>
          <NuxtLink :to="`/editor/${carouselId}`" class="btn-primary">Open editor</NuxtLink>
        </div>
      </div>

      <div v-if="generationState !== 'idle'" class="mt-4 inline-flex rounded-full bg-slate/10 px-3 py-1 text-xs font-semibold uppercase text-slate">
        Generation {{ generationState }}
      </div>
    </div>

    <p v-if="loading" class="panel p-4 text-sm text-slate">Loading preview...</p>
    <p v-else-if="error" class="rounded-xl bg-rose-50 p-3 text-sm text-rose-700">{{ error }}</p>

    <div v-else class="space-y-4">
      <div class="panel p-4">
        <div class="flex items-center justify-between">
          <button class="btn-secondary" :disabled="!canPrev" @click="index -= 1">←</button>
          <p class="text-xs uppercase tracking-[0.2em] text-slate">Slide {{ index + 1 }} / {{ slides.length }}</p>
          <button class="btn-secondary" :disabled="!canNext" @click="index += 1">→</button>
        </div>

        <div class="mt-4 overflow-x-auto pb-1">
          <div class="flex min-w-max gap-3">
            <button
              v-for="(slide, i) in slides"
              :key="slide.id"
              type="button"
              class="w-72 shrink-0 rounded-xl border p-4 text-left"
              :class="i === index ? 'border-ink bg-white' : 'border-slate/20 bg-slate/5'"
              @click="index = i"
            >
              <p class="text-xs uppercase text-slate">{{ i + 1 }}</p>
              <h3 class="mt-2 font-display text-xl leading-tight">{{ slide.title }}</h3>
              <p class="mt-2 max-h-24 overflow-hidden text-sm text-slate">{{ slide.body }}</p>
            </button>
          </div>
        </div>
      </div>

      <article v-if="currentSlide" class="panel p-6">
        <p class="text-xs uppercase tracking-[0.2em] text-slate">Current slide</p>
        <h2 class="mt-2 font-display text-4xl leading-tight">{{ currentSlide.title }}</h2>
        <p class="mt-3 max-w-2xl text-lg text-slate">{{ currentSlide.body }}</p>
      </article>
    </div>
  </section>
</template>
