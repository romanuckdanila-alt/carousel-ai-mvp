# carousel-ai (MVP)

`carousel-ai` — это MVP-сервис для генерации Instagram-каруселей из текста/видео, с последующим редактированием слайдов и экспортом в ZIP с изображениями.

## Quick Demo Flow
Быстрый демо-сценарий:

1. Запустите проект
```bash
docker compose up --build
```
2. Откройте приложение  
`http://localhost:3000`
3. Нажмите "Create Carousel"
4. Вставьте исходный текст или ссылку на видео
5. Нажмите "Generate"
6. Дождитесь завершения генерации слайдов
7. Откройте редактор и при необходимости настройте layout
8. Нажмите "Export"
9. Скачайте ZIP с изображениями слайдов

В базе уже может быть демо-карусель (`AI Startup Onboarding Guide`) для быстрого просмотра preview/editor/export без ручного создания.

## Описание проекта
Продукт позволяет:
- создавать карусели из исходного контента,
- запускать асинхронную генерацию слайдов через LLM,
- просматривать результат до редактирования,
- настраивать дизайн (шаблон, фон, текст, выравнивание),
- экспортировать слайды как PNG (1080x1350) в ZIP.

## Архитектура
Система состоит из 4 сервисов:
- `frontend` (Nuxt 3): пользовательский интерфейс,
- `backend` (FastAPI): API и бизнес-логика,
- `postgres`: хранение данных,
- `minio`: файловое хранилище (S3-совместимое).

Ключевые пайплайны:
- генерация слайдов: OpenRouter -> валидация JSON -> запись в БД,
- экспорт: Playwright рендерит PNG -> архивирование -> загрузка в MinIO.

## Стек
- FastAPI
- Nuxt 3 (Vue 3)
- PostgreSQL
- MinIO
- Docker Compose
- SQLAlchemy
- Playwright
- OpenRouter (через OpenAI SDK)

## Как запустить
```bash
docker compose up --build
```

Открыть:
- Frontend: `http://localhost:3000`
- Backend: `http://localhost:8000`

## Флоу продукта
1. Создать карусель
2. Сгенерировать слайды
3. Посмотреть Preview
4. Отредактировать в Editor
5. Экспортировать ZIP

## Описание API
Основные эндпоинты:
- `GET /health`
- `/carousels`
  - `GET /carousels`
  - `POST /carousels`
  - `GET /carousels/{id}`
  - `DELETE /carousels/{id}`
- `/slides`
  - `GET /carousels/{id}/slides`
  - `PATCH /carousels/{id}/slides/{slide_id}`
- `/design`
  - `PATCH /carousels/{id}/design`
- `/generations`
  - `POST /generations`
  - `GET /generations/{id}`
- `/assets`
  - `POST /assets/upload`
- `/exports`
  - `POST /exports`
  - `GET /exports/{id}`

Пример запуска генерации:
```bash
curl -X POST http://localhost:8000/generations \
  -H "Content-Type: application/json" \
  -d '{"carousel_id":"<CAROUSEL_ID>"}'
```

## LLM генерация
Пайплайн генерации:
1. Создается задача (`POST /generations`).
2. FastAPI запускает фоновую обработку (`BackgroundTasks`).
3. `LLMService` делает запрос в OpenRouter.
4. Ответ проверяется как JSON со структурой `{"slides": [...]}`.
5. Если JSON слегка поврежден, применяется этап JSON repair.
6. Если запрос/валидация окончательно неуспешны, включается fallback на локальные слайды.

Провайдер:
- OpenRouter (`/chat/completions`)
- модель по умолчанию: `openai/gpt-4o-mini`

## Экспорт
1. Вызывается `POST /exports`.
2. Слайды рендерятся Playwright в PNG `1080x1350`.
3. Файлы архивируются (`slide_01.png`, `slide_02.png`, ...).
4. ZIP загружается в MinIO.
5. Возвращается presigned URL для скачивания.

