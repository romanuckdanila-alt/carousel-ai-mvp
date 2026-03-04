from __future__ import annotations

import html
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import uuid4
from zipfile import ZIP_DEFLATED, ZipFile

from playwright.sync_api import sync_playwright

from app.config import settings
from app.models import Carousel, Slide
from app.services.storage import StorageService


class ExportService:
    def __init__(self, storage: StorageService) -> None:
        self.storage = storage

    def render_and_upload_zip(self, carousel: Carousel, slides: list[Slide]) -> str:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            png_paths = self._render_pngs(tmp_path, carousel, slides)

            zip_path = tmp_path / "carousel.zip"
            with ZipFile(zip_path, "w", ZIP_DEFLATED) as archive:
                for png_path in png_paths:
                    archive.write(png_path, arcname=png_path.name)

            key = f"exports/{carousel.id}/{uuid4()}.zip"
            self.storage.upload_bytes(
                settings.exports_bucket,
                key,
                zip_path.read_bytes(),
                "application/zip",
            )
            return self.storage.public_presigned_get_url(settings.exports_bucket, key)

    def _render_pngs(self, tmp_path: Path, carousel: Carousel, slides: list[Slide]) -> list[Path]:
        rendered: list[Path] = []
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True, args=["--no-sandbox"])
            page = browser.new_page(viewport={"width": 1080, "height": 1350})
            for slide in sorted(slides, key=lambda s: s.order):
                html_content = self._slide_html(carousel.title, slide.order, slide.title, slide.body, slide.footer)
                page.set_content(html_content, wait_until="networkidle")
                png_path = tmp_path / f"slide_{slide.order:02d}.png"
                page.screenshot(path=str(png_path), type="png")
                rendered.append(png_path)
            browser.close()
        return rendered

    def _slide_html(self, carousel_title: str, order: int, title: str, body: str, footer: str) -> str:
        safe_title = html.escape(title)
        safe_body = html.escape(body).replace("\n", "<br />")
        safe_footer = html.escape(footer)
        safe_carousel_title = html.escape(carousel_title)

        return f"""
<!doctype html>
<html>
  <head>
    <meta charset=\"utf-8\" />
    <style>
      * {{ box-sizing: border-box; }}
      body {{
        margin: 0;
        width: 1080px;
        height: 1350px;
        font-family: 'Trebuchet MS', 'Segoe UI', sans-serif;
        background: linear-gradient(145deg, #f6f8ff 0%, #fef6e4 48%, #e6fffb 100%);
        color: #102a43;
      }}
      .frame {{
        width: 100%;
        height: 100%;
        padding: 68px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
      }}
      .chip {{
        display: inline-flex;
        width: fit-content;
        align-items: center;
        background: rgba(16, 42, 67, 0.08);
        border-radius: 999px;
        padding: 8px 14px;
        font-size: 24px;
      }}
      h1 {{
        margin: 20px 0 0;
        font-size: 70px;
        line-height: 1.08;
        letter-spacing: -1px;
      }}
      p {{
        margin: 28px 0;
        font-size: 40px;
        line-height: 1.35;
        color: #334e68;
      }}
      .footer {{
        margin-top: 30px;
        font-size: 30px;
        color: #486581;
      }}
      .meta {{
        font-size: 26px;
        color: #627d98;
      }}
    </style>
  </head>
  <body>
    <div class=\"frame\">
      <div>
        <div class=\"chip\">Slide {order}</div>
        <div class=\"meta\">{safe_carousel_title}</div>
        <h1>{safe_title}</h1>
        <p>{safe_body}</p>
      </div>
      <div class=\"footer\">{safe_footer}</div>
    </div>
  </body>
</html>
"""
