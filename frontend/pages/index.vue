<script setup lang="ts">
import type { Carousel, Slide } from "~/composables/useApi"
import { mapCarouselStatus } from "~/composables/useApi"

const { api } = useApi()

const loading = ref(true)
const error = ref("")
const carousels = ref<Carousel[]>([])
const previews = reactive<Record<string, Slide | null>>({})
const viewMode = ref<"grid" | "list">("grid")
const deleteDialogCarouselId = ref<string | null>(null)
const deletingId = ref<string | null>(null)

const statusClass = (status: string) => {
  if (status === "ready") return "bg-emerald-100 text-emerald-700"
  if (status === "generating") return "bg-amber-100 text-amber-800"
  if (status === "failed") return "bg-rose-100 text-rose-700"
  return "bg-slate-100 text-slate-600"
}

const statusDotClass = (status: string) => {
  if (status === "ready") return "bg-emerald-500"
  if (status === "generating") return "bg-amber-500"
  if (status === "failed") return "bg-rose-500"
  return "bg-slate-400"
}

const createdLabel = (raw: string) =>
  new Date(raw).toLocaleString([], {
    month: "short",
    day: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit"
  })

const load = async () => {
  loading.value = true
  error.value = ""

  try {
    const list = await api<Carousel[]>("/carousels")
    carousels.value = list

    await Promise.all(
      list.map(async (carousel) => {
        try {
          const slides = await api<Slide[]>(`/carousels/${carousel.id}/slides`)
          previews[carousel.id] = slides[0] || null
        } catch {
          previews[carousel.id] = null
        }
      })
    )
  } catch (err: any) {
    error.value = err?.data?.detail || err?.message || "Failed to load carousels"
  } finally {
    loading.value = false
  }
}

const openDeleteDialog = (carouselId: string) => {
  deleteDialogCarouselId.value = carouselId
}

const closeDeleteDialog = () => {
  if (deletingId.value) return
  deleteDialogCarouselId.value = null
}

const confirmDelete = async () => {
  if (!deleteDialogCarouselId.value) return
  const id = deleteDialogCarouselId.value
  deletingId.value = id
  error.value = ""

  try {
    await api<{ status: string }>(`/carousels/${id}`, { method: "DELETE" })
    carousels.value = carousels.value.filter((carousel) => carousel.id !== id)
    delete previews[id]
    deleteDialogCarouselId.value = null
  } catch (err: any) {
    error.value = err?.data?.detail || err?.message || "Failed to delete carousel"
  } finally {
    deletingId.value = null
  }
}

onMounted(load)
</script>

