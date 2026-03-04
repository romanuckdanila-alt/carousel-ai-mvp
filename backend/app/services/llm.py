from __future__ import annotations

import json
import logging
import re
from typing import Any

from openai import OpenAI

from app.config import settings
from app.models import Carousel, Language


logger = logging.getLogger(__name__)


class LLMService:
    def __init__(self) -> None:
        self.client = None
        if settings.openrouter_api_key:
            self.client = OpenAI(
                api_key=settings.openrouter_api_key,
                base_url=settings.openrouter_base_url,
            )
            logger.info(
                "OpenRouter client initialized base_url=%s endpoint=%s model=%s",
                settings.openrouter_base_url,
                f"{settings.openrouter_base_url}/chat/completions",
                settings.openrouter_model,
            )

    def generate_slides(self, carousel: Carousel) -> dict[str, Any]:
        if not self.client:
            logger.warning(
                "OpenRouter API key missing; using fallback slides for carousel_id=%s",
                carousel.id,
            )
            return {"slides": self._fallback_slides(carousel), "provider": "local_fallback"}

        system_prompt = (
            "You generate concise Instagram carousel slides. "
            "Return strictly valid JSON with this shape only: "
            '{"slides":[{"order":1,"title":"","body":"","footer":""}]}'
        )
        user_prompt = (
            f"Create {carousel.slides_count} slides in {carousel.language.value}. "
            f"Carousel title: {carousel.title}. "
            f"Source type: {carousel.source_type.value}. "
            f"Source payload: {json.dumps(carousel.source_payload, ensure_ascii=False)}. "
            f"Style hint: {carousel.style_hint or 'none'}. "
            "Each slide must be distinct, specific, and practical. "
            "Do not wrap JSON in markdown. Return JSON only."
        )

        try:
            content, model_used = self._request_openrouter(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                carousel=carousel,
            )
            payload = self._parse_json_payload(content)
            slides = self._validate_and_normalize_slides(payload, carousel)
            return {"slides": slides, "provider": "openrouter", "model": model_used}
        except Exception as exc:
            logger.exception(
                "Falling back to local slides for carousel_id=%s due to generation error: %s",
                carousel.id,
                exc,
            )
            return {
                "slides": self._fallback_slides(carousel),
                "provider": "local_fallback",
                "error": str(exc),
            }

    def _request_openrouter(self, system_prompt: str, user_prompt: str, carousel: Carousel) -> tuple[str, str]:
        last_error: Exception | None = None
        models_to_try = [settings.openrouter_model]
        backup_model = "openrouter/free"
        if settings.openrouter_model != backup_model:
            models_to_try.append(backup_model)

        for model_name in models_to_try:
            for attempt in range(1, 4):
                request_payload = {
                    "model": model_name,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    "temperature": 0.7,
                }
                logger.info(
                    "OpenRouter request attempt=%s carousel_id=%s model=%s endpoint=%s headers=%s payload=%s",
                    attempt,
                    carousel.id,
                    model_name,
                    f"{settings.openrouter_base_url}/chat/completions",
                    json.dumps(
                        {
                            "Authorization": "Bearer ***",
                            "Content-Type": "application/json",
                        }
                    ),
                    json.dumps(request_payload, ensure_ascii=False),
                )

                try:
                    completion = self.client.chat.completions.create(
                        model=model_name,
                        messages=request_payload["messages"],
                        temperature=0.7,
                        timeout=60,
                    )
                    content = completion.choices[0].message.content or ""
                    logger.info(
                        "OpenRouter response attempt=%s carousel_id=%s model=%s content=%s",
                        attempt,
                        carousel.id,
                        model_name,
                        content,
                    )
                    return content, model_name
                except Exception as exc:
                    last_error = exc
                    status_code = getattr(exc, "status_code", None)
                    logger.warning(
                        "OpenRouter request failed attempt=%s carousel_id=%s model=%s status_code=%s error=%s",
                        attempt,
                        carousel.id,
                        model_name,
                        status_code,
                        exc,
                    )
                    # If the configured model is blocked by billing, move to free backup model.
                    if status_code == 402 and model_name == settings.openrouter_model and backup_model in models_to_try:
                        logger.warning(
                            "Primary model billing issue for carousel_id=%s. Trying backup model=%s",
                            carousel.id,
                            backup_model,
                        )
                        break

        raise RuntimeError(f"OpenRouter request failed across all retries: {last_error}")

    def _parse_json_payload(self, content: str) -> dict[str, Any]:
        cleaned = self._strip_code_fences(content)
        try:
            payload = json.loads(cleaned)
            if not isinstance(payload, dict):
                raise ValueError("OpenRouter payload root is not an object")
            return payload
        except json.JSONDecodeError as exc:
            logger.warning("OpenRouter JSON parse failed on raw content: %s", cleaned)
            candidate = self._extract_json_candidate(cleaned)
            if not candidate:
                logger.error("OpenRouter response has no JSON object to parse")
                raise ValueError("OpenRouter response does not contain JSON object") from exc

            try:
                payload = json.loads(candidate)
                if not isinstance(payload, dict):
                    raise ValueError("OpenRouter payload root is not an object")
                return payload
            except json.JSONDecodeError as nested_exc:
                repaired = self._repair_json(candidate)
                try:
                    payload = json.loads(repaired)
                    if not isinstance(payload, dict):
                        raise ValueError("OpenRouter payload root is not an object")
                    logger.info("OpenRouter JSON repaired successfully")
                    return payload
                except json.JSONDecodeError as repaired_exc:
                    logger.error(
                        "OpenRouter extracted JSON parsing failed: %s; repair_error=%s",
                        nested_exc,
                        repaired_exc,
                    )
                    raise ValueError("OpenRouter JSON parsing failed") from repaired_exc

    def _strip_code_fences(self, text: str) -> str:
        stripped = text.strip()
        if stripped.startswith("```") and stripped.endswith("```"):
            stripped = re.sub(r"^```(?:json)?\s*", "", stripped, flags=re.IGNORECASE)
            stripped = re.sub(r"\s*```$", "", stripped)
        return stripped.strip()

    def _extract_json_candidate(self, text: str) -> str | None:
        first_brace = text.find("{")
        if first_brace == -1:
            return None

        last_brace = text.rfind("}")
        if last_brace == -1 or last_brace < first_brace:
            return text[first_brace:].strip()
        return text[first_brace : last_brace + 1].strip()

    def _repair_json(self, text: str) -> str:
        # Common malformed output: trailing commas and missing closing braces/brackets.
        repaired = re.sub(r",\s*([}\]])", r"\1", text.strip())
        stack: list[str] = []
        in_string = False
        escaped = False

        for char in repaired:
            if in_string:
                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == '"':
                    in_string = False
                continue

            if char == '"':
                in_string = True
                continue

            if char in "{[":
                stack.append(char)
                continue

            if char in "}]":
                if not stack:
                    continue
                top = stack[-1]
                if (top == "{" and char == "}") or (top == "[" and char == "]"):
                    stack.pop()

        closers = []
        for opener in reversed(stack):
            closers.append("}" if opener == "{" else "]")
        return repaired + "".join(closers)

    def _validate_and_normalize_slides(self, payload: dict[str, Any], carousel: Carousel) -> list[dict[str, Any]]:
        slides = payload.get("slides")
        if not isinstance(slides, list):
            logger.error("OpenRouter payload missing 'slides' array: %s", payload)
            raise ValueError("OpenRouter payload is missing 'slides' list")

        if len(slides) < carousel.slides_count:
            logger.error(
                "OpenRouter returned insufficient slides carousel_id=%s expected=%s got=%s",
                carousel.id,
                carousel.slides_count,
                len(slides),
            )
            raise ValueError("OpenRouter returned fewer slides than requested")

        normalized: list[dict[str, Any]] = []
        for idx in range(1, carousel.slides_count + 1):
            source = slides[idx - 1]
            if not isinstance(source, dict):
                raise ValueError(f"Slide {idx} is not an object")

            title = str(source.get("title", "")).strip()
            body = str(source.get("body", "")).strip()
            footer = str(source.get("footer", "")).strip()

            if not title or not body:
                raise ValueError(f"Slide {idx} is missing required title/body fields")

            normalized.append(
                {
                    "order": idx,
                    "title": title,
                    "body": body,
                    "footer": footer,
                }
            )

        return normalized

    def _fallback_slides(self, carousel: Carousel) -> list[dict[str, Any]]:
        return [
            {
                "order": idx,
                "title": self._fallback_title(idx, carousel.language),
                "body": self._fallback_body(idx, carousel.language),
                "footer": self._fallback_footer(carousel.language),
            }
            for idx in range(1, carousel.slides_count + 1)
        ]

    def _fallback_title(self, idx: int, language: Language) -> str:
        if language == Language.RU:
            return f"Слайд {idx}: ключевая мысль"
        if language == Language.FR:
            return f"Slide {idx} : idee cle"
        return f"Slide {idx}: key point"

    def _fallback_body(self, idx: int, language: Language) -> str:
        if language == Language.RU:
            return "Кратко раскройте идею, добавьте 2-3 полезных тезиса и один практический шаг."
        if language == Language.FR:
            return "Expliquez l'idee en 2-3 points utiles et ajoutez une action concrete."
        return "Explain the idea in 2-3 useful bullets and add one practical action."

    def _fallback_footer(self, language: Language) -> str:
        if language == Language.RU:
            return "Сохраните пост и поделитесь с командой"
        if language == Language.FR:
            return "Enregistrez ce post et partagez-le"
        return "Save this post and share it"
