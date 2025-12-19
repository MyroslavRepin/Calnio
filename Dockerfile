FROM python:3.11-slim

# Install `uv` for future installing dependices instead of `pip`
RUN pip install --no-cache-dir uv

WORKDIR /calnio

COPY pyproject.toml uv.lock ./

RUN uv sync --frozen

COPY . .

EXPOSE 8000

#CMD [
#    "uvicorn",
#    "server.app.main:app",
#    "--host", "0.0.0.0",
#    "--port", "8000",
#    "--log-level",
#    "debug",
#    "--reload",
#    "--timeout-keep-alive",
#    "60"
#] Old hardcoded command

CMD ["uv", "run", "uvicorn", "server.app.main:app", "--app-dir", "/calnio", "--host", "0.0.0.0", "--port", "8000"]
