<script setup lang="ts">
import type { Carousel, Slide } from "~/composables/useApi"
import { mapCarouselStatus } from "~/composables/useApi"

const { api } = useApi()

const loading = ref(true)
const error = ref("")
const carousels = ref<Carousel[]>([])
const previews = reactive<Record<string, Slide | null>>({})
const viewMode = ref<"grid" | "list">("grid")

const statusClass = (status: string) => {
  if (status === "ready") return "bg-emerald-100 text-emerald-700"
  if (status === "generating") return "bg-amber-100 text-amber-700"
  if (status === "failed") return "bg-rose-100 text-rose-700"
  return "bg-slate-100 text-slate-600"
}

const createdLabel = (raw: string) =>
  new Date(raw).toLocaleString([], {
    month: "short",
    day: "2-digit",
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

onMounted(load)
</script>

<template>
  <section class="space-y-5">
    <div class="panel p-5">
      <div class="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p class="text-xs uppercase tracking-[0.2em] text-slate">Workspace</p>
          <h1 class="font-display text-3xl">My Carousels</h1>
          <p class="mt-1 text-sm text-slate">Track generation status, preview first slide and continue editing.</p>
        </div>

        <div class="flex items-center gap-2">
          <button class="btn-secondary" @click="viewMode = 'grid'">Grid</button>
          <button class="btn-secondary" @click="viewMode = 'list'">List</button>
          <button class="btn-secondary" @click="load">Refresh</button>
          <NuxtLink to="/create" class="btn-primary">Create Carousel</NuxtLink>
        </div>
      </div>
    </div>

    <div v-if="loading" class="panel p-5 text-sm text-slate">Loading carousels...</div>
    <div v-else-if="error" class="rounded-xl bg-rose-50 p-3 text-sm text-rose-700">{{ error }}</div>

    <div v-else class="space-y-3">
      <div
        :class="viewMode === 'grid' ? 'grid gap-4 md:grid-cols-2 xl:grid-cols-3' : 'grid gap-3'"
      >
        <article
          v-for="carousel in carousels"
          :key="carousel.id"
          class="panel overflow-hidden border border-slate/10"
        >
          <div class="relative min-h-40 border-b border-slate/10 bg-gradient-to-br from-white via-white to-slate-50 p-4">
            <div class="absolute right-3 top-3 rounded-full px-2 py-1 text-xs font-semibold" :class="statusClass(mapCarouselStatus(carousel.status))">
              {{ mapCarouselStatus(carousel.status) }}
            </div>

            <div v-if="previews[carousel.id]" class="space-y-2 pr-16">
              <p class="text-xs uppercase tracking-wide text-slate">Preview slide 1</p>
              <h3 class="font-display text-xl leading-tight">{{ previews[carousel.id]?.title }}</h3>
              <p class="max-h-20 overflow-hidden text-sm text-slate">{{ previews[carousel.id]?.body }}</p>
            </div>
            <div v-else class="flex h-full items-center justify-center rounded-lg border border-dashed border-slate/20 text-sm text-slate">
              No slides yet
            </div>
          </div>

          <div class="space-y-3 p-4">
            <div>
              <h2 class="font-display text-2xl leading-tight">{{ carousel.title }}</h2>
              <p class="text-xs text-slate">Created {{ createdLabel(carousel.created_at) }}</p>
            </div>

            <div class="grid grid-cols-3 gap-2 text-xs text-slate">
              <div class="rounded-lg bg-slate/5 p-2"><span class="block text-[10px] uppercase">Slides</span>{{ carousel.slides_count }}</div>
              <div class="rounded-lg bg-slate/5 p-2"><span class="block text-[10px] uppercase">Language</span>{{ carousel.language }}</div>
              <div class="rounded-lg bg-slate/5 p-2"><span class="block text-[10px] uppercase">Source</span>{{ carousel.source_type }}</div>
            </div>

            <div class="flex flex-wrap gap-2 pt-1">
              <NuxtLink :to="`/preview/${carousel.id}`" class="btn-secondary">Open</NuxtLink>
              <NuxtLink :to="`/editor/${carousel.id}`" class="btn-primary">Continue editing</NuxtLink>
            </div>
          </div>
        </article>
      </div>

      <NuxtLink
        to="/create"
        class="panel flex min-h-24 items-center justify-center border border-dashed border-slate/25 text-sm font-semibold text-slate transition hover:bg-white"
      >
        + Create new carousel
      </NuxtLink>
    </div>
  </section>
</template>
