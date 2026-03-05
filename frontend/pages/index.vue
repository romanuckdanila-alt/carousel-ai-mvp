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
  if (status === "ready") return "border-emerald-200 bg-emerald-50 text-emerald-700"
  if (status === "generating") return "border-amber-200 bg-amber-50 text-amber-700"
  if (status === "failed") return "border-rose-200 bg-rose-50 text-rose-700"
  return "border-slate-200 bg-slate-50 text-slate-600"
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

    <div v-if="loading" :class="viewMode === 'grid' ? 'grid gap-6 md:grid-cols-2 xl:grid-cols-3' : 'grid gap-3'">
      <article v-for="i in 6" :key="`s-${i}`" class="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
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

    <div
      v-else
      :class="viewMode === 'grid'
        ? 'grid items-stretch gap-6 md:grid-cols-2 xl:grid-cols-3'
        : 'grid divide-y divide-slate-200 rounded-xl border border-slate-200 bg-white'"
    >
      <article
        v-for="carousel in carousels"
        :key="carousel.id"
        class="flex flex-col rounded-xl border border-slate-200 bg-white p-6 transition hover:shadow-md"
        :class="viewMode === 'grid' ? 'h-full' : 'h-auto rounded-none border-0 p-4 shadow-none hover:shadow-none'"
      >
        <div class="flex items-center justify-between gap-2">
          <div class="inline-flex items-center rounded-full border px-2 py-0.5 text-xs font-semibold" :class="statusClass(mapCarouselStatus(carousel.status))">
              {{ mapCarouselStatus(carousel.status) }}
          </div>
          <span class="text-xs text-slate-500">{{ createdLabel(carousel.created_at) }}</span>
        </div>

        <h2 class="mt-3 line-clamp-2 text-lg font-semibold tracking-tight text-slate-900">{{ carousel.title }}</h2>

        <p v-if="previews[carousel.id]?.body" class="mt-2 line-clamp-2 text-sm leading-relaxed text-slate-600">
          {{ previews[carousel.id]?.body }}
        </p>
        <p v-else class="mt-2 text-sm leading-relaxed text-slate-500">No slide preview yet.</p>

        <p class="mt-3 text-xs text-slate-500">
          Slides {{ carousel.slides_count }} · {{ carousel.language }} · {{ carousel.source_type }}
        </p>

        <div class="mt-4 flex items-center gap-2">
          <NuxtLink :to="`/preview/${carousel.id}`" class="btn-secondary !px-3 !py-1.5">Open</NuxtLink>
          <NuxtLink :to="`/editor/${carousel.id}`" class="btn-primary !px-3 !py-1.5">Continue editing</NuxtLink>
          <button
            class="btn-secondary !border-rose-200 !px-3 !py-1.5 !text-rose-700 hover:!bg-rose-50"
            :disabled="Boolean(deletingId)"
            @click="openDeleteDialog(carousel.id)"
          >
            {{ deletingId === carousel.id ? 'Deleting...' : 'Delete' }}
          </button>
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
