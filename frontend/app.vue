<template>
  <div class="mx-auto max-w-6xl px-4 pb-10 pt-6 sm:px-6 lg:px-8">
    <header class="mb-8 flex flex-wrap items-center justify-between gap-4">
      <NuxtLink to="/" class="font-display text-3xl tracking-tight text-ink">carousel-ai</NuxtLink>
      <nav class="flex items-center gap-2 text-sm">
        <NuxtLink to="/" class="btn-secondary">Carousels</NuxtLink>
        <NuxtLink to="/create" class="btn-primary">Create</NuxtLink>
      </nav>
    </header>
    <NuxtPage />
  </div>
</template>
