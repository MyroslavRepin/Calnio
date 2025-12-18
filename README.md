# Calnio

**Version:** 1.16.1  
**License:** See [LICENSE](LICENSE)

## About the Project

Calnio is a professional service for **bidirectional synchronization** of tasks and events between **Notion** and **Apple Calendar** (via CalDAV protocol). The platform enables seamless integration between these productivity tools, ensuring your tasks and events stay synchronized across both platforms in real-time.

### Technology Stack

- **Backend Framework:** FastAPI + Litestar for high-performance async API
- **ORM:** SQLAlchemy 2.0 with async support
- **Database:** PostgreSQL with asyncpg driver
- **Task Scheduling:** APScheduler for background sync operations
- **CalDAV Integration:** aiocaldav for async Apple Calendar sync
- **Notion Integration:** Official notion_client SDK
- **Monitoring:** Prometheus metrics and custom logging with Loguru
- **Containerization:** Docker & Docker Compose
- **Port Forwarding:** ngrok for remote access

### Key Features

**Bidirectional Sync:** Changes in Notion reflect in Apple Calendar and vice versa
**Real-time Updates:** Webhook-based instant synchronization from Notion
**Scheduled Sync:** Background tasks using APScheduler for periodic updates
**Conflict Resolution:** Smart conflict handling based on last-modified timestamps
**Multi-User Support:** Isolated task synchronization per user
**Email Notifications:** Waitlist management and user notifications via SMTP
**API Documentation:** Interactive OpenAPI/Scalar documentation
**Metrics & Monitoring:** Prometheus integration for observability

### Architecture Overview

```
┌─────────────┐         ┌──────────────┐         ┌─────────────┐
│   Notion    │◄───────►│    Calnio    │◄───────►│    CalDAV   │
│     API     │ Webhooks│   Backend    │  Sync   │   (Apple)   │
└─────────────┘         └──────────────┘         └─────────────┘
                              │
                              ▼
                        ┌──────────────┐
                        │  PostgreSQL  │
                        │   Database   │
                        └──────────────┘
```

- **Notion Webhooks** trigger immediate sync when tasks are updated
- **Background Scheduler** performs periodic CalDAV → Database → Notion sync
- **Database** serves as the source of truth for conflict resolution
- **ngrok** exposes local development environment for webhook testing

---

# Getting Started

## Prerequisites

- Python 3.11+
- PostgreSQL 12+
- Docker & Docker Compose (optional but recommended)
- ngrok account (for webhook integrations)

## Environment Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/Calnio.git
   cd Calnio
   ```

2. **Create a `.env` file** in the project root with the following variables:
   ```env
   # Database
   DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/calnio
   
   # Notion API
   NOTION_API_KEY=your_notion_integration_token
   
   # CalDAV (Apple Calendar)
   CALDAV_URL=https://caldav.icloud.com
   CALDAV_USERNAME=your_apple_id
   CALDAV_PASSWORD=your_app_specific_password
   
   # Email (Optional)
   EMAIL_HOST=smtp.gmail.com
   EMAIL_PORT=587
   EMAIL_USER=your_email@gmail.com
   EMAIL_PASSWORD=your_app_password
   
   # ngrok
   NGROK_AUTHTOKEN=your_ngrok_token
   ```

## Running the Project

### Option 1: Docker Compose (Recommended)

**Start all services:**
```bash
docker-compose up -d
```

This will start:
- Calnio backend (port 8000)
- ngrok tunnel (exposes backend to internet)

**View logs:**
```bash
docker-compose logs -f calnio
```

**Stop services:**
```bash
docker-compose down
```

### Option 2: Local Development

**macOS & Linux:**

```bash
# Make the startup script executable
chmod +x START_SERVER.sh

# Start the server
./START_SERVER.sh

# Reset virtual environment and reinstall dependencies
./START_SERVER.sh --reset
```

**Windows:**

Double-click `START_SERVER.bat` or run from Command Prompt:
```cmd
START_SERVER.bat

