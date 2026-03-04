<script setup lang="ts">
import type {
  AssetUploadResult,
  Carousel,
  CarouselDesignSettings,
  CarouselDesignUpdatePayload,
  ExportResult,
  GenerationResult,
  Slide
} from "~/composables/useApi"
import { mapCarouselStatus, mapGenerationStatus, wait } from "~/composables/useApi"

const route = useRoute()
const { api } = useApi()

const carousel = ref<Carousel | null>(null)
const slides = ref<Slide[]>([])
const currentIndex = ref(0)
const loading = ref(true)
const savingSlide = ref(false)
const savingDesign = ref(false)
const exporting = ref(false)
const regenerating = ref(false)
const error = ref("")
const message = ref("")
const generationState = ref<"idle" | "queued" | "running" | "done" | "failed">("idle")

const activeSection = ref<"template" | "background" | "text" | "layout" | "additional" | "export">("template")
const templateModalOpen = ref(false)
const applyToAllSlides = ref(true)

const design = reactive({
  template: "Classic" as "Classic" | "Bold" | "Minimal",
  backgroundColor: "#ffffff",
  backgroundImageUrl: "",
  darkOverlay: false,
  showHeader: true,
  showFooter: true,
  headerText: "",
  footerText: "",
  contentPadding: 52,
  horizontalAlignment: "left" as "left" | "center" | "right",
  verticalAlignment: "top" as "top" | "center" | "bottom",
  showOrderBadge: true,
  roundedPreview: true
})

const templatePresets = [
  {
    id: "Classic" as const,
    title: "Classic",
    hint: "Clean educational style",
    bg: "#ffffff"
  },
  {
    id: "Bold" as const,
    title: "Bold",
    hint: "High-contrast punchy look",
    bg: "#0f172a"
  },
  {
    id: "Minimal" as const,
    title: "Minimal",
    hint: "Soft typography-focused layout",
    bg: "#f6f8fc"
  }
]

const carouselId = computed(() => String(route.params.id))
const currentSlide = computed(() => slides.value[currentIndex.value] || null)
const canPrev = computed(() => currentIndex.value > 0)
const canNext = computed(() => currentIndex.value < slides.value.length - 1)

const verticalJustify = computed(() => {
  if (design.verticalAlignment === "center") return "center"
  if (design.verticalAlignment === "bottom") return "flex-end"
  return "flex-start"
})

const horizontalItems = computed(() => {
  if (design.horizontalAlignment === "center") return "center"
  if (design.horizontalAlignment === "right") return "flex-end"
  return "flex-start"
})

const slideContainerStyle = computed(() => {
  const hasImage = Boolean(design.backgroundImageUrl)
  const overlay = design.darkOverlay ? "linear-gradient(rgba(12, 14, 25, 0.45), rgba(12, 14, 25, 0.45))" : ""
  const bgImage = hasImage
    ? overlay
      ? `${overlay}, url(${design.backgroundImageUrl})`
      : `url(${design.backgroundImageUrl})`
    : "none"

  return {
    padding: `${design.contentPadding}px`,
    backgroundColor: design.backgroundColor,
    backgroundImage: bgImage,
    backgroundSize: "cover",
    backgroundPosition: "center",
    textAlign: design.horizontalAlignment,
    color: design.template === "Bold" ? "#f8fafc" : "#102a43"
  }
})

const statusChipClass = computed(() => {
  const status = mapCarouselStatus(carousel.value?.status || "draft")
  if (status === "ready") return "bg-emerald-100 text-emerald-700"
  if (status === "generating") return "bg-amber-100 text-amber-700"
  if (status === "failed") return "bg-rose-100 text-rose-700"
  return "bg-slate-100 text-slate-700"
})

