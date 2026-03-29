FROM python:3.11-slim

# Install `uv` for future installing dependices instead of `pip`
RUN pip install --no-cache-dir uv

WORKDIR /calnio

COPY pyproject.toml uv.lock ./

RUN uv sync --frozen

COPY . .

EXPOSE 8080

CMD ["uv", "run", "uvicorn", "server.main:app", "--app-dir", "/calnio", "--host", "0.0.0.0", "--port", "8080", "--reload", "--reload-dir", "/calnio/server"]
