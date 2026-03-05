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
const exportState = ref<"idle" | "exporting" | "preparing" | "ready" | "failed">("idle")

const activeSection = ref<"template" | "background" | "text" | "layout" | "additional" | "export">("template")
const templateModalOpen = ref(false)
const applyToAllSlides = ref(true)

const design = reactive({
  template: "Classic" as "Classic" | "Bold" | "Minimal",
  backgroundColor: "#ffffff",
  backgroundImageUrl: "",
  darkOverlayOpacity: 0,
  showHeader: true,
  showFooter: true,
  headerText: "",
  footerText: "",
  contentPadding: 48,
  horizontalAlignment: "left" as "left" | "center" | "right",
  verticalAlignment: "center" as "top" | "center" | "bottom",
  showOrderBadge: true,
  roundedPreview: true
})

const templatePresets = [
  {
    id: "Classic" as const,
    title: "Classic",
    hint: "Balanced content and calm colors",
    bg: "#ffffff",
    text: "#102a43"
  },
  {
    id: "Bold" as const,
    title: "Bold",
    hint: "High contrast with centered hierarchy",
    bg: "#0f172a",
    text: "#f8fafc"
  },
  {
    id: "Minimal" as const,
    title: "Minimal",
    hint: "Light and typography focused",
    bg: "#f3f6fb",
    text: "#102a43"
  }
]

const carouselId = computed(() => String(route.params.id))
const currentSlide = computed(() => slides.value[currentIndex.value] || null)
const canPrev = computed(() => currentIndex.value > 0)
const canNext = computed(() => currentIndex.value < slides.value.length - 1)
const clampedPadding = computed(() => Math.max(16, Math.min(design.contentPadding, 72)))

const justifyMap = computed(() => {
  if (design.verticalAlignment === "top") return "flex-start"
  if (design.verticalAlignment === "bottom") return "flex-end"
  return "center"
})

const alignSelfMap = computed(() => {
  if (design.horizontalAlignment === "left") return "flex-start"
  if (design.horizontalAlignment === "right") return "flex-end"
  return "stretch"
})

const articleStyle = computed(() => ({
  alignSelf: alignSelfMap.value,
  width: design.horizontalAlignment === "center" ? "100%" : "100%",
}))

const slideContainerStyle = computed(() => {
  const textColor = design.template === "Bold" ? "#f8fafc" : "#102a43"
  const overlayOpacity = Math.max(0, Math.min(90, design.darkOverlayOpacity)) / 100
  const overlay = overlayOpacity > 0
    ? `linear-gradient(rgba(8, 12, 24, ${overlayOpacity}), rgba(8, 12, 24, ${overlayOpacity}))`
    : ""
  const hasImage = Boolean(design.backgroundImageUrl)

  const backgroundImage = hasImage
    ? overlay
      ? `${overlay}, url(${design.backgroundImageUrl})`
      : `url(${design.backgroundImageUrl})`
    : "none"

  return {
    backgroundColor: design.backgroundColor,
    backgroundImage,
    backgroundSize: "cover",
    backgroundPosition: "center",
    color: textColor,
    padding: `${clampedPadding.value}px`,
    textAlign: design.horizontalAlignment
  }
})

const statusChipClass = computed(() => {
  const status = mapCarouselStatus(carousel.value?.status || "draft")
  if (status === "ready") return "bg-emerald-100 text-emerald-700"
  if (status === "generating") return "bg-amber-100 text-amber-800"
  if (status === "failed") return "bg-rose-100 text-rose-700"
  return "bg-slate-100 text-slate-700"
})

const exportStatusText = computed(() => {
  if (exportState.value === "exporting") return "Exporting..."
  if (exportState.value === "preparing") return "Preparing images..."
  if (exportState.value === "ready") return "Download ready"
  if (exportState.value === "failed") return "Export failed"
  return ""
})

