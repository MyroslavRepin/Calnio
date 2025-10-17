# Changelog

All notable changes to this project will be documented in this file.

This project follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)  
and adheres to [Semantic Versioning](https://semver.org/)

<!-- ## vX.Y.Z - YYYY-MM-DD

### Added

- Short description of new features or integrations
- New models, endpoints, or functionality

### Changed

- Updates or improvements to existing features
- Backend/frontend behavior changes

### Fixed

- Bugs or issues that were resolved
- Problems with redirects, tokens, or database

### Known Issue

- Anything still broken or limitations users should know -->
## 1.15.3 - 2025-10-17
Minor patches and fixes.

### Added

- Rewrote CalDAV integration class to use `asyncio.to_thread` and fixed an error when creating new events.
- Added an Alembic migration to create the new table introduced in recent commits.

### Changed

- Applied migrations and updated database schema accordingly.

### Fixed

- Miscellaneous minor patches and fixes across the codebase.

### Notes

- Version in `server/app/version.py` was intentionally not changed here.

## [Unreleased] - 2025-10-17
Minor patches and fixes.

### Added

- Rewrote CalDAV integration class to use `asyncio.to_thread` and fixed an error when creating new events.
- Added an Alembic migration to create the new table introduced in recent commits.

### Changed

- Applied migrations and updated database schema accordingly.

### Fixed

- Miscellaneous minor patches and fixes across the codebase.

### Notes

- Version in `server/app/version.py` was intentionally not changed here.


## v1.15.2 - 2025-10-08

### Changed

- Refactored Notion integration modules: migrated `notion_sync`, `notion_integrations` to the new `notion_syncing` package for improved structure and maintainability.
- Enhanced Notion task syncing logic to better coordinate Redis and database interactions.
- Improved `to_notion` serialization: properties now safely handle `None` values, reducing risk of invalid updates.
- Updated Postgres triggers to include `db_to_notion_sync` for seamless task updates from database changes.
- Optimized module imports and removed unused code for better performance and clarity.

### Fixed

- Improved webhook handling and task synchronization reliability between Notion and the local database.
- Fixed issues with task property serialization that could cause incomplete or incorrect Notion updates.
- Enhanced logging for debugging sync operations and database triggers.

## v1.15.1 - 2025-10-07

### Added

- **Full Async CalDAV ORM Layer**: Complete CalDAV integration with aiocaldav and icalendar
  - `CalDavORM` class with full CRUD operations (create, read, update, delete)
  - `CalDavEventData` Pydantic schema for type-safe event handling
  - `CalDavEventFilter` for advanced event filtering and search
  - `CalDavEventLocal` SQLAlchemy model for local event persistence
  - Support for recurring events with iCalendar RRULE
  - Event filtering by date range, keywords, status, and recurrence rules
  - Soft delete functionality with proper sync status tracking
  - Calendar listing and management
  - Remote and local event synchronization
- **iCalendar Integration**: Full support for .ics file generation and parsing
  - VEVENT creation with proper timezone handling
  - RRULE support for recurring events
  - Status management (needs-action, completed, cancelled)
  - Description and datetime field handling
- **Enhanced Database Models**: New CalDAV event persistence layer
  - `caldav_events` table with comprehensive event fields
  - User association and calendar identification
  - Remote URL tracking for reliable updates/deletes
  - Sync status management and conflict detection

### Changed

- **Professional Logging**: Removed all emojis from codebase for cleaner, professional appearance
  - Updated all script files (cleanup_duplicates.py, migrate_normalize_ids.py, setup_precommit.py)
  - Converted manage.py print statements to proper logger calls
  - Standardized logging across generate_tree.py and database utilities
  - Maintained proper log levels (info, warning, error) without emoji decorations
- **Improved Code Quality**: Enhanced type safety and static analysis compliance
  - Fixed PEP 604 union syntax compatibility
  - Resolved SQLAlchemy type hints for where clauses
  - Updated timezone handling to use `datetime.UTC` instead of deprecated `datetime.utcnow()`
  - Proper imports and schema exports for better IDE support

### Fixed

- **Import Resolution**: Fixed unresolved reference errors in CalDAV modules
  - Proper schema package exports in `__init__.py`
  - Direct module imports for better static analysis
- **Type Safety**: Resolved all static analyzer warnings
  - Explicit `__eq__` calls in SQLAlchemy where clauses
  - Union type annotations using `typing.Union`
  - Proper timezone-aware datetime defaults
- **ICS Parsing**: Fixed byte/string conversion issues in icalendar integration
  - Proper UTF-8 decoding of ICS data before parsing
  - Safe handling of malformed calendar data

### Technical Details

- **CalDAV ORM Usage Examples**:
```text
# Initialize ORM
orm = CalDavORM(client)

# Create event
event = CalDavEventData(
    title="Meeting",
    start=datetime(2025,10,7,15,0, tzinfo=UTC),
    end=datetime(2025,10,7,16,0, tzinfo=UTC),
    rrule={"FREQ":"DAILY", "COUNT":"5"}
)
uid = await orm.create_event(calendar, event)

# Get events with filters
events = await orm.get_events(
    calendar, 
    start=datetime.now(UTC),
    end=datetime.now(UTC) + timedelta(days=30),
    filters={"keywords": "meeting", "status": "needs-action"}
)
```

## v1.15.0 - 2025-10-06

### Added

- **Loguru Integration**: Replaced Python's standard logging with Loguru for unified, structured logging across the entire codebase
- **ID Normalization System**: Added `normalize_notion_id()` utility function to ensure all Notion page IDs are stored consistently without dashes
- **Enhanced Webhook Logging**: Comprehensive logging system for easy visual scanning of webhook events
  - 🔄 = Sync/processing started
  - 📝 = Event info
  - 📡 = API call
  - 📄 = Data received
  - 🔍 = Database lookup
  - ♻️ = Update operation
  - ➕ = Create operation
  - 🗑️ = Delete operation
  - ✅ = Success
  - ⚠️ = Warning
  - ❌ = Error
- **Database Cleanup Script**: Added `cleanup_duplicates.py` script to identify and remove duplicate tasks
- **ID Migration Script**: Added `migrate_normalize_ids.py` for normalizing existing database IDs

### Changed

- **Logging System Overhaul**: 
  - Removed all `print()` statements from server code
  - Replaced all `logging.*()` calls with Loguru `logger.*()` 
  - Unified log format with short timestamps (HH:mm:ss instead of full date)
  - Intercepted uvicorn logs to use Loguru format
- **Webhook Event Handling**: 
  - Now properly handles `page.created`, `page.properties_updated`, and `page.deleted` events
  - Fixed event type detection (was using `page.updated`, now uses correct `page.properties_updated`)
- **ID Storage Format**: All task IDs and notion_page_ids now stored without dashes for consistency
- **CRUD Operations Enhanced**:
  - `create_task()` now shows whether it's updating existing task or creating new one
  - Better logging in all CRUD operations with clear indicators
  - Simplified database queries (removed redundant user_id check when notion_page_id is unique)
- **Redis Client**: Replaced print statements with proper Loguru logging
- **OAuth Callback**: Enhanced logging throughout authentication flow

### Fixed

- **Critical: Duplicate Tasks Bug**: Fixed webhook sync creating duplicate tasks instead of updating existing ones
  - Root cause: Mismatch between IDs with dashes (old data) and without dashes (new normalization)
  - Solution: Normalized all existing IDs and ensured consistent format
- **Webhook Sync Issues**:
  - Fixed tasks not being found for deletion (ID format mismatch)
  - Fixed updates creating new tasks instead of modifying existing ones
  - Fixed `page.updated` events being ignored (now handles `page.properties_updated`)
- **Database Cleanup**: Removed 1 duplicate task from production database
- **Logging Configuration**: 
  - Removed duplicate logger configurations
  - Fixed InterceptHandler for proper uvicorn log interception
  - Cleaned up unused logging imports and functions
- **Error Handling**: Added proper exception logging with `exc_info=True` for full stack traces

### Improved

- **Developer Experience**:
  - Logs now clearly show whether tasks are being created or updated
  - Both raw and normalized page IDs logged for debugging
  - Step-by-step webhook processing visible in logs
  - Easier to trace sync flow with clear indicators
- **Code Quality**:
  - Removed deprecated `datetime.utcnow()` calls (now using `datetime.now(UTC)`)
  - Better type hints for CRUD functions
  - Consistent error messages across all modules
- **Database Integrity**:
  - Guaranteed no duplicates (notion_page_id unique constraint enforced)
  - All IDs normalized for consistent lookups
  - One notion_page_id = One task (always)

### Notes

- Migration required: Run `cleanup_duplicates.py` on existing databases to normalize IDs
- All logs now use consistent emoji system for visual scanning
- Webhook sync now properly handles all Notion event types
- No more duplicate tasks - database uniqueness enforced

## v1.14.1 - 2025-10-01

### Changed

- **Typo in project version fixed**: version updated from incorrect `1.92` to correct `1.14.1` according to semantic versioning
- **Major Project Structure Refactoring**: Reorganized backend directory structure for improved clarity and maintainability
- **Authentication System Consolidation**: Merged multiple authentication files (`login.py`, `logout.py`, `signup.py`) into a unified `auth.py` module
- **Directory Reorganization**: 
  - Moved database-related files from `backend/app/db/` to `backend/db/`
  - Relocated services from `backend/app/services/` to `backend/services/`
  - Moved integrations to `backend/integartions/` (OAuth and Notion clients)
  - Reorganized utilities into `backend/utils/` with security and Notion submodules
- **Enhanced JWT Configuration**: Improved authentication configuration and security utilities organization
- **File Renaming**: Updated file names for better consistency (e.g., `refresh.py` → `refresh_cookies.py`, `schedulor.py` → `scheduler_service.py`)
- **Import Path Updates**: Updated all import statements to reflect the new directory structure

### Fixed

- Version numbering corrected from '1.92' to '1.14.1' to properly reflect project evolution and changes made since v1.14.0

## v1.14.0 - 2025-09-30

### Fixed
- Redirects to /dashboard after canceling Notion OAuth (error=access_denied)

## v1.13.2 - 2025-09-30

### Fixed

- Login issue related to session_id and 72 bytes limit. Improved session handling to prevent duplicate errors.

## v1.13.1 - 2025-09-30

### Fixed

- Fixed and created new `async_get_db_cm` context manager for improved database session handling in APScheduler jobs.

## v1.13.0 - 2025-09-30

### Added

- Introduced a new scheduling system using AsyncIOScheduler to periodically synchronize Notion data for users.
- Added `schedulor.py` for job scheduling and lifecycle management (startup/shutdown hooks in `main.py`).
- Added `apscheduler_test.py` script for demonstrating and testing scheduled tasks.
- Created `notion_client.py` to encapsulate Notion client creation and usage.

### Changed

- Refactored Notion client instantiation to use the new helper from `notion_client.py` across the codebase.
- Improved database dependency management by refactoring `async_get_db` with `@asynccontextmanager` for cleaner resource handling.
- Updated project structure and documentation (`DIRECTORY_STRUCTURE.md`) to reflect new migration, service, and script files.
- Replaced a logging statement with a print statement in `notion_sync_background` for better visibility during background sync.

### Fixed

- Minor improvements and code cleanup for better maintainability.

## v1.91.0 - 2025-09-29

### Added

- Enhanced user authentication with authorization check in login flow
- Added centralized logging configuration in config.py
- Added end_date field to Notion tasks for better task management
- Added async connection check and table creation for database management
- Added Alembic migration commands for schema management
- Added directory tree generation script with Git pre-commit hook
- Added user information display on dashboard

### Changed

- Refactored project structure for better organization
- Renamed task_date to start_date in Notion tasks
- Unified background task execution into `notion_sync_background`
- Moved CRUD operations to services directory
- Refactored token handling and user authentication flow
- Updated Notion integration with improved page handling
- Streamlined task handling in API endpoints
- Enhanced database management with better async handling

### Fixed

- Fixed date type error in database operations
- Fixed logging setup by removing direct configuration from main.py
- Fixed task management with proper background processing
- Fixed Notion task synchronization issues

### Removed

- Removed direct logging configuration from main.py
- Removed deprecated database scripts

## v1.9.4 - 2025-09-18

### Added

- Added `background_tasks` module for async task processing

### Changed

- Refactored and moved task update, create, and delete functions to `background_tasks/notion_sync.py`
- Applied Alembic migrations

## v1.9.3 - 2025-08-20

### Changed

- Moving **CRUD** functions from **utils/** to **CRUD/**

## v1.9.0 - 2025-09-16

### Added

- Adds Function to add all tasks from database

## v1.8.0 - 2025-09-12

### Added

- New model: **UserNotionTask**
- Adding feature to add task from html form and save to db

## v1.7.0 - 2025-09-10

### Changed

- Now config of environments controls from **.env**

## v1.6.2 - 2025-09-9

### Changed

- Now if user is logged in he will be redirected to dashboard

## v1.4.1 - 2025-08-07

### Fixed

- Need to open in web as **localhost** not as **0.0.0.0**

---

## v1.4.0 - 2025-08-07

### Added

- Adding Notion integrations to db
- New model: **UserNotionIntegration**

## v1.2.1 - 2025-08-05

### Known Issue

- Cross-Site redirect erases cookies

---

## v1.30 - 2025-08-05

### Added

- Updating password functional

## v1.2.1 - 2025-08-05

### Fixed

- Success box after **updating profile** can disapear after **5 sec**

---

## v1.2.0 - 2025-08-05

### Changed

- Now **access token** updating in backend

### Fixed

- После обновления access token пользователь всё ещё видит `unauthorized.html`, пока не обновит страницу вручную.

---

## v1.1.0 - 2025-07-29

### Added

- Реализация **рефреш токена**: поддержка получения нового access token по cookie.
- **curl-тестирование** endpoint'а рефреша токена с истечением срока действия.
- Добавлен **middleware**, логирующий ошибки в консоли Chrome Web Inspector.

### Known Issue

- После обновления access token пользователь всё ещё видит `unauthorized.html`, пока не обновит страницу вручную.

## v1.1.0

### Changed

- **Login** API now support login via **username**

---

## v1.1.0 - 2025-07-29

### Added

- Реализация **рефреш токена**: поддержка получения нового access token по cookie.
- **curl-тестирование** endpoint'а рефреша токена с истечением срока действия.
- Добавлен **middleware**, логирующий ошибки в консоли Chrome Web Inspector.

### ⚠ Known Issue

- После обновления access token пользователь всё ещё видит `unauthorized.html`, пока не обновит страницу вручную.

## v1.0.0

### Added

- **Create** function to create database tables.
- **Create User** function to add new users.
- **Get Users** function to fetch the list of users.
- **Delete User** and **Update User** functions for deleting and updating users.
- Asynchronous versions of CRUD operations for better performance and responsiveness.
- Updated Users API to support async operations using `AsyncSession`.

### Changed

- Converted main database operations from synchronous to asynchronous.
- Modified Users API structure to fully support asynchronous workflows.

---

## v0.4.2

### Added

- **CHANGELOQ.md** changelog file to keep track of changes

### Changed

- Refractoring `User` model and schema: `UserCreate`

### Removed

- `practise/` directory

---

## [0.1.0]

### Initial Release

- FastAPI backend project structure
- PostgreSQL + SQLAlchemy setup
- Initial routes and base HTML templates
