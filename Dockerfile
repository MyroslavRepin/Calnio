FROM python:3.13-slim

WORKDIR /calnio

# Системные зависимости для psycopg2-binary
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Создаем изолированную среду venv для контейнера
ENV VIRTUAL_ENV=/opt/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
RUN python -m venv "$VIRTUAL_ENV" && pip install --upgrade pip uv

# Копируем манифесты зависимостей первыми
COPY pyproject.toml uv.lock ./

# Синхронизируем зависимости (замороженные, если есть lock-файл)
RUN uv sync --frozen

# Копируем проект
COPY . .

EXPOSE 8000

# Запускаем через uv, используя venv
CMD ["uv", "run", "main.py"]