<template>
  <section class="space-y-6">
    <div class="panel p-6">
      <div class="flex flex-wrap items-start justify-between gap-4">
        <div class="space-y-2">
          <p class="meta-label">Workspace</p>
          <h1 class="page-title font-display">My Carousels</h1>
          <p class="body-copy max-w-[65ch]">Manage generated carousels, continue editing and export final assets.</p>
        </div>

        <div class="flex flex-wrap items-center gap-2">
          <button class="btn-secondary" @click="viewMode = 'grid'">Grid</button>
          <button class="btn-secondary" @click="viewMode = 'list'">List</button>
          <button class="btn-secondary" @click="load">Refresh</button>
          <NuxtLink to="/create" class="btn-primary">Create Carousel</NuxtLink>
        </div>
      </div>
    </div>

    <p v-if="error" class="rounded-xl bg-rose-50 p-3 text-sm text-rose-700">{{ error }}</p>

    <div v-if="loading" :class="viewMode === 'grid' ? 'grid gap-4 md:grid-cols-2 xl:grid-cols-3' : 'grid gap-3'">
      <article v-for="i in 6" :key="`s-${i}`" class="panel overflow-hidden p-4">
        <div class="skeleton h-36 w-full" />
        <div class="mt-4 space-y-2">
          <div class="skeleton h-6 w-2/3" />
          <div class="skeleton h-4 w-1/2" />
          <div class="grid grid-cols-3 gap-2 pt-2">
            <div class="skeleton h-10 w-full" />
            <div class="skeleton h-10 w-full" />
            <div class="skeleton h-10 w-full" />
          </div>
        </div>
      </article>
    </div>

    <div v-else-if="carousels.length === 0" class="panel px-6 py-14 text-center">
      <p class="meta-label">Empty</p>
      <h2 class="mt-2 font-display text-3xl font-semibold text-slate-900">Create your first carousel</h2>
      <p class="body-copy mx-auto mt-2 max-w-prose">Start from text or video and generate editable slide decks in minutes.</p>
      <NuxtLink to="/create" class="btn-primary mt-6 px-8 py-3 text-base">Create</NuxtLink>
    </div>

    <div v-else :class="viewMode === 'grid' ? 'grid items-stretch gap-4 md:grid-cols-2 xl:grid-cols-3' : 'grid items-start gap-3'">
      <article
        v-for="carousel in carousels"
        :key="carousel.id"
        class="panel slide-card flex flex-col overflow-hidden border border-slate-200/70"
        :class="viewMode === 'grid' ? 'h-full' : 'h-auto'"
      >
        <div class="relative border-b border-slate-200/70 bg-white p-4">
          <div class="flex items-center justify-between gap-2">
            <div class="inline-flex items-center gap-2 rounded-full px-2.5 py-1 text-xs font-semibold" :class="statusClass(mapCarouselStatus(carousel.status))">
              <span class="h-2 w-2 rounded-full" :class="statusDotClass(mapCarouselStatus(carousel.status))" />
              {{ mapCarouselStatus(carousel.status) }}
            </div>
            <span class="text-[11px] text-slate">{{ createdLabel(carousel.created_at) }}</span>
          </div>

          <div class="mt-3 min-h-32 rounded-xl border border-slate-200/70 bg-slate-50 p-3">
            <template v-if="previews[carousel.id]">
              <p class="meta-label">First slide</p>
              <h3 class="mt-1 line-clamp-2 font-display text-lg font-medium leading-snug text-slate-900">{{ previews[carousel.id]?.title }}</h3>
              <p class="body-copy mt-2 line-clamp-3">{{ previews[carousel.id]?.body }}</p>
            </template>
            <div v-else class="flex h-full min-h-24 items-center justify-center rounded-lg border border-dashed border-slate-300 text-sm text-slate">
              No slide preview
            </div>
          </div>
        </div>

        <div class="flex flex-1 flex-col gap-4 p-4">
          <h2 class="card-title line-clamp-2 font-display">{{ carousel.title }}</h2>

          <div class="grid grid-cols-3 gap-2">
            <div class="rounded-xl bg-slate-50 p-2">
              <p class="meta-label">Slides</p>
              <p class="text-base font-semibold text-slate-900">{{ carousel.slides_count }}</p>
            </div>
            <div class="rounded-xl bg-slate-50 p-2">
              <p class="meta-label">Language</p>
              <p class="text-base font-semibold text-slate-900">{{ carousel.language }}</p>
            </div>
            <div class="rounded-xl bg-slate-50 p-2">
              <p class="meta-label">Source</p>
              <p class="text-base font-semibold text-slate-900">{{ carousel.source_type }}</p>
            </div>
          </div>

          <div class="mt-auto flex flex-wrap gap-2 pt-1">
            <NuxtLink :to="`/preview/${carousel.id}`" class="btn-secondary">Open</NuxtLink>
            <NuxtLink :to="`/editor/${carousel.id}`" class="btn-primary">Continue editing</NuxtLink>
            <button
              class="btn-secondary !border-rose-200 !text-rose-700 hover:!bg-rose-50"
              :disabled="Boolean(deletingId)"
              @click="openDeleteDialog(carousel.id)"
            >
              {{ deletingId === carousel.id ? 'Deleting...' : 'Delete' }}
            </button>
          </div>
        </div>
      </article>
    </div>

    <div v-if="deleteDialogCarouselId" class="fixed inset-0 z-50 flex items-center justify-center bg-black/35 p-4">
      <div class="panel w-full max-w-sm p-5">
        <h3 class="section-title font-display">Delete this carousel?</h3>
        <p class="meta-copy mt-2">This action cannot be undone.</p>
        <div class="mt-5 flex items-center justify-end gap-2">
          <button class="btn-secondary" :disabled="Boolean(deletingId)" @click="closeDeleteDialog">Cancel</button>
          <button class="btn-secondary !border-rose-200 !bg-rose-600 !text-white hover:!bg-rose-700" :disabled="Boolean(deletingId)" @click="confirmDelete">
            {{ deletingId ? 'Deleting...' : 'Delete' }}
          </button>
        </div>
      </div>
    </div>
  </section>
</template>
