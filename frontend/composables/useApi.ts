export type CarouselLanguage = "RU" | "EN" | "FR"
export type CarouselSourceType = "text" | "video"

export interface CarouselDesignSettings {
  template?: "Classic" | "Bold" | "Minimal"
  apply_to_all_slides?: boolean
  background_color?: string
  background_image_url?: string
  dark_overlay?: boolean
  dark_overlay_opacity?: number
  show_header?: boolean
  show_footer?: boolean
  header_text?: string
  footer_text?: string
  content_padding?: number
  horizontal_alignment?: "left" | "center" | "right"
  vertical_alignment?: "top" | "center" | "bottom"
  additional?: Record<string, unknown>
}

export interface CarouselSourcePayload {
  text?: string
  video_url?: string
  links?: string[]
  design?: CarouselDesignSettings
  [key: string]: unknown
}

export interface Carousel {
  id: string
  title: string
  source_type: CarouselSourceType
  source_payload: CarouselSourcePayload
  slides_count: number
  language: CarouselLanguage
  style_hint: string | null
  status: string
  created_at: string
}

export interface Slide {
  id: string
  carousel_id: string
  order: number
  title: string
  body: string
  footer: string
}

export interface ExportResult {
  id: string
  carousel_id: string
  status: string
  zip_url: string | null
}

export interface GenerationResult {
  id: string
  carousel_id: string
  status: "pending" | "running" | "completed" | "failed"
  result_json: Record<string, unknown> | null
  created_at: string
}

export interface AssetUploadResult {
  key: string
  url: string
}

export interface CarouselDesignUpdatePayload {
  template?: string
  apply_to_all_slides?: boolean
  background_color?: string
  background_image_url?: string
  dark_overlay?: boolean
  dark_overlay_opacity?: number
  show_header?: boolean
  show_footer?: boolean
  header_text?: string
  footer_text?: string
  content_padding?: number
  horizontal_alignment?: "left" | "center" | "right"
  vertical_alignment?: "top" | "center" | "bottom"
  additional?: Record<string, unknown>
}

export const mapCarouselStatus = (status: string) => {
  if (status === "draft") return "draft"
  if (status === "generating") return "generating"
  if (status === "ready") return "ready"
  if (status === "generation_failed") return "failed"
  if (status === "generated" || status === "generated_fallback" || status === "exported") return "ready"
  return status
}

export const mapGenerationStatus = (status: GenerationResult["status"] | string) => {
  if (status === "pending") return "queued"
  if (status === "running") return "running"
  if (status === "completed") return "done"
  return "failed"
}

export const wait = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms))

export const useApi = () => {
  const config = useRuntimeConfig()
  const baseUrl = config.public.apiBase as string

  const api = <T>(path: string, options?: Parameters<typeof $fetch<T>>[1]) => {
    return $fetch<T>(`${baseUrl}${path}`, options)
  }

  return { api, baseUrl }
}
