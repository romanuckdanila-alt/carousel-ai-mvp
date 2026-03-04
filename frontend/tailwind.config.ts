import type { Config } from "tailwindcss"

export default {
  content: [
    "./app.vue",
    "./components/**/*.{vue,js,ts}",
    "./pages/**/*.{vue,js,ts}",
    "./composables/**/*.{js,ts}",
    "./plugins/**/*.{js,ts}"
  ],
  theme: {
    extend: {
      fontFamily: {
        display: ["'Space Grotesk'", "'Avenir Next'", "sans-serif"],
        body: ["'IBM Plex Sans'", "'Segoe UI'", "sans-serif"]
      },
      colors: {
        ink: "#102A43",
        slate: "#334E68",
        shell: "#F7FBFC",
        amber: "#F6BD60",
        mint: "#84DCC6"
      }
    }
  },
  plugins: []
} satisfies Config
