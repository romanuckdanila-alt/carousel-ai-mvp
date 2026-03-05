<template>
  <div class="min-h-screen bg-slate-50">
    <div class="mx-auto max-w-6xl px-6 py-10">
      <header class="mb-8 flex flex-wrap items-center justify-between gap-4">
        <NuxtLink to="/" class="font-display text-3xl tracking-tight text-ink">carousel-ai</NuxtLink>
        <nav class="flex items-center gap-2 text-sm">
          <NuxtLink to="/" class="btn-secondary">Carousels</NuxtLink>
          <NuxtLink to="/create" class="btn-primary">Create</NuxtLink>
        </nav>
      </header>
      <NuxtPage />
    </div>
  </div>
</template>
