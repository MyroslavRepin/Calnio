FROM python:3.11-slim-buster

WORKDIR /calnio

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

#ENTRYPOINT [
#    "uvicorn",
#    "server.app.main:app",
#    "--host", "0.0.0.0",
#    "--port", "8000",
#    "--log-level",
#    "info",
#    "--reload",
#    "--timeout-keep-alive",
#    "60"
#    ]
CMD ["uvicorn", "server.app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]