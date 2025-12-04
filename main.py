import os
import subprocess

# Read host/port/reload from environment with sensible defaults for container
HOST = os.getenv("HOST", "0.0.0.0")
PORT = os.getenv("PORT", "8000")
RELOAD = os.getenv("RELOAD", "False").lower() == "true"

args = [
    "uvicorn",
    "server.app.main:app",
    "--host",
    HOST,
    "--port",
    PORT,
]

# Enable reload only if explicitly set (useful for local dev, not in container)
if RELOAD:
    args.append("--reload")

subprocess.run(args, check=True)
