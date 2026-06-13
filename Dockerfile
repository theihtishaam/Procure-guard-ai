FROM python:3.12-slim

WORKDIR /app

ENV HOST=0.0.0.0
ENV PORT=8765
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY pyproject.toml uv.lock ./
RUN pip install --no-cache-dir uv && uv sync --frozen

COPY . .

EXPOSE 8765

CMD ["uv", "run", "python", "-m", "app.main"]
