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