const hydrateDesign = () => {
  const raw = (carousel.value?.source_payload?.design || {}) as CarouselDesignSettings
  design.template = (raw.template as any) || "Classic"
  design.backgroundColor = raw.background_color || "#ffffff"
  design.backgroundImageUrl = raw.background_image_url || ""
  design.darkOverlay = raw.dark_overlay ?? false
  design.showHeader = raw.show_header ?? true
  design.showFooter = raw.show_footer ?? true
  design.headerText = raw.header_text || (carousel.value?.title || "")
  design.footerText = raw.footer_text || ""
  design.contentPadding = raw.content_padding ?? 52
  design.horizontalAlignment = (raw.horizontal_alignment as any) || "left"
  design.verticalAlignment = (raw.vertical_alignment as any) || "top"

  const additional = raw.additional || {}
  design.showOrderBadge = Boolean(additional.show_order_badge ?? true)
  design.roundedPreview = Boolean(additional.rounded_preview ?? true)
}

const load = async () => {
  loading.value = true
  error.value = ""

  try {
    carousel.value = await api<Carousel>(`/carousels/${carouselId.value}`)
    slides.value = await api<Slide[]>(`/carousels/${carouselId.value}/slides`)
    currentIndex.value = 0
    hydrateDesign()
  } catch (err: any) {
    error.value = err?.data?.detail || err?.message || "Failed to load editor"
  } finally {
    loading.value = false
  }
}

const saveSlide = async () => {
  if (!currentSlide.value) return
  savingSlide.value = true
  error.value = ""

  try {
    const updated = await api<Slide>(`/carousels/${carouselId.value}/slides/${currentSlide.value.id}`, {
      method: "PATCH",
      body: {
        title: currentSlide.value.title,
        body: currentSlide.value.body,
        footer: currentSlide.value.footer
      }
    })

    const idx = slides.value.findIndex((slide) => slide.id === updated.id)
    if (idx !== -1) slides.value[idx] = updated
    message.value = "Slide text saved"
  } catch (err: any) {
    error.value = err?.data?.detail || err?.message || "Failed to save slide"
  } finally {
    savingSlide.value = false
  }
}

const saveDesign = async (patch: CarouselDesignUpdatePayload) => {
  savingDesign.value = true
  error.value = ""

  try {
    const updated = await api<Carousel>(`/carousels/${carouselId.value}/design`, {
      method: "PATCH",
      body: patch
    })

    carousel.value = updated
    message.value = "Design settings saved"
  } catch (err: any) {
    error.value = err?.data?.detail || err?.message || "Failed to save design"
  } finally {
    savingDesign.value = false
  }
}

const applyTemplate = async (preset: typeof templatePresets[number]) => {
  design.template = preset.id
  design.backgroundColor = preset.bg
  design.horizontalAlignment = preset.id === "Bold" ? "center" : "left"

  await saveDesign({
    template: preset.id,
    background_color: preset.bg,
    horizontal_alignment: design.horizontalAlignment,
    apply_to_all_slides: applyToAllSlides.value
  })

  templateModalOpen.value = false
}

const uploadBackground = async (event: Event) => {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return

  const form = new FormData()
  form.append("file", file)

  try {
    savingDesign.value = true
    const uploaded = await api<AssetUploadResult>("/assets/upload", {
      method: "POST",
      body: form as any
    })
    design.backgroundImageUrl = uploaded.url
    await saveDesign({ background_image_url: uploaded.url })
  } catch (err: any) {
    error.value = err?.data?.detail || err?.message || "Failed to upload image"
  } finally {
    savingDesign.value = false
    input.value = ""
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
    const generation = await api<GenerationResult>("/generations", {
      method: "POST",
      body: { carousel_id: carouselId.value }
    })
    await pollGeneration(generation.id)
    await load()
    message.value = "Slides regenerated"
  } catch (err: any) {
    generationState.value = "failed"
    error.value = err?.data?.detail || err?.message || "Failed to regenerate"
  } finally {
    regenerating.value = false
  }
}

