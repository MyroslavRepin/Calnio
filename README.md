# Calnio

## About the Project

Calnio is a service for **two-way synchronization** of tasks and events between **Notion** and **Apple Calendar**. The project uses:

- **FastAPI** for building the backend API,
- **SQLAlchemy** as the ORM for database interactions,
- **PostgreSQL** as the main database,
- **Notion API** to access and modify Notion data,
- **CalDAV** protocol for integrating with Apple Calendar.

The goal is to provide a reliable and easy-to-use tool for automatic syncing between these two popular platforms.

---

# Running the Project

To start the backend server, use the following command depending on your operating system.

**Make sure you're in the root of the `Calnio/` project directory before running these commands.**

---

## Environment Variables

The following environment variables can be configured:

| Variable | Default | Description |
|----------|---------|-------------|
| `HOST` | `0.0.0.0` | Server bind address |
| `PORT` | `8000` | Server port |
| `RELOAD` | `False` | Enable hot-reload (set to `true` for development) |
| `DEFAULT_SYNC_INTERVAL_SECONDS` | - | Default sync interval for CalDav synchronization |

---

## macOS & Linux

**Start normally:**

```bash
chmod +x START_SERVER.sh
./START_SERVER.sh
```

**Reset .venv and reinstall dependencies:**

```bash
./START_SERVER.sh --reset
```

## Windows

**Start normally:**

Double-click **START_SERVER.bat**
or run from Command Prompt:

```cmd
START_SERVER.bat
```

**Reset .venv and reinstall dependencies:**

```cmd
START_SERVER.bat --reset
```

## Docker

The project uses `uv` for dependency management. To run with Docker:

```bash
docker-compose up --build
```

The Docker container uses `main.py` as the entry point and respects `HOST`, `PORT`, and `RELOAD` environment variables.

## Utils

**Check how many lines of code writed**

```cmd
cloc --include-lang=Python,BourneShell,Markdown,HTML,CSS,Text --exclude-dir=.venv,.git,node_modules,tests,docs,vendor .
```

**To run in HTTPS**

```
  --ssl-certfile localhost+2.pem \
  --ssl-keyfile localhost+2-key.pem
```

---

# Database Management with Alembic

This project uses **Alembic** for database migrations, which allows you to safely add new columns, modify existing tables, and track database schema changes without losing data.

## Quick Start

### 1. Apply Current Migrations
When you first set up the project or pull changes that include new migrations:

```bash
python manage.py upgrade
```

### 2. Create a New Migration
When you modify your models (add/remove columns, tables, etc.):

```bash
python manage.py migrate "Description of your changes"
```

### 3. Apply New Migration
After creating a migration, apply it to the database:

```bash
python manage.py upgrade
```

## Common Alembic Commands

### Using manage.py (Recommended)

```bash
# Check database connection
python manage.py check

# Generate a new migration after model changes
python manage.py migrate "Add new columns to users table"

# Apply all pending migrations
python manage.py upgrade

# Rollback one migration
python manage.py downgrade

# Rollback to specific migration
python manage.py downgrade <revision_id>
```

### Direct Alembic Commands

```bash
# Show current migration status
alembic current

# Show migration history
alembic history

# Generate migration with custom message
alembic revision --autogenerate -m "Your migration message"

# Upgrade to latest migration
alembic upgrade head

# Downgrade by one revision
alembic downgrade -1

# Upgrade/downgrade to specific revision
alembic upgrade <revision_id>
alembic downgrade <revision_id>
```

## Workflow for Model Changes

1. **Modify your models** in `backend/app/models/`
2. **Generate migration**: `python manage.py migrate "Description"`
3. **Review the migration** in `alembic/versions/` directory
4. **Apply migration**: `python manage.py upgrade`
5. **Commit both model changes and migration files** to git

## Important Notes

- **Always review generated migrations** before applying them
- **Never edit applied migrations** - create a new one instead
- **Keep migration files in version control**
- **Test migrations on development database first**
- **Backup production database before applying migrations**

## Troubleshooting

### Migration Conflicts
If you have merge conflicts in migrations:
```bash
# Remove conflicting migration file
rm alembic/versions/conflicting_file.py

# Generate new migration
python manage.py migrate "Merged changes"
```

### Reset Database (Development Only)
⚠️ **This will delete all data!**
```bash
python server/app/db/recreate_tables.py
```

### Manual Migration Creation
```bash
# Create empty migration file
alembic revision -m "Custom migration"
# Then edit the generated file manually
```

---

# Exposing the Backend with ngrok

To make your local backend accessible over the internet, you can use [ngrok](https://ngrok.com/).

## Step-by-step ngrok setup

1. **Install ngrok**
   - Download from https://ngrok.com/download
   - Unzip and move the binary to your PATH (e.g., `/usr/local/bin`)
   - Or install via Homebrew:
     ```bash
     brew install ngrok/ngrok/ngrok
     ```

2. **Authenticate ngrok**
   - Sign up at ngrok.com and get your auth token.
   - Run:
     ```bash
     ngrok config add-authtoken <YOUR_AUTH_TOKEN>
     ```

3. **Expose your local backend**
   - Run:
     ```bash
     ngrok http 8000
     ```
   - This will expose your local server (running on port 8000) to the internet.

4. **Access your backend remotely**
   - Use your ngrok domain:
     - **Domain:** `splendid-frog-caring.ngrok-free.app`
     - **Tunnel ID:** `rd_30yfenO1ffkaWZqL6swTVgCDvPc`
     - **Region:** Global
     - **Created:** Aug 7, 2025

5. **Check tunnel status and endpoints**
   - Visit the ngrok dashboard or use the CLI to view active tunnels and endpoints.
   - Example endpoint: `https://splendid-frog-caring.ngrok-free.app`

## Quick Start with Your ngrok Token and Domain

1. **Authenticate ngrok with your token**
   ```bash
   ngrok config add-authtoken 30yfUeunkQtrivsTQb1ZubXStt3_ULkbxYtBYchAUnG9bqtN
   ```

2. **Expose your backend with your custom domain**
   ```bash
   ngrok http 8000 --hostname=splendid-frog-caring.ngrok-free.app
   ```
   This will make your backend available at: https://splendid-frog-caring.ngrok-free.app
