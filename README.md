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

# Running the Project

To start the backend server, use the following command depending on your operating system.

**Make sure you're in the root of the `Scheduloo/` project directory before running these commands.**

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