## Какие упрощения сделаны для MVP
- Асинхронные задачи реализованы через `BackgroundTasks` (без отдельной очереди/воркеров типа Celery).
- Нет полноценной аутентификации и мульти-тенантности.
- Дизайн-настройки хранятся в `source_payload.design` (JSON), без отдельной normalized схемы.
- Экспорт выполняется синхронно в рамках API-вызова `POST /exports`.
- Токены оцениваются эвристически на фронтенде (без точного токенайзера).
- Очистка объектов в MinIO при удалении карусели выполняется в режиме best-effort.

## Демо-данные
При пустой БД backend создает демонстрационную карусель:
- заголовок: `AI Startup Onboarding Guide`
- 6 слайдов
- статус: `ready`

Это позволяет сразу проверить preview/editor/export после запуска.

## Инструменты
- Cursor
- ChatGPT
- Codex

## Оценка времени разработки
- MVP: ~9 часов
- Полировка UX/UI и отладка: ~6 часов
- Итого: ~15 часов

## Оценка расхода токенов
На одну генерацию (6–10 слайдов):
- Prompt/Input: ~900–1,700 токенов
- Completion/Output: ~350–1,200 токенов
- Итого: ~1,250–2,900 токенов

## Примечание по дизайну
Figma-макет использовался как референс для структуры экранов, иерархии интерфейса и логики переходов между основными разделами приложения (My Carousels → Create → Preview → Editor).

Так как целью задания было создание работающего end-to-end MVP, основной фокус реализации был сделан на:

- рабочем пользовательском флоу
- понятной визуальной иерархии
- адаптивной верстке
- простом и консистентном дизайн-подходе

Вместо точного pixel-perfect воспроизведения макета интерфейс был реализован с использованием упрощённой компонентной структуры на базе Tailwind.

Это позволило быстрее реализовать ключевые функции редактора (настройки шаблонов, фон, layout, дополнительные параметры) и упростить дальнейшее расширение интерфейса.

Общая структура экранов и взаимодействие пользователя соответствуют референсу из Figma, при этом визуальная часть была упрощена для MVP.

При необходимости интерфейс можно дополнительно привести к pixel-perfect соответствию макету.

## Примеры API
### Создание карусели
```bash
curl -X POST http://localhost:8000/carousels \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Demo Carousel",
    "source_type": "text",
    "source_payload": {"text": "Example post text"},
    "slides_count": 6,
    "language": "EN"
  }'
```

### Список каруселей
```bash
curl http://localhost:8000/carousels
```

### Генерация слайдов
```bash
curl -X POST http://localhost:8000/generations \
  -H "Content-Type: application/json" \
  -d '{
    "carousel_id": "<carousel_id>"
  }'
```

### Экспорт карусели
```bash
curl -X POST http://localhost:8000/exports \
  -H "Content-Type: application/json" \
  -d '{
    "carousel_id": "<carousel_id>"
  }'
```

## Архитектура
Backend:
- FastAPI
- PostgreSQL
- MinIO (S3-совместимое хранилище)

Frontend:
- Nuxt 3
- Vue
- TailwindCSS

Infrastructure:
- Docker
- docker-compose

Ключевые модули:

`backend/`
- `app/`
- `models`
- `services`
- `routes`

`frontend/`
- `pages`
- `composables`
- `assets`

## Заметки по разработке
Время разработки:
~7–9 часов на реализацию MVP.

Использованные инструменты:
- Codex
- ChatGPT

## Использование LLM
Провайдер:
OpenRouter

Модель:
GPT-класса

Назначение:
Генерация структуры слайдов карусели (title, body, footer).

Средняя стоимость генерации:
примерно $0.01–$0.02 за одну карусель в зависимости от объема токенов.

Генерация выполняется асинхронно и обычно занимает 5–15 секунд в зависимости от времени ответа LLM.
