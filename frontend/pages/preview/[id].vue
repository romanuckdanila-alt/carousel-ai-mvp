<script setup lang="ts">
import type { Carousel, GenerationResult, Slide } from "~/composables/useApi"
import { mapGenerationStatus, wait } from "~/composables/useApi"

const route = useRoute()
const { api } = useApi()

const carousel = ref<Carousel | null>(null)
const slides = ref<Slide[]>([])
const index = ref(0)
const thumbRefs = ref<(HTMLElement | null)[]>([])
const loading = ref(true)
const regenerating = ref(false)
const error = ref("")
const generationState = ref<"idle" | "queued" | "running" | "done" | "failed">("idle")

const carouselId = computed(() => String(route.params.id))
const currentSlide = computed(() => slides.value[index.value] || null)
const canPrev = computed(() => index.value > 0)
const canNext = computed(() => index.value < slides.value.length - 1)
const slideBadge = (slideIndex: number) => String(slideIndex + 1).padStart(2, "0")
const setThumbRef = (el: Element | null, i: number) => {
  thumbRefs.value[i] = el as HTMLElement | null
}

const goPrev = () => {
  if (canPrev.value) index.value -= 1
}

const goNext = () => {
  if (canNext.value) index.value += 1
}

watch(index, async (nextIndex) => {
  await nextTick()
  thumbRefs.value[nextIndex]?.scrollIntoView({
    behavior: "smooth",
    block: "nearest",
    inline: "center"
  })
})

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
  <section class="space-y-6">
    <div class="panel p-6">
      <div class="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p class="meta-label">Step 3</p>
          <h1 class="font-display text-3xl md:text-4xl">Preview</h1>
          <p class="mt-1 text-sm text-slate">{{ carousel?.title || 'Generated carousel preview' }}</p>
        </div>

        <div class="flex flex-wrap gap-2">
          <button class="btn-secondary" :disabled="regenerating" @click="regenerate">
            <span v-if="regenerating" class="loader-dot" />
            {{ regenerating ? 'Regenerating...' : 'Regenerate' }}
          </button>
          <NuxtLink :to="`/editor/${carouselId}`" class="btn-primary">Open in Editor</NuxtLink>
        </div>
      </div>

      <div v-if="generationState !== 'idle'" class="mt-4 inline-flex items-center gap-2 rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold uppercase text-slate-700">
        <span v-if="generationState === 'queued' || generationState === 'running'" class="loader-dot text-amber-500" />
        <span v-else-if="generationState === 'done'" class="h-2 w-2 rounded-full bg-emerald-500" />
        <span v-else class="h-2 w-2 rounded-full bg-rose-500" />
        {{ generationState }}
      </div>
    </div>

    <div v-if="loading" class="panel space-y-4 p-4 md:p-6">
      <div class="skeleton h-4 w-32" />
      <div class="preview-wrapper">
        <div class="preview-scale">
          <div class="skeleton w-full rounded-[24px]" style="aspect-ratio: 4 / 5;" />
        </div>
      </div>
      <div class="thumb-strip">
        <div v-for="i in 5" :key="`preview-skeleton-${i}`" class="skeleton h-48 w-40 shrink-0 rounded-[18px]" />
      </div>
    </div>
    <p v-else-if="error" class="rounded-xl bg-rose-50 p-3 text-sm text-rose-700">{{ error }}</p>

    <div v-else class="space-y-4">
      <div class="panel overflow-visible p-4 md:p-6">
        <div class="flex items-center justify-between">
          <button class="btn-secondary nav-arrow" :disabled="!canPrev" @click="goPrev">←</button>
          <p class="meta-label">Slide {{ index + 1 }} / {{ slides.length }}</p>
          <button class="btn-secondary nav-arrow" :disabled="!canNext" @click="goNext">→</button>
        </div>

        <div class="preview-wrapper mt-5">
          <div class="preview-scale">
            <transition name="fade" mode="out-in">
              <article v-if="currentSlide" :key="currentSlide.id" class="slide-canvas slide-card">
                <header class="slide-section slide-header">
                  <p class="meta-label">Slide {{ index + 1 }}</p>
                  <h2 class="slide-title">{{ currentSlide.title }}</h2>
                </header>

                <div class="slide-section slide-body-wrap">
                  <p class="slide-body">{{ currentSlide.body }}</p>
                </div>

                <footer class="slide-section slide-footer">
                  {{ currentSlide.footer || carousel?.title || 'Carousel preview' }}
                </footer>
              </article>
            </transition>
          </div>
        </div>
      </div>

      <div class="panel overflow-visible p-4">
        <p class="meta-label">Slides</p>
        <div class="thumb-strip mt-3">
          <button
            v-for="(slide, i) in slides"
            :key="slide.id"
            type="button"
            class="thumb-item slide-card"
            :class="{ 'thumb-item--active': i === index }"
            @click="index = i"
            :ref="(el) => setThumbRef(el, i)"
          >
            <article class="thumb-canvas">
              <p class="meta-label">{{ slideBadge(i) }}</p>
              <h3 class="thumb-title">{{ slide.title }}</h3>
              <p class="thumb-body">{{ slide.body }}</p>
            </article>
          </button>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.25s ease, transform 0.25s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
  transform: translateY(4px);
}

