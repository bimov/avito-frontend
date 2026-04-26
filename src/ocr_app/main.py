from __future__ import annotations

from pathlib import Path
import tempfile

from flask import Flask, render_template, request

from ocr_app.ocr_service import OCRProcessingError, run_ocr_pipeline
from ocr_app.ocr_utils import (
    is_allowed_filename,
    normalize_sort_option,
    normalize_threshold,
)


BASE_DIR = Path(__file__).resolve().parent
app = Flask(__name__, template_folder=str(BASE_DIR / "templates"))


def build_context() -> dict[str, object]:
    return {
        "error_title": None,
        "error_message": None,
        "result_image": None,
        "words": [],
        "status_message": None,
        "threshold": "0.85",
        "sort_option": "confidence-desc",
        "show_heading": True,
    }


def finalize_context(context: dict[str, object]) -> dict[str, object]:
    context["show_heading"] = not any(
        (
            context["error_title"],
            context["result_image"],
            context["words"],
            context["status_message"],
        )
    )
    return context


@app.route("/", methods=["GET", "POST"])
def index() -> str:
    context = build_context()

    if request.method == "POST":
        threshold = normalize_threshold(request.form.get("threshold"))
        sort_option = normalize_sort_option(request.form.get("sort"))

        context["threshold"] = f"{threshold:.2f}"
        context["sort_option"] = sort_option

        upload = request.files.get("image")
        if upload is None or not upload.filename:
            context["error_title"] = "FileRequired"
            context["error_message"] = "Выберите изображение перед отправкой формы."
            return render_template("index.html", **finalize_context(context))

        if not is_allowed_filename(upload.filename):
            context["error_title"] = "UnsupportedImage"
            context["error_message"] = "Поддерживаются файлы JPG, JPEG, PNG и WEBP."
            return render_template("index.html", **finalize_context(context))

        suffix = Path(upload.filename).suffix.lower() or ".png"
        temp_path: Path | None = None

        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
                upload.save(temp_file)
                temp_path = Path(temp_file.name)

            result_image, words = run_ocr_pipeline(
                image_path=temp_path,
                threshold=threshold,
                sort_option=sort_option,
            )
            context["result_image"] = result_image
            context["words"] = words

            if words:
                context["status_message"] = None
            else:
                context["status_message"] = "Слова с таким порогом не найдены."
        except OCRProcessingError as error:
            context["error_title"] = error.title
            context["error_message"] = error.message
        finally:
            if temp_path is not None and temp_path.exists():
                temp_path.unlink()

    return render_template("index.html", **finalize_context(context))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=False)
