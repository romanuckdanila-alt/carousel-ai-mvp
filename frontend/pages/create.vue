<script setup lang="ts">
import type { Carousel, CarouselLanguage, CarouselSourceType, GenerationResult } from "~/composables/useApi"
import { mapGenerationStatus, wait } from "~/composables/useApi"

const { api } = useApi()

const method = ref<CarouselSourceType | "links">("text")
const loading = ref(false)
const generationStep = ref<"idle" | "queued" | "running" | "done" | "failed">("idle")
const generationMessage = ref("")
const error = ref("")

const form = reactive({
  title: "",
  slidesCount: 7,
  language: "EN" as CarouselLanguage,
  styleHint: "",
  sourceInput: ""
})

const methodCards = [
  { id: "text", title: "From text", hint: "Paste notes, script or article draft." },
  { id: "video", title: "From video link", hint: "Insert URL and generate summary slides." },
  { id: "links", title: "From links", hint: "Optional mode: multiple URLs in one input." }
] as const

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
    generationMessage.value = mapped === "done"
      ? "Generation completed"
      : mapped === "failed"
        ? "Generation failed"
        : `Generation ${mapped}`

    if (mapped === "done") return
    if (mapped === "failed") throw new Error("Generation failed")
    await wait(1000)
  }

  throw new Error("Generation timeout")
}

const submit = async () => {
  loading.value = true
  error.value = ""
  generationStep.value = "queued"
  generationMessage.value = "Generation queued"

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
    error.value = err?.data?.detail || err?.message || "Failed to create carousel"
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <section class="space-y-6">
    <div class="panel p-6">
      <p class="meta-label">Step 1</p>
      <h1 class="font-display text-3xl md:text-4xl">Create Carousel</h1>
      <p class="mt-2 text-sm text-slate">Select source type and generate a production-ready carousel.</p>

      <div class="mt-6 grid gap-3 md:grid-cols-3">
        <button
          v-for="item in methodCards"
          :key="item.id"
          type="button"
          class="slide-card rounded-[20px] border p-4 text-left transition"
          :class="item.id === method ? 'border-ink bg-ink/5 shadow-[var(--shadow-soft)]' : 'border-slate-200 bg-white hover:border-slate-300'"
          @click="method = item.id"
        >
          <p class="font-display text-xl">{{ item.title }}</p>
          <p class="mt-1 text-sm text-slate">{{ item.hint }}</p>
        </button>
      </div>
    </div>

    <form class="panel space-y-4 p-6" @submit.prevent="submit">
      <div class="grid gap-4 md:grid-cols-2">
        <label class="block">
          <span class="mb-1 block text-sm font-medium">Title</span>
          <input v-model="form.title" class="field" placeholder="AI onboarding playbook" required />
        </label>

        <label class="block">
          <span class="mb-1 block text-sm font-medium">Slides count</span>
          <input v-model.number="form.slidesCount" class="field" type="number" min="6" max="10" />
        </label>
      </div>

      <div class="grid gap-4 md:grid-cols-2">
        <label class="block">
          <span class="mb-1 block text-sm font-medium">Language</span>
          <select v-model="form.language" class="field">
            <option value="RU">RU</option>
            <option value="EN">EN</option>
          </select>
        </label>

        <label class="block">
          <span class="mb-1 block text-sm font-medium">Style hint</span>
          <input v-model="form.styleHint" class="field" placeholder="minimal, educational, with CTA" />
        </label>
      </div>

      <label class="block">
        <span class="mb-1 block text-sm font-medium">
          {{ method === 'video' ? 'Video link' : method === 'links' ? 'Links list' : 'Source text' }}
        </span>
        <textarea
          v-model="form.sourceInput"
          class="field min-h-36"
          :placeholder="method === 'video' ? 'https://youtube.com/...' : method === 'links' ? 'https://site.com/post-1\nhttps://site.com/post-2' : 'Paste your source text'"
          required
        />
      </label>

      <div class="rounded-[16px] border border-slate-200 bg-slate-50/60 p-3">
        <p class="text-xs text-slate">Generation will consume approximately <strong>{{ estimatedTokens }}</strong> tokens.</p>
      </div>

      <div v-if="generationStep !== 'idle'" class="rounded-[16px] border border-slate-200 bg-white p-3">
        <div class="flex items-center gap-2 text-sm font-medium">
          <span v-if="generationStep === 'queued' || generationStep === 'running'" class="loader-dot text-amber-500" />
          <span v-if="generationStep === 'done'" class="h-2 w-2 rounded-full bg-emerald-500" />
          <span v-if="generationStep === 'failed'" class="h-2 w-2 rounded-full bg-rose-500" />
          <span>Generation status: <span class="capitalize">{{ generationStep }}</span></span>
        </div>
        <p class="text-xs text-slate">{{ generationMessage }}</p>
      </div>

      <p v-if="error" class="rounded-xl bg-rose-50 p-3 text-sm text-rose-700">{{ error }}</p>

      <div class="flex flex-wrap items-center gap-3">
        <button class="btn-primary" :disabled="loading">
          <span v-if="loading" class="loader-dot" />
          {{ loading ? 'Generating...' : 'Generate carousel' }}
        </button>
        <NuxtLink to="/" class="btn-secondary">Cancel</NuxtLink>
      </div>
    </form>
  </section>
</template>