const hydrateDesign = () => {
  const raw = (carousel.value?.source_payload?.design || {}) as CarouselDesignSettings
  design.template = (raw.template as any) || "Classic"
  design.backgroundColor = raw.background_color || "#ffffff"
  design.backgroundImageUrl = raw.background_image_url || ""
  design.darkOverlayOpacity = Math.round((raw.dark_overlay_opacity ?? (raw.dark_overlay ? 0.45 : 0)) * 100)
  design.showHeader = raw.show_header ?? true
  design.showFooter = raw.show_footer ?? true
  design.headerText = raw.header_text || (carousel.value?.title || "")
  design.footerText = raw.footer_text || ""
  design.contentPadding = Math.max(16, Math.min(raw.content_padding ?? 48, 72))
  design.horizontalAlignment = (raw.horizontal_alignment as any) || "left"
  design.verticalAlignment = (raw.vertical_alignment as any) || "center"

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
    const uploaded = await api<AssetUploadResult>("/assets/upload", {
      method: "POST",
      body: form as any
    })
    design.backgroundImageUrl = uploaded.url
    await saveDesign({ background_image_url: uploaded.url })
  } catch (err: any) {
    error.value = err?.data?.detail || err?.message || "Failed to upload image"
  } finally {
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
  exportState.value = "exporting"
  error.value = ""

  try {
    const exportTask = await api<ExportResult>("/exports", {
      method: "POST",
      body: { carousel_id: carouselId.value }
    })

    exportState.value = "preparing"
    let result = exportTask

    if (result.status !== "completed") {
      for (let i = 0; i < 45; i += 1) {
        await wait(1000)
        result = await api<ExportResult>(`/exports/${result.id}`)
        if (result.status === "completed" || result.status === "failed") break
      }
    }

    if (result.zip_url) {
      exportState.value = "ready"
      message.value = "Download ready"
      window.open(result.zip_url, "_blank")
    } else {
      throw new Error("Export failed")
    }
  } catch (err: any) {
    exportState.value = "failed"
    error.value = err?.data?.detail || err?.message || "Failed to export"
  } finally {
    exporting.value = false
  }
}

onMounted(load)
</script>