.preview-wrapper {
  overflow: visible;
  display: flex;
  justify-content: center;
}

.preview-scale {
  --preview-scale: 0.95;
  width: min(100%, 560px, calc((100vh - 320px) * 4 / 5));
  transform: scale(var(--preview-scale));
  transform-origin: top center;
  overflow: visible;
}

.slide-canvas {
  aspect-ratio: 4 / 5;
  width: 100%;
  border-radius: 20px;
  border: 1px solid rgba(148, 163, 184, 0.35);
  background:
    radial-gradient(420px 240px at 90% 0%, rgba(132, 220, 198, 0.18), transparent 60%),
    radial-gradient(360px 220px at 0% 100%, rgba(246, 189, 96, 0.16), transparent 65%),
    #ffffff;
  box-shadow: var(--shadow-card);
  padding: clamp(20px, 3.8vw, 36px);
  display: flex;
  flex-direction: column;
  gap: clamp(14px, 2vw, 20px);
}

.slide-section {
  min-width: 0;
}

.slide-header {
  border-bottom: 1px solid rgba(148, 163, 184, 0.35);
  padding-bottom: 14px;
}

.slide-title {
  margin-top: 10px;
  font-family: "Space Grotesk", "Avenir Next", sans-serif;
  font-size: clamp(1.8rem, 3.3vw, 2.4rem);
  line-height: 1.1;
  color: #102a43;
}

.slide-body-wrap {
  flex: 1;
  display: flex;
  align-items: center;
}

.slide-body {
  margin: 0;
  font-size: clamp(1.04rem, 1.9vw, 1.25rem);
  line-height: 1.6;
  color: #334e68;
  white-space: pre-wrap;
}

.slide-footer {
  border-top: 1px solid rgba(148, 163, 184, 0.35);
  padding-top: 14px;
  font-size: clamp(0.82rem, 1.35vw, 0.92rem);
  font-weight: 600;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  color: #627d98;
}

.thumb-strip {
  overflow-x: auto;
  overflow-y: visible;
  padding-bottom: 8px;
  display: flex;
  gap: 12px;
}

.thumb-item {
  width: 180px;
  flex-shrink: 0;
  border-radius: 20px;
  padding: 0;
  border: 1px solid rgba(148, 163, 184, 0.35);
  background: #ffffff;
  transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
}

.thumb-item:hover {
  transform: translateY(-1px);
  border-color: rgba(16, 42, 67, 0.35);
}

.thumb-item--active {
  border-color: rgba(16, 42, 67, 0.65);
  box-shadow: var(--shadow-soft);
}

.thumb-canvas {
  aspect-ratio: 4 / 5;
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  text-align: left;
}

.thumb-title {
  margin: 0;
  font-family: "Space Grotesk", "Avenir Next", sans-serif;
  font-size: 1rem;
  line-height: 1.2;
  color: #102a43;
  overflow: hidden;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
}

.thumb-body {
  margin: 0;
  font-size: 0.82rem;
  line-height: 1.4;
  color: #627d98;
  overflow: hidden;
  display: -webkit-box;
  -webkit-line-clamp: 5;
  -webkit-box-orient: vertical;
}

@media (max-width: 1120px) {
  .preview-scale {
    --preview-scale: 0.9;
  }
}

@media (max-width: 820px) {
  .preview-scale {
    --preview-scale: 0.85;
  }
}

@media (max-width: 560px) {
  .preview-scale {
    --preview-scale: 0.8;
    width: min(100%, 460px, calc((100vh - 300px) * 4 / 5));
  }

  .thumb-item {
    width: 148px;
  }
}
</style>