REM Reset and reinstall
START_SERVER.bat --reset
```

### Option 3: Manual Start

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py upgrade

# Start the server
uvicorn server.app.main:app --reload --port 8000
```

## Access the Application

- **API:** http://localhost:8000
- **API Documentation:** http://localhost:8000/schema
- **Health Check:** http://localhost:8000/health
- **Metrics:** http://localhost:8000/metrics
- **Public URL (via ngrok):** https://calnio.ngrok.dev

## Development Utilities

**Count lines of code:**
```bash
cloc --include-lang=Python,BourneShell,Markdown,HTML,CSS,Text \
     --exclude-dir=.venv,.git,node_modules,tests,docs,vendor .
```

**Run with HTTPS (local development):**
```bash
uvicorn server.app.main:app --reload \
  --ssl-certfile localhost+2.pem \
  --ssl-keyfile localhost+2-key.pem
```

**Run tests:**
```bash
pytest tests/
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
**This will delete all data!**
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

# Remote Access with ngrok

Calnio uses [ngrok](https://ngrok.com/) to expose the local backend to the internet, enabling webhook integrations with Notion and remote access to the API.

## Current Configuration

- **Domain:** `calnio.ngrok.dev`
- **Version:** ngrok v3
- **Local Port:** 8000
- **Protocol:** HTTP/HTTPS

## Setup Instructions

### 1. Install ngrok

**macOS (Homebrew):**
```bash
brew install ngrok/ngrok/ngrok
```

**Manual Installation:**
- Download from https://ngrok.com/download
- Unzip and move the binary to your PATH (e.g., `/usr/local/bin`)

### 2. Authenticate ngrok

Sign up at [ngrok.com](https://ngrok.com) and add your authentication token:

```bash
ngrok config add-authtoken <YOUR_AUTH_TOKEN>
```

### 3. Start ngrok Tunnel

The project includes a pre-configured `ngrok.yml` file. Start the tunnel with:

```bash
ngrok start --all --config ngrok.yml
```

Or use Docker Compose (recommended):

```bash
docker-compose up ngrok
```

### 4. Access Your Backend

Once ngrok is running, your local backend (port 8000) will be accessible at:

- **Public URL:** `https://calnio.ngrok.dev`
- **Local URL:** `http://localhost:8000`

### Configuration File

The `ngrok.yml` configuration:

```yaml
version: 3
agent:
  authtoken: <YOUR_TOKEN>
endpoints:
  - name: calnio
    url: calnio.ngrok.dev
    upstream:
      url: calnio:8000
```

## Monitoring

- View tunnel status: `http://localhost:4040` (ngrok web interface)
- Check active connections and request/response logs in real-time
- Monitor webhook payloads from Notion

---

# Project Structure

```
Calnio/
├── server/
│   ├── app/
│   │   ├── core/           # Core application configuration
│   │   ├── routes/         # API endpoints
│   │   └── main.py         # FastAPI application entry point
│   ├── db/
│   │   ├── models/         # SQLAlchemy models
│   │   └── repositories/   # Database access layer
│   ├── services/
│   │   ├── sync/           # Synchronization logic
│   │   ├── caldav/         # CalDAV integration
│   │   └── scheduler/      # Background task scheduler
│   ├── integrations/       # Third-party API integrations
│   ├── middleware/         # Custom middleware
│   └── utils/              # Utility functions
├── frontend/
│   ├── templates/          # Jinja2 HTML templates
│   └── static/            # CSS, JS, fonts, assets
├── logs/                   # Application logs (auto-rotated)
├── tests/                  # Test suites
├── scripts/                # Utility scripts
├── docker-compose.yml      # Docker orchestration
├── requirements.txt        # Python dependencies
├── manage.py              # Database migration manager
└── README.md              # This file
```

---

# Deployment