<template>
  <section class="space-y-6">
    <div class="panel p-5">
      <div class="flex flex-wrap items-center justify-between gap-3">
        <div class="space-y-1">
          <p class="meta-label">Step 4</p>
          <h1 class="page-title font-display">Carousel Editor</h1>
          <p class="body-copy max-w-[65ch]">{{ carousel?.title || 'Loading...' }}</p>
        </div>

        <div class="flex items-center gap-2">
          <span class="rounded-full px-3 py-1 text-xs font-semibold uppercase" :class="statusChipClass">
            {{ mapCarouselStatus(carousel?.status || 'draft') }}
          </span>
          <button class="btn-secondary" :disabled="regenerating" @click="regenerate">
            <span v-if="regenerating" class="loader-dot" />
            {{ regenerating ? 'Regenerating...' : 'Regenerate' }}
          </button>
        </div>
      </div>

      <div v-if="generationState !== 'idle'" class="mt-3 inline-flex items-center gap-2 rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold uppercase text-slate-700">
        <span v-if="generationState === 'queued' || generationState === 'running'" class="loader-dot text-amber-500" />
        <span v-else-if="generationState === 'done'" class="h-2 w-2 rounded-full bg-emerald-500" />
        <span v-else class="h-2 w-2 rounded-full bg-rose-500" />
        {{ generationState }}
      </div>
    </div>

    <p v-if="loading" class="panel p-4 text-sm text-slate">Loading editor...</p>
    <p v-else-if="error" class="rounded-[16px] bg-rose-50 p-3 text-sm text-rose-700">{{ error }}</p>

    <div v-else class="grid gap-4 xl:grid-cols-[1fr_390px]">
      <div class="panel p-4">
        <div class="flex items-center justify-between gap-2">
          <button class="btn-secondary nav-arrow" :disabled="!canPrev" @click="currentIndex -= 1">← Prev</button>
          <p class="meta-label">Slide {{ currentIndex + 1 }} / {{ slides.length }}</p>
          <button class="btn-secondary nav-arrow" :disabled="!canNext" @click="currentIndex += 1">Next →</button>
        </div>

        <div class="editor-preview-wrapper mt-4">
          <div class="editor-preview-scale">
          <div
            class="editor-preview-canvas slide-card relative aspect-[4/5] w-full border border-slate-200/70"
            :class="design.roundedPreview ? 'rounded-[20px]' : 'rounded-[12px]'"
            :style="slideContainerStyle"
          >
            <div class="editor-content flex h-full flex-col rounded-[inherit] bg-white/0">
              <header
                class="border-b pb-3"
                :class="design.template === 'Bold' ? 'border-white/20 text-slate-100' : 'border-slate-300/70 text-slate-600'"
                v-show="design.showHeader"
              >
                <p class="meta-label !text-current">{{ design.headerText || carousel?.title }}</p>
              </header>

              <main class="flex min-h-0 flex-1 flex-col" :style="{ justifyContent: justifyMap }">
                <article class="w-full max-w-[96%] py-4" :style="articleStyle">
                  <div
                    v-if="design.showOrderBadge"
                    class="mb-3 inline-flex rounded-full px-2.5 py-1 text-xs font-semibold"
                    :class="design.template === 'Bold' ? 'bg-white/20 text-white' : 'bg-slate-200/70 text-slate-700'"
                  >
                    Slide {{ currentIndex + 1 }}
                  </div>
                  <h2 class="editor-title font-display text-[clamp(1.65rem,2.8vw,2.3rem)] leading-[1.08]">{{ currentSlide?.title }}</h2>
                  <p class="editor-body mt-4 whitespace-pre-wrap text-[clamp(1rem,1.8vw,1.15rem)] leading-[1.65]">{{ currentSlide?.body }}</p>
                </article>
              </main>

              <footer
                class="border-t pt-3"
                :class="design.template === 'Bold' ? 'border-white/20 text-slate-100' : 'border-slate-300/70 text-slate-600'"
                v-show="design.showFooter"
              >
                <p class="text-sm">{{ design.footerText || currentSlide?.footer }}</p>
              </footer>
            </div>
          </div>
          </div>
        </div>
      </div>

      <aside class="panel p-4">
        <h2 class="section-title font-display">Slide Text</h2>

        <div v-if="currentSlide" class="mt-4 space-y-4">
          <label class="block">
            <span class="form-label">Title</span>
            <input v-model="currentSlide.title" class="field" />
          </label>

          <label class="block">
            <span class="form-label">Body</span>
            <textarea v-model="currentSlide.body" class="field min-h-32" />
          </label>

          <label class="block">
            <span class="form-label">Footer</span>
            <input v-model="currentSlide.footer" class="field" />
          </label>

          <button class="btn-primary" :disabled="savingSlide" @click="saveSlide">
            <span v-if="savingSlide" class="loader-dot" />
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

      <div class="mt-4 rounded-[16px] border border-slate-200/70 bg-white p-4">
        <div v-if="activeSection === 'template'" class="space-y-3">
          <p class="meta-copy max-w-prose">Select a visual template preset.</p>
          <div class="grid gap-3 md:grid-cols-3">
            <button
              v-for="preset in templatePresets"
              :key="preset.id"
              type="button"
              class="rounded-[16px] border p-3 text-left transition"
              :class="design.template === preset.id ? 'border-ink bg-ink/5' : 'border-slate-200 hover:border-slate-300'"
              @click="applyTemplate(preset)"
            >
              <div class="h-16 rounded-[12px] border border-slate-200/60 p-2" :style="{ backgroundColor: preset.bg, color: preset.text }">
                <p class="text-[11px] uppercase tracking-wide opacity-70">Header</p>
                <p class="font-display text-sm">Title</p>
              </div>
              <p class="mt-2 font-display text-xl">{{ preset.title }}</p>
              <p class="meta-copy">{{ preset.hint }}</p>
            </button>
          </div>
          <button class="btn-secondary" @click="templateModalOpen = true">Open template modal</button>
        </div>

        <div v-else-if="activeSection === 'background'" class="space-y-4">
          <div class="grid gap-4 md:grid-cols-2">
            <label class="block">
              <span class="form-label">Background color</span>
              <input v-model="design.backgroundColor" type="color" class="mt-1 h-10 w-20 rounded-[12px] border border-slate-200 p-1" />
            </label>

            <label class="block">
              <span class="form-label">Overlay intensity: {{ design.darkOverlayOpacity }}%</span>
              <input v-model.number="design.darkOverlayOpacity" type="range" class="mt-2 w-full" min="0" max="90" step="5" />
            </label>
          </div>

          <label class="block">
            <span class="form-label">Background image</span>
            <input type="file" accept="image/*" class="field mt-1" @change="uploadBackground" />
          </label>

          <button
            class="btn-primary"
            :disabled="savingDesign"
            @click="saveDesign({ background_color: design.backgroundColor, dark_overlay: design.darkOverlayOpacity > 0, dark_overlay_opacity: design.darkOverlayOpacity / 100 })"
          >
            <span v-if="savingDesign" class="loader-dot" />
            {{ savingDesign ? 'Saving...' : 'Save background settings' }}
          </button>
        </div>

        <div v-else-if="activeSection === 'text'" class="space-y-3">
          <label class="inline-flex items-center gap-2 text-sm text-slate-700">
            <input v-model="design.showHeader" type="checkbox" />
            Show header
          </label>
          <label class="inline-flex items-center gap-2 text-sm text-slate-700">
            <input v-model="design.showFooter" type="checkbox" />
            Show footer
          </label>

          <label class="block">
            <span class="form-label">Header text</span>
            <input v-model="design.headerText" class="field mt-1" />
          </label>

          <label class="block">
            <span class="form-label">Footer text</span>
            <input v-model="design.footerText" class="field mt-1" />
          </label>

          <button
            class="btn-primary"
            :disabled="savingDesign"
            @click="saveDesign({ show_header: design.showHeader, show_footer: design.showFooter, header_text: design.headerText, footer_text: design.footerText })"
          >
            <span v-if="savingDesign" class="loader-dot" />
            {{ savingDesign ? 'Saving...' : 'Save text settings' }}
          </button>
        </div>

        <div v-else-if="activeSection === 'layout'" class="space-y-3">
          <label class="block">
            <span class="form-label">Content padding: {{ clampedPadding }}px</span>
            <input v-model.number="design.contentPadding" class="mt-2 w-full" type="range" min="16" max="72" step="2" />
          </label>

          <label class="block">
            <span class="form-label">Horizontal alignment</span>
            <select v-model="design.horizontalAlignment" class="field mt-1">
              <option value="left">Left</option>
              <option value="center">Center</option>
              <option value="right">Right</option>
            </select>
          </label>

          <label class="block">
            <span class="form-label">Vertical alignment</span>
            <select v-model="design.verticalAlignment" class="field mt-1">
              <option value="top">Top</option>
              <option value="center">Center</option>
              <option value="bottom">Bottom</option>
            </select>
          </label>

          <button
            class="btn-primary"
            :disabled="savingDesign"
            @click="saveDesign({ content_padding: clampedPadding, horizontal_alignment: design.horizontalAlignment, vertical_alignment: design.verticalAlignment })"
          >
            <span v-if="savingDesign" class="loader-dot" />
            {{ savingDesign ? 'Saving...' : 'Save layout settings' }}
          </button>
        </div>

        <div v-else-if="activeSection === 'additional'" class="space-y-3">
          <label class="inline-flex items-center gap-2 text-sm text-slate-700">
            <input v-model="design.showOrderBadge" type="checkbox" />
            Show slide number badge
          </label>
          <label class="inline-flex items-center gap-2 text-sm text-slate-700">
            <input v-model="design.roundedPreview" type="checkbox" />
            Rounded preview
          </label>

          <button
            class="btn-primary"
            :disabled="savingDesign"
            @click="saveDesign({ additional: { show_order_badge: design.showOrderBadge, rounded_preview: design.roundedPreview } })"
          >
            <span v-if="savingDesign" class="loader-dot" />
            {{ savingDesign ? 'Saving...' : 'Save additional settings' }}
          </button>
        </div>

        <div v-else class="space-y-3">
          <p class="meta-copy max-w-prose">Export carousel as 1080x1350 PNG ZIP.</p>
          <button class="btn-primary" :disabled="exporting" @click="exportZip">
            <span v-if="exporting" class="loader-dot" />
            {{ exporting ? 'Exporting...' : 'Export ZIP' }}
          </button>
          <p v-if="exportState !== 'idle'" class="text-xs font-semibold uppercase text-slate-500">{{ exportStatusText }}</p>
        </div>
      </div>
    </div>

    <p v-if="message" class="rounded-[16px] bg-emerald-50 p-3 text-sm text-emerald-700">{{ message }}</p>

    <div v-if="templateModalOpen" class="fixed inset-0 z-50 flex items-center justify-center bg-black/35 p-4">
      <div class="w-full max-w-xl rounded-[16px] bg-white p-5 shadow-[var(--shadow-card)]">
        <div class="flex items-center justify-between gap-3">
          <h3 class="font-display text-2xl">Template Presets</h3>
          <button class="btn-secondary" @click="templateModalOpen = false">Close</button>
        </div>

        <label class="mt-3 inline-flex items-center gap-2 text-sm text-slate-700">
          <input v-model="applyToAllSlides" type="checkbox" />
          Apply to all slides
        </label>

        <div class="mt-4 grid gap-3 md:grid-cols-3">
          <button
            v-for="preset in templatePresets"
            :key="preset.id"
            class="rounded-[16px] border border-slate-200 p-4 text-left transition hover:border-ink"
            @click="applyTemplate(preset)"
          >
            <div class="mb-2 h-16 rounded-[12px] border border-slate-200/70 p-2" :style="{ backgroundColor: preset.bg, color: preset.text }">
              <p class="text-[11px] uppercase tracking-wide opacity-70">Header</p>
              <p class="font-display text-sm">Slide title</p>
            </div>
            <p class="font-display text-xl">{{ preset.title }}</p>
            <p class="meta-copy">{{ preset.hint }}</p>
          </button>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.editor-preview-wrapper {
  overflow: visible;
  display: flex;
  justify-content: center;
}

.editor-preview-scale {
  --editor-scale: 0.95;
  width: min(100%, 560px);
  transform: scale(var(--editor-scale));
  transform-origin: top center;
}

.editor-preview-canvas {
  overflow: visible;
}

.editor-content {
  padding: clamp(24px, 3.2vw, 42px);
}

.editor-title,
.editor-body {
  overflow-wrap: break-word;
  word-break: normal;
}

.editor-title {
  color: #0f172a;
}

.editor-body {
  color: #334155;
}

@media (max-width: 1120px) {
  .editor-preview-scale {
    --editor-scale: 0.9;
    width: min(100%, 520px);
  }
}

@media (max-width: 820px) {
  .editor-preview-scale {
    --editor-scale: 0.85;
    width: min(100%, 490px);
  }
}

@media (max-width: 560px) {
  .editor-preview-scale {
    --editor-scale: 0.8;
    width: min(100%, 450px);
  }
}

@media (max-height: 900px) {
  .editor-preview-scale {
    --editor-scale: 0.9;
  }
}

@media (max-height: 780px) {
  .editor-preview-scale {
    --editor-scale: 0.84;
  }
}

@media (max-height: 680px) {
  .editor-preview-scale {
    --editor-scale: 0.78;
  }
}
</style>
