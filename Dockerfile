FROM node:23-alpine3.20

WORKDIR /app

# Install daisyui
COPY package.json package.json
COPY package-lock.json package-lock.json
RUN npm install

# Setup python
FROM python:3.12-alpine AS linux-amd64
WORKDIR /app
RUN apk add --no-cache curl gcompat build-base
RUN curl https://github.com/tailwindlabs/tailwindcss/releases/download/v4.0.6/tailwindcss-linux-x64-musl -L -o /bin/tailwindcss

FROM python:3.12-alpine AS linux-arm64
WORKDIR /app
RUN apk add --no-cache curl gcompat build-base
RUN curl https://github.com/tailwindlabs/tailwindcss/releases/download/v4.0.6/tailwindcss-linux-arm64-musl -L -o /bin/tailwindcss

FROM ${TARGETOS}-${TARGETARCH}${TARGETVARIANT}
RUN chmod +x /bin/tailwindcss

COPY --from=0 /app/node_modules/ node_modules/
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

COPY uv.lock pyproject.toml /app/
RUN uv sync --frozen --no-cache

# Install AudiobookBay scraper dependencies
COPY audibookbay-scraper/requirements.txt /app/audibookbay-scraper-requirements.txt
RUN uv pip install -r /app/audibookbay-scraper-requirements.txt

COPY alembic/ alembic/
COPY alembic.ini alembic.ini
COPY static/ static/
COPY templates/ templates/
COPY app/ app/

# Copy the AudiobookBay scraper code
COPY audibookbay-scraper/ /app/audibookbay-scraper/

# Create services directory if it doesn't exist (in case app/services doesn't exist in the COPY above)
RUN mkdir -p /app/app/services
# Create __init__.py in services directory if it doesn't exist
RUN [ -f /app/app/services/__init__.py ] || echo '"""Services package for AudioBookRequest application."""' > /app/app/services/__init__.py

RUN /bin/tailwindcss -i static/tw.css -o static/globals.css -m
# Fetch all the required js files
RUN uv run python /app/app/util/fetch_js.py

ENV ABR_APP__PORT=8000
ARG VERSION
ENV ABR_APP__VERSION=$VERSION

# Enable AudiobookBay router in main.py
RUN sed -i 's/# from app.routers import audiobookbay/from app.routers import audiobookbay/g' /app/app/main.py && \
    sed -i 's/# app.include_router(audiobookbay.router)/app.include_router(audiobookbay.router)/g' /app/app/main.py

# Use JSON format for CMD to prevent issues with OS signals
CMD ["/bin/sh", "-c", "/app/.venv/bin/alembic upgrade heads && /app/.venv/bin/fastapi run --port $ABR_APP__PORT"]

