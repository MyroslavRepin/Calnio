import subprocess

subprocess.run(
    ['uv', 'run', 'uvicorn', 'server.app.main:app', '--reload'],
    cwd='server'
)

# ! This anti-pattern