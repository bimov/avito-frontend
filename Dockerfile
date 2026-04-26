FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/workspace/src

WORKDIR /workspace

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        tesseract-ocr \
        tesseract-ocr-eng \
        tesseract-ocr-rus \
    && rm -rf /var/lib/apt/lists/*

COPY src/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY src ./src
COPY tools ./tools

EXPOSE 8000

CMD ["python", "-m", "ocr_app.main"]
