# 📜 Changelog

All notable changes to this project will be documented in this file.

This project follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)  
and adheres to [Semantic Versioning](https://semver.org/).

---

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
