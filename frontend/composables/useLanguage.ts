import { translations } from "~/i18n"

type Language = keyof typeof translations
type TranslationKey = keyof (typeof translations)["en"]

const STORAGE_KEY = "carousel_ai_ui_lang"

export const useLanguage = () => {
  const lang = useState<Language>("ui-language", () => "en")
  const initialized = useState<boolean>("ui-language-initialized", () => false)

  const setLang = (next: Language) => {
    lang.value = next
    if (process.client) {
      localStorage.setItem(STORAGE_KEY, next)
    }
  }

  const t = (key: TranslationKey) => {
    return translations[lang.value][key] ?? translations.en[key] ?? key
  }

  if (process.client && !initialized.value) {
    const saved = localStorage.getItem(STORAGE_KEY)
    if (saved === "en" || saved === "ru") {
      lang.value = saved
    }
    initialized.value = true
  }

  return { lang, setLang, t }
}

