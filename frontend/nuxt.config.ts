export default defineNuxtConfig({
  ssr: false,
  devtools: { enabled: false },
  modules: ["@nuxtjs/tailwindcss"],
  css: ["~/assets/css/main.css"],
  runtimeConfig: {
    public: {
      apiBase: process.env.NUXT_PUBLIC_API_BASE || "http://localhost:8000"
    }
  },
  app: {
    head: {
      title: "carousel-ai",
      meta: [
        { name: "viewport", content: "width=device-width, initial-scale=1" }
      ]
    }
  }
})
