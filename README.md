# Scheduloo

## About the Project

Scheduloo is a service for **two-way synchronization** of tasks and events between **Notion** and **Apple Calendar**. The project uses:

- **FastAPI** for building the backend API,
- **SQLAlchemy** as the ORM for database interactions,
- **PostgreSQL** as the main database,
- **Notion API** to access and modify Notion data,
- **CalDAV** protocol for integrating with Apple Calendar.

The goal is to provide a reliable and easy-to-use tool for automatic syncing between these two popular platforms.

---

## Running the Project

To start the backend server, enter the `backend/` directory and run:

```bash
uvicorn app.main:app --reload
```
