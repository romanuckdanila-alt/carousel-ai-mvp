<script setup lang="ts">
const { lang, setLang, t } = useLanguage()
const isLangMenuOpen = ref(false)
const langMenuRef = ref<HTMLElement | null>(null)

const toggleLangMenu = () => {
  isLangMenuOpen.value = !isLangMenuOpen.value
}

const closeLangMenu = () => {
  isLangMenuOpen.value = false
}

const handleDocumentClick = (event: MouseEvent) => {
  if (!langMenuRef.value) return
  if (!langMenuRef.value.contains(event.target as Node)) {
    closeLangMenu()
  }
}

onMounted(() => {
  document.addEventListener("click", handleDocumentClick)
})

onBeforeUnmount(() => {
  document.removeEventListener("click", handleDocumentClick)
})
</script>

<template>
  <div class="min-h-screen bg-slate-50">
    <div class="mx-auto max-w-6xl px-6 py-10">
      <header class="mb-8 flex flex-wrap items-center justify-between gap-4">
        <NuxtLink to="/" class="font-display text-3xl tracking-tight text-ink">carousel-ai</NuxtLink>
        <nav class="flex items-center gap-2 text-sm">
          <NuxtLink to="/" class="btn-secondary">{{ t("myCarousels") }}</NuxtLink>
          <NuxtLink to="/create" class="btn-primary">{{ t("createCarousel") }}</NuxtLink>
          <div ref="langMenuRef" class="relative">
            <button
              type="button"
              class="flex items-center gap-2 rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-sm"
              @click.stop="toggleLangMenu"
            >
              <span>🌐</span>
              <span class="uppercase">{{ lang }}</span>
            </button>
            <div
              v-if="isLangMenuOpen"
              class="absolute right-0 z-20 mt-2 w-36 rounded-lg border border-slate-200 bg-white p-1 shadow-sm"
            >
              <button
                type="button"
                class="block w-full rounded-md px-3 py-2 text-left text-sm hover:bg-slate-50"
                @click="setLang('en'); closeLangMenu()"
              >
                English
              </button>
              <button
                type="button"
                class="block w-full rounded-md px-3 py-2 text-left text-sm hover:bg-slate-50"
                @click="setLang('ru'); closeLangMenu()"
              >
                Русский
              </button>
            </div>
          </div>
        </nav>
      </header>
      <NuxtPage />
    </div>
  </div>
</template>
