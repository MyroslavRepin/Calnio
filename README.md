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
python backend/app/db/recreate_tables.py
```

### Manual Migration Creation
```bash
# Create empty migration file
alembic revision -m "Custom migration"
# Then edit the generated file manually
```

# Scheduling and Background Synchronization

Calnio includes an automatic background synchronization system that periodically syncs your tasks with Notion. This system uses APScheduler to manage scheduled jobs and allows users to configure their synchronization intervals.

## Scheduling Features

### Configurable Sync Intervals
- Users can set their preferred synchronization interval between 5 minutes and 24 hours (1440 minutes)
- Default interval is 30 minutes
- Each user has their own independent sync schedule
- Sync intervals can be updated through the dashboard settings

### Background Job Management
- Automatic initialization of sync jobs when users connect their Notion integration
- Jobs are automatically updated when users change their sync interval
- Proper cleanup when the application shuts down
- Thread-safe job execution with async/await support

### User Interface
The dashboard includes a "Sync Interval" field where users can:
- View their current sync interval
- Update the interval (with validation)
- See helpful text about the allowed range (5 minutes to 24 hours)

## How It Works

1. **Application Startup**: The scheduler starts and initializes sync jobs for all existing users with Notion integrations
2. **User Configuration**: Users can modify their sync interval through the dashboard profile settings
3. **Automatic Syncing**: Background jobs run at each user's configured interval to sync their Notion pages
4. **Job Management**: The system automatically adds/removes/updates jobs based on user actions

## Technical Implementation

### Components
- **SyncScheduler**: Main scheduler service managing all background sync jobs
- **APScheduler**: Background scheduler library handling job execution
- **Database Migration**: Added `sync_interval` column to users table
- **User Interface**: Dashboard form with sync interval configuration

### Configuration
```python
# Default sync interval (30 minutes)
sync_interval: Mapped[int] = mapped_column(Integer, default=30)

# Validation range: 5 minutes to 24 hours
if sync_interval < 5 or sync_interval > 1440:
    sync_interval = 30  # Reset to default if invalid
```

### Job Execution
Each sync job:
1. Connects to the user's Notion workspace using their access token
2. Retrieves all accessible pages
3. Creates or updates tasks in the local database
4. Handles errors gracefully and logs important events

## Monitoring and Logs

The application logs important scheduling events:
- Scheduler startup/shutdown
- Job additions/removals/updates
- Sync job execution results
- Error handling and warnings

Check the application logs to monitor sync job activity and troubleshoot any issues.