const exportZip = async () => {
  exporting.value = true
  error.value = ""

  try {
    const exportTask = await api<ExportResult>("/exports", {
      method: "POST",
      body: { carousel_id: carouselId.value }
    })

    let result = exportTask
    if (result.status !== "completed") {
      for (let i = 0; i < 30; i += 1) {
        await wait(1000)
        result = await api<ExportResult>(`/exports/${result.id}`)
        if (result.status === "completed" || result.status === "failed") break
      }
    }

    if (result.zip_url) {
      window.open(result.zip_url, "_blank")
      message.value = "Export ZIP ready"
    } else {
      throw new Error("Export failed")
    }
  } catch (err: any) {
    error.value = err?.data?.detail || err?.message || "Failed to export"
  } finally {
    exporting.value = false
  }
}

onMounted(load)
</script>

<template>
  <section class="space-y-4">
    <div class="panel p-4">
      <div class="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p class="text-xs uppercase tracking-[0.2em] text-slate">Step 4</p>
          <h1 class="font-display text-2xl md:text-3xl">Carousel Editor</h1>
          <p class="text-sm text-slate">{{ carousel?.title || 'Loading...' }}</p>
        </div>

        <div class="flex items-center gap-2">
          <span class="rounded-full px-2 py-1 text-xs font-semibold uppercase" :class="statusChipClass">
            {{ mapCarouselStatus(carousel?.status || 'draft') }}
          </span>
          <button class="btn-secondary" :disabled="regenerating" @click="regenerate">
            {{ regenerating ? 'Regenerating...' : 'Regenerate' }}
          </button>
        </div>
      </div>

      <div v-if="generationState !== 'idle'" class="mt-3 inline-flex rounded-full bg-slate/10 px-3 py-1 text-xs font-semibold uppercase text-slate">
        Generation {{ generationState }}
      </div>
    </div>

    <p v-if="loading" class="panel p-4 text-sm text-slate">Loading editor...</p>
    <p v-else-if="error" class="rounded-xl bg-rose-50 p-3 text-sm text-rose-700">{{ error }}</p>

    <div v-else class="grid gap-4 xl:grid-cols-[1fr_380px]">
      <div class="panel p-4">
        <div class="flex items-center justify-between gap-2">
          <button class="btn-secondary" :disabled="!canPrev" @click="currentIndex -= 1">← Prev</button>
          <p class="text-xs uppercase tracking-[0.2em] text-slate">Slide {{ currentIndex + 1 }} / {{ slides.length }}</p>
          <button class="btn-secondary" :disabled="!canNext" @click="currentIndex += 1">Next →</button>
        </div>

        <div class="mt-4 flex justify-center">
          <div
            class="relative aspect-[4/5] w-full max-w-[520px] overflow-hidden border border-slate/20"
            :class="design.roundedPreview ? 'rounded-3xl' : 'rounded-lg'"
            :style="slideContainerStyle"
          >
            <div class="flex h-full w-full flex-col" :style="{ justifyContent: verticalJustify, alignItems: horizontalItems }">
              <p
                v-if="design.showHeader"
                class="mb-3 text-xs uppercase tracking-[0.15em]"
                :class="design.template === 'Bold' ? 'text-slate-200' : 'text-slate-500'"
              >
                {{ design.headerText || carousel?.title }}
              </p>

              <div class="max-w-[95%]">
                <div
                  v-if="design.showOrderBadge"
                  class="mb-3 inline-flex rounded-full px-2 py-1 text-xs font-semibold"
                  :class="design.template === 'Bold' ? 'bg-white/20 text-white' : 'bg-slate/10 text-slate-700'"
                >
                  Slide {{ currentIndex + 1 }}
                </div>
                <h2 class="font-display text-[clamp(1.3rem,2.5vw,2.1rem)] leading-tight">{{ currentSlide?.title }}</h2>
                <p class="mt-3 whitespace-pre-wrap text-[clamp(0.95rem,1.8vw,1.1rem)] leading-relaxed opacity-90">{{ currentSlide?.body }}</p>
              </div>

              <p
                v-if="design.showFooter"
                class="mt-4 text-sm"
                :class="design.template === 'Bold' ? 'text-slate-200' : 'text-slate-500'"
              >
                {{ design.footerText || currentSlide?.footer }}
              </p>
            </div>
          </div>
        </div>
      </div>

      <aside class="panel p-4">
        <h2 class="font-display text-xl">Slide Text</h2>

        <div v-if="currentSlide" class="mt-3 space-y-3">
          <label class="block">
            <span class="mb-1 block text-xs uppercase tracking-wide text-slate">Title</span>
            <input v-model="currentSlide.title" class="field" />
          </label>

          <label class="block">
            <span class="mb-1 block text-xs uppercase tracking-wide text-slate">Body</span>
            <textarea v-model="currentSlide.body" class="field min-h-32" />
          </label>

          <label class="block">
            <span class="mb-1 block text-xs uppercase tracking-wide text-slate">Footer</span>
            <input v-model="currentSlide.footer" class="field" />
          </label>

          <button class="btn-primary" :disabled="savingSlide" @click="saveSlide">
            {{ savingSlide ? 'Saving...' : 'Save slide text' }}
          </button>
        </div>
      </aside>
    </div>

    <div class="panel p-3">
      <div class="grid gap-2 sm:grid-cols-3 lg:grid-cols-6">
        <button class="btn-secondary" :class="activeSection === 'template' ? '!bg-ink !text-white' : ''" @click="activeSection = 'template'">Template</button>
        <button class="btn-secondary" :class="activeSection === 'background' ? '!bg-ink !text-white' : ''" @click="activeSection = 'background'">Background</button>
        <button class="btn-secondary" :class="activeSection === 'text' ? '!bg-ink !text-white' : ''" @click="activeSection = 'text'">Text</button>
        <button class="btn-secondary" :class="activeSection === 'layout' ? '!bg-ink !text-white' : ''" @click="activeSection = 'layout'">Layout</button>
        <button class="btn-secondary" :class="activeSection === 'additional' ? '!bg-ink !text-white' : ''" @click="activeSection = 'additional'">Additional</button>
        <button class="btn-secondary" :class="activeSection === 'export' ? '!bg-ink !text-white' : ''" @click="activeSection = 'export'">Export</button>
      </div>

      <div class="mt-3 rounded-xl border border-slate/15 bg-white p-4">
        <div v-if="activeSection === 'template'" class="space-y-3">
          <p class="text-sm text-slate">Choose one of predefined templates.</p>
          <button class="btn-primary" @click="templateModalOpen = true">Open Template Modal</button>
        </div>

        <div v-else-if="activeSection === 'background'" class="space-y-3">
          <label class="block">
            <span class="mb-1 block text-xs uppercase tracking-wide text-slate">Background color</span>
            <input v-model="design.backgroundColor" type="color" class="h-10 w-20 rounded-md border border-slate/20 p-1" />
          </label>

          <label class="inline-flex items-center gap-2 text-sm text-slate">
            <input v-model="design.darkOverlay" type="checkbox" />
            Dark overlay
          </label>

          <label class="block">
            <span class="mb-1 block text-xs uppercase tracking-wide text-slate">Background image</span>
            <input type="file" accept="image/*" class="field" @change="uploadBackground" />
          </label>

          <button
            class="btn-primary"
            :disabled="savingDesign"
            @click="saveDesign({ background_color: design.backgroundColor, dark_overlay: design.darkOverlay })"
          >
            {{ savingDesign ? 'Saving...' : 'Save background settings' }}
          </button>
        </div>

        <div v-else-if="activeSection === 'text'" class="space-y-3">
          <label class="inline-flex items-center gap-2 text-sm text-slate">
            <input v-model="design.showHeader" type="checkbox" />
            Show header
          </label>
          <label class="inline-flex items-center gap-2 text-sm text-slate">
            <input v-model="design.showFooter" type="checkbox" />
            Show footer
          </label>

          <label class="block">
            <span class="mb-1 block text-xs uppercase tracking-wide text-slate">Header text</span>
            <input v-model="design.headerText" class="field" />
          </label>

          <label class="block">
            <span class="mb-1 block text-xs uppercase tracking-wide text-slate">Footer text</span>
            <input v-model="design.footerText" class="field" />
          </label>

          <button
            class="btn-primary"
            :disabled="savingDesign"
            @click="saveDesign({ show_header: design.showHeader, show_footer: design.showFooter, header_text: design.headerText, footer_text: design.footerText })"
          >
            {{ savingDesign ? 'Saving...' : 'Save text settings' }}
          </button>
        </div>

        <div v-else-if="activeSection === 'layout'" class="space-y-3">
          <label class="block">
            <span class="mb-1 block text-xs uppercase tracking-wide text-slate">Content padding: {{ design.contentPadding }}px</span>
            <input v-model.number="design.contentPadding" class="w-full" type="range" min="0" max="180" step="2" />
          </label>

          <label class="block">
            <span class="mb-1 block text-xs uppercase tracking-wide text-slate">Horizontal alignment</span>
            <select v-model="design.horizontalAlignment" class="field">
              <option value="left">Left</option>
              <option value="center">Center</option>
              <option value="right">Right</option>
            </select>
          </label>

          <label class="block">
            <span class="mb-1 block text-xs uppercase tracking-wide text-slate">Vertical alignment</span>
            <select v-model="design.verticalAlignment" class="field">
              <option value="top">Top</option>
              <option value="center">Center</option>
              <option value="bottom">Bottom</option>
            </select>
          </label>

          <button
            class="btn-primary"
            :disabled="savingDesign"
            @click="saveDesign({ content_padding: design.contentPadding, horizontal_alignment: design.horizontalAlignment, vertical_alignment: design.verticalAlignment })"
          >
            {{ savingDesign ? 'Saving...' : 'Save layout settings' }}
          </button>
        </div>

        <div v-else-if="activeSection === 'additional'" class="space-y-3">
          <label class="inline-flex items-center gap-2 text-sm text-slate">
            <input v-model="design.showOrderBadge" type="checkbox" />
            Show slide order badge
          </label>
          <label class="inline-flex items-center gap-2 text-sm text-slate">
            <input v-model="design.roundedPreview" type="checkbox" />
            Rounded preview card
          </label>

          <button
            class="btn-primary"
            :disabled="savingDesign"
            @click="saveDesign({ additional: { show_order_badge: design.showOrderBadge, rounded_preview: design.roundedPreview } })"
          >
            {{ savingDesign ? 'Saving...' : 'Save additional settings' }}
          </button>
        </div>

        <div v-else class="space-y-3">
          <p class="text-sm text-slate">Export carousel into 1080x1350 PNG ZIP package.</p>
          <button class="btn-primary" :disabled="exporting" @click="exportZip">
            {{ exporting ? 'Exporting...' : 'Export ZIP' }}
          </button>
        </div>
      </div>
    </div>

    <p v-if="message" class="rounded-xl bg-emerald-50 p-3 text-sm text-emerald-700">{{ message }}</p>

    <div v-if="templateModalOpen" class="fixed inset-0 z-50 flex items-center justify-center bg-black/35 p-4">
      <div class="w-full max-w-xl rounded-2xl bg-white p-5 shadow-2xl">
        <div class="flex items-center justify-between gap-3">
          <h3 class="font-display text-2xl">Template Presets</h3>
          <button class="btn-secondary" @click="templateModalOpen = false">Close</button>
        </div>

        <label class="mt-3 inline-flex items-center gap-2 text-sm text-slate">
          <input v-model="applyToAllSlides" type="checkbox" />
          Apply to all slides
        </label>

        <div class="mt-4 grid gap-3 md:grid-cols-3">
          <button
            v-for="preset in templatePresets"
            :key="preset.id"
            class="rounded-xl border border-slate/20 p-4 text-left transition hover:border-ink"
            @click="applyTemplate(preset)"
          >
            <div class="mb-2 h-16 rounded-lg border border-slate/15" :style="{ backgroundColor: preset.bg }" />
            <p class="font-display text-xl">{{ preset.title }}</p>
            <p class="text-xs text-slate">{{ preset.hint }}</p>
          </button>
        </div>
      </div>
    </div>
  </section>
</template>
