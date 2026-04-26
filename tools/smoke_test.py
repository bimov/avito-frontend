from __future__ import annotations

from io import BytesIO
from pathlib import Path
import sys

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ocr_app.main import app


def main() -> int:
    image = Image.new("RGB", (1200, 320), "white")
    drawer = ImageDraw.Draw(image)
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 110)
    drawer.text((70, 90), "МОЛОКО 42", fill="black", font=font)

    buffer = BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)

    client = app.test_client()
    response = client.post(
        "/",
        data={
            "threshold": "0.10",
            "sort": "confidence-desc",
            "image": (buffer, "sample.png"),
        },
        content_type="multipart/form-data",
    )
    text = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "МОЛОКО" in text
    assert "data:image/png;base64," in text

    print("Container smoke test passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
