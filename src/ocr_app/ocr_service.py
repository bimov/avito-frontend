from __future__ import annotations

from base64 import b64encode
from io import BytesIO
from pathlib import Path
import subprocess
import tempfile

from PIL import Image, ImageDraw, ImageOps

from ocr_app.ocr_utils import OCRWord, parse_tsv, select_words


class OCRProcessingError(Exception):
    def __init__(self, title: str, message: str) -> None:
        super().__init__(message)
        self.title = title
        self.message = message


def run_ocr_pipeline(image_path: Path, threshold: float, sort_option: str) -> tuple[str, list[OCRWord]]:
    normalized_path = normalize_image(image_path)

    try:
        tsv_output = run_tesseract(normalized_path)
        words = parse_tsv(tsv_output)
        filtered_words = select_words(words, threshold=threshold, sort_option=sort_option)
        preview = render_preview(normalized_path, filtered_words)
        return preview, filtered_words
    finally:
        if normalized_path.exists():
            normalized_path.unlink()


def normalize_image(source_path: Path) -> Path:
    try:
        with Image.open(source_path) as image:
            normalized = ImageOps.exif_transpose(image).convert("RGB")
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
            temp_path = Path(temp_file.name)
            temp_file.close()
            normalized.save(temp_path, format="PNG")
            return temp_path
    except OSError as error:
        raise OCRProcessingError("InvalidImage", "Не удалось открыть изображение.") from error


def run_tesseract(image_path: Path) -> str:
    command = [
        "tesseract",
        str(image_path),
        "stdout",
        "-l",
        "rus+eng",
        "--psm",
        "6",
        "tsv",
    ]

    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError as error:
        raise OCRProcessingError("TesseractMissing", "Tesseract не найден в контейнере.") from error

    if completed.returncode != 0:
        details = completed.stderr.strip() or "Не удалось получить результат OCR."
        raise OCRProcessingError("OCRFailed", details)

    return completed.stdout


def render_preview(image_path: Path, words: list[OCRWord]) -> str:
    with Image.open(image_path) as image:
        canvas = ImageOps.exif_transpose(image).convert("RGBA")
        canvas.thumbnail((1400, 1400))
        draw = ImageDraw.Draw(canvas, "RGBA")

        scale_x = canvas.width / image.width
        scale_y = canvas.height / image.height

        for word in words:
            polygon = [
                (int(x * scale_x), int(y * scale_y))
                for x, y in word.polygon
            ]
            outline, fill = pick_colors(word.confidence)
            draw.polygon(polygon, outline=outline, fill=fill, width=3)

        buffer = BytesIO()
        canvas.save(buffer, format="PNG")
        encoded = b64encode(buffer.getvalue()).decode("ascii")
        return f"data:image/png;base64,{encoded}"


def pick_colors(confidence: float) -> tuple[tuple[int, int, int, int], tuple[int, int, int, int]]:
    if confidence >= 0.95:
        return (23, 111, 99, 255), (23, 111, 99, 56)

    if confidence >= 0.85:
        return (203, 91, 53, 255), (203, 91, 53, 52)

    return (181, 59, 50, 255), (181, 59, 50, 44)
