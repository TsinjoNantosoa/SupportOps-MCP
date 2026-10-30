FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app
COPY pyproject.toml README.md LICENSE ./
COPY src ./src
COPY knowledge ./knowledge
RUN python -m pip install --no-cache-dir .

RUN useradd --create-home --uid 10001 supportops \
    && mkdir -p /data \
    && chown -R supportops:supportops /app /data
USER supportops

CMD ["supportops-ticketing"]
