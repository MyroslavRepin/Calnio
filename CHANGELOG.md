# 📜 Changelog

All notable changes to this project will be documented in this file.

This project follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)  
and adheres to [Semantic Versioning](https://semver.org/)

<!-- ## vX.Y.Z - YYYY-MM-DD

### 🚀 Added

- Short description of new features or integrations
- New models, endpoints, or functionality

### 🔄 Changed

- Updates or improvements to existing features
- Backend/frontend behavior changes

### 🔧 Fixed

- Bugs or issues that were resolved
- Problems with redirects, tokens, or database

### ⚠ Known Issue

- Anything still broken or limitations users should know -->

## v1.92.2 - 2025-09-30

### 🔧 Fixed

- Login issue related to session_id and 72 bytes limit. Improved session handling to prevent duplicate errors.

## v1.92.1 - 2025-09-30

### 🔧 Fixed

- Fixed and created new `async_get_db_cm` context manager for improved database session handling in APScheduler jobs.

## v1.92.0 - 2025-09-30

### 🚀 Added

- Introduced a new scheduling system using AsyncIOScheduler to periodically synchronize Notion data for users.
- Added `schedulor.py` for job scheduling and lifecycle management (startup/shutdown hooks in `main.py`).
- Added `apscheduler_test.py` script for demonstrating and testing scheduled tasks.
- Created `notion_client.py` to encapsulate Notion client creation and usage.

### 🔄 Changed

- Refactored Notion client instantiation to use the new helper from `notion_client.py` across the codebase.
- Improved database dependency management by refactoring `async_get_db` with `@asynccontextmanager` for cleaner resource handling.
- Updated project structure and documentation (`DIRECTORY_STRUCTURE.md`) to reflect new migration, service, and script files.
- Replaced a logging statement with a print statement in `notion_sync_background` for better visibility during background sync.

### 🔧 Fixed

- Minor improvements and code cleanup for better maintainability.

## v1.91.0 - 2025-09-29

### 🚀 Added

- Enhanced user authentication with authorization check in login flow
- Added centralized logging configuration in config.py
- Added end_date field to Notion tasks for better task management
- Added async connection check and table creation for database management
- Added Alembic migration commands for schema management
- Added directory tree generation script with Git pre-commit hook
- Added user information display on dashboard

### 🔄 Changed

- Refactored project structure for better organization
- Renamed task_date to start_date in Notion tasks
- Unified background task execution into `notion_sync_background`
- Moved CRUD operations to services directory
- Refactored token handling and user authentication flow
- Updated Notion integration with improved page handling
- Streamlined task handling in API endpoints
- Enhanced database management with better async handling

### 🔧 Fixed

- Fixed date type error in database operations
- Fixed logging setup by removing direct configuration from main.py
- Fixed task management with proper background processing
- Fixed Notion task synchronization issues

### 🗑️ Removed

- Removed direct logging configuration from main.py
- Removed deprecated database scripts

## v1.9.4 - 2025-09-18

### 🚀 Added

- Added `background_tasks` module for async task processing

### 🔄 Changed

- Refactored and moved task update, create, and delete functions to `background_tasks/notion_sync.py`
- Applied Alembic migrations

## v1.9.3 - 2025-08-20

### 🔄 Changed

- Moving **CRUD** functions from **utils/** to **CRUD/**

## v1.9.0 - 2025-09-16

### 🚀 Added

- Adds Function to add all tasks from database

## v1.8.0 - 2025-09-12

### 🚀 Added

- New model: **UserNotionTask**
- Adding feature to add task from html form and save to db

## v1.7.0 - 2025-09-10

### 🔄 Changed

- Now config of environments controls from **.env**

## v1.6.2 - 2025-09-9

### 🔄 Changed

- Now if user is logged in he will be redirected to dashboard

## v1.4.1 - 2025-08-07

### 🔧 Fixed

- Need to open in web as **localhost** not as **0.0.0.0**

---

## v1.4.0 - 2025-08-07

### 🚀 Added

- Adding Notion integrations to db
- New model: **UserNotionIntegration**

## v1.2.1 - 2025-08-05

### ⚠ Known Issue

- Cross-Site redirect erases cookies

---

## v1.30 - 2025-08-05

### 🚀 Added

- Updating password functional

## v1.2.1 - 2025-08-05

### ⚠ Fixed

- Success box after **updating profile** can disapear after **5 sec**

---

## v1.2.0 - 2025-08-05

### 🔄 Changed

- Now **access token** updating in backend

### ⚠ Fixed

- После обновления access token пользователь всё ещё видит `unauthorized.html`, пока не обновит страницу вручную.

---

## v1.1.0 - 2025-07-29

### 🚀 Added

- Реализация **рефреш токена**: поддержка получения нового access token по cookie.
- **curl-тестирование** endpoint'а рефреша токена с истечением срока действия.
- Добавлен **middleware**, логирующий ошибки в консоли Chrome Web Inspector.

### ⚠ Known Issue

- После обновления access token пользователь всё ещё видит `unauthorized.html`, пока не обновит страницу вручную.

## v1.1.0

### 🔄 Changed

- **Login** API now support login via **username**

---

## v1.1.0 - 2025-07-29

### 🚀 Added

- Реализация **рефреш токена**: поддержка получения нового access token по cookie.
- **curl-тестирование** endpoint'а рефреша токена с истечением срока действия.
- Добавлен **middleware**, логирующий ошибки в консоли Chrome Web Inspector.

### ⚠ Known Issue

- После обновления access token пользователь всё ещё видит `unauthorized.html`, пока не обновит страницу вручную.

## v1.0.0

### 🚀 Added

- **Create** function to create database tables.
- **Create User** function to add new users.
- **Get Users** function to fetch the list of users.
- **Delete User** and **Update User** functions for deleting and updating users.
- Asynchronous versions of CRUD operations for better performance and responsiveness.
- Updated Users API to support async operations using `AsyncSession`.

### 🔄 Changed

- Converted main database operations from synchronous to asynchronous.
- Modified Users API structure to fully support asynchronous workflows.

---

## v0.4.2

### 🚀 Added

- **CHANGELOQ.md** changelog file to keep track of changes

### 🔄 Changed

- Refractoring `User` model and schema: `UserCreate`

### 🗑 Removed

- `practise/` directory

---

## [0.1.0]

### 🚀 Initial Release

- FastAPI backend project structure
- PostgreSQL + SQLAlchemy setup
- Initial routes and base HTML templates