## Production Deployment

For production deployment, ensure:

1. **Environment Variables** are properly configured
2. **Database** is backed up regularly
3. **HTTPS** is enabled (use proper SSL certificates, not localhost certs)
4. **Monitoring** is set up (Prometheus, Grafana, Loki)
5. **Rate Limiting** is configured for API endpoints
6. **Secrets** are stored securely (not in code or version control)

## Docker Production Build

```bash
docker build -t calnio:latest .
docker-compose -f docker-compose.yml up -d
```

## Health Checks

The application includes health check endpoints:

- `/health` - Basic health check
- `/metrics` - Prometheus metrics
- `/version` - Current application version

---

# Troubleshooting

### Common Issues

**1. Database Connection Errors**
```bash
# Check PostgreSQL is running
psql -U postgres -c "SELECT version();"

# Verify DATABASE_URL in .env
echo $DATABASE_URL
```

**2. Migration Conflicts**
```bash
# Reset migrations (development only - will delete data!)
python manage.py downgrade base
python manage.py upgrade head
```

**3. CalDAV Authentication Failed**
- Ensure you're using an **App-Specific Password** for Apple ID
- Generate one at: https://appleid.apple.com/account/manage
- Verify CALDAV_URL, CALDAV_USERNAME, CALDAV_PASSWORD in `.env`

**4. Notion Webhook Not Working**
- Check ngrok is running and accessible
- Verify webhook URL in Notion integration settings
- Review webhook logs at `http://localhost:4040`

**5. Port Already in Use**
```bash
# Find and kill process using port 8000
lsof -ti:8000 | xargs kill -9
```

---

# Roadmap & Known Issues

See [CHANGELOG.md](CHANGELOG.md) for version history and recent updates.

### Upcoming Features

- [ ] Google Calendar integration
- [ ] Microsoft Outlook/Calendar sync
- [ ] Task priorities and tags synchronization
- [ ] Recurring event support improvements
- [ ] Mobile app (iOS/Android)
- [ ] Advanced filtering and selective sync
- [ ] Two-factor authentication (2FA)

### Known Issues

- Timezone handling for all-day events may need refinement
- Large calendars (1000+ events) may experience slower initial sync
- Some CalDAV servers have rate limiting (handled with retry logic)

For current bugs and feature requests, please check the [Issues](https://github.com/yourusername/Calnio/issues) page.

---

# Contributing

We welcome contributions! Please follow these guidelines:

1. **Fork** the repository
2. **Create a feature branch:** `git checkout -b feature/your-feature-name`
3. **Follow coding standards:**
   - Use type hints for Python functions
   - Follow PEP 8 style guide
   - Write docstrings for functions and classes
   - Add tests for new features
4. **Commit your changes:** `git commit -am 'Add new feature'`
5. **Push to your branch:** `git push origin feature/your-feature-name`
6. **Create a Pull Request**

### Development Setup

```bash
# Install development dependencies
pip install -r requirements.txt

# Install pre-commit hooks
python scripts/setup_precommit.py

# Run tests
pytest tests/

# Check code style
flake8 server/
```

---

# License

This project is licensed under the terms specified in the [LICENSE](LICENSE) file.

---

# Contact & Support

- **Issues:** Report bugs or request features via [GitHub Issues](https://github.com/yourusername/Calnio/issues)
- **Discussions:** Join discussions on [GitHub Discussions](https://github.com/yourusername/Calnio/discussions)
- **Email:** For private inquiries, contact the maintainers

---

# Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/)
- CalDAV integration powered by [aiocaldav](https://github.com/python-caldav/caldav)
- Notion integration using [notion-sdk-py](https://github.com/ramnes/notion-sdk-py)
- Monitoring with [Prometheus](https://prometheus.io/)

---

**Current Version:** 1.16.1  
**Last Updated:** November 2025  
**Maintained by:** Myroslav Repin and contributors
