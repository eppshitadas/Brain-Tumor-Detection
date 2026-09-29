# Used for Docker-based hosts (Hugging Face Spaces, Render, Railway, Fly.io).
# Build context: the repository root.
FROM python:3.11-slim

WORKDIR /app
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ ./backend
COPY model/ ./model

ENV PORT=7860
EXPOSE 7860
WORKDIR /app/backend
CMD ["gunicorn", "--bind", "0.0.0.0:7860", "--timeout", "120", "--workers", "1", "app:app"]
