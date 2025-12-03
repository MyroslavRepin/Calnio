import subprocess

subprocess.run(
    ['uvicorn', 'server.app.main:app', '--reload'],
)