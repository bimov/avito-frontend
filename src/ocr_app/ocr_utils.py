from __future__ import annotations

from dataclasses import dataclass
import csv
import io


ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
SORT_OPTIONS = {"confidence-desc", "confidence-asc", "word-asc"}
DEFAULT_THRESHOLD = 0.85
DEFAULT_SORT_OPTION = "confidence-desc"


@dataclass(frozen=True)
class OCRWord:
    text: str
    confidence: float
    left: int
    top: int
    width: int
    height: int

    @property
    def fragment(self) -> str:
        text = self.text.strip()
        if len(text) <= 4:
            return text.upper()
        return f"{text[:4].upper()}..."

    @property
    def polygon(self) -> list[tuple[int, int]]:
        right = self.left + self.width
        bottom = self.top + self.height
        return [
            (self.left, self.top),
            (right, self.top),
            (right, bottom),
            (self.left, bottom),
        ]


def is_allowed_filename(filename: str) -> bool:
    if "." not in filename:
        return False
    return filename.lower().rsplit(".", 1)[1] in {"jpg", "jpeg", "png", "webp"}


def normalize_threshold(raw_value: str | None) -> float:
    if raw_value is None:
        return DEFAULT_THRESHOLD

    try:
        value = float(raw_value)
    except ValueError:
        return DEFAULT_THRESHOLD

    return min(1.0, max(0.0, value))


def normalize_sort_option(raw_value: str | None) -> str:
    if raw_value in SORT_OPTIONS:
        return raw_value
    return DEFAULT_SORT_OPTION


def parse_tsv(tsv_text: str) -> list[OCRWord]:
    rows: list[OCRWord] = []
    reader = csv.DictReader(io.StringIO(tsv_text), delimiter="\t")

    for row in reader:
        if row.get("level") != "5":
            continue

        text = (row.get("text") or "").strip()
        if not text:
            continue

        try:
            confidence = float(row.get("conf", "-1"))
            left = int(row.get("left", "0"))
            top = int(row.get("top", "0"))
            width = int(row.get("width", "0"))
            height = int(row.get("height", "0"))
        except ValueError:
            continue

        if confidence < 0:
            continue

        rows.append(
            OCRWord(
                text=text,
                confidence=confidence / 100,
                left=left,
                top=top,
                width=width,
                height=height,
            )
        )

    return rows


def select_words(words: list[OCRWord], threshold: float, sort_option: str) -> list[OCRWord]:
    filtered = [word for word in words if word.confidence >= threshold]

    if sort_option == "confidence-asc":
        return sorted(filtered, key=lambda word: (word.confidence, word.text.lower()))

    if sort_option == "word-asc":
        return sorted(filtered, key=lambda word: (word.text.lower(), -word.confidence))

    return sorted(filtered, key=lambda word: (-word.confidence, word.text.lower()))
