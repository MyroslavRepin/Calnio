# Project Directory Structure

Generated automatically on commit.

```
Calnio/
├── frontend/
│   ├── assets/
│   │   ├── apple_calendar_app_logo.png
│   │   ├── apple_logo.png
│   │   ├── apple_reminders_app_logo.png
│   │   ├── github_logo.png
│   │   ├── google_logo.png
│   │   └── notion_app_logo.png
│   ├── static/
│   │   ├── css/
│   │   │   ├── components.css
│   │   │   ├── fonts.css
│   │   │   ├── layout.css
│   │   │   ├── login.css
│   │   │   └── main.css
│   │   └── js/
│   │       ├── api.js
│   │       ├── burger-menu.js
│   │       ├── dashboard.js
│   │       ├── header.js
│   │       └── refreshThenDashboard.js
│   └── templates/
│       ├── 404.html
│       ├── 500.html
│       ├── burger-menu-example.html
│       ├── dashboard.html
│       ├── error.html
│       ├── landing.html
│       ├── load_dashboard.html
│       ├── login.html
│       ├── signup.html
│       ├── tasks.html
│       ├── unauthorized.html
│       └── users.html
├── logs/
├── scripts/
│   ├── apscheduler_test.py
│   ├── cleanup_duplicates.py
│   ├── generate_tree.py
│   ├── migrate_normalize_ids.py
│   ├── playground.py
│   └── setup_precommit.py
├── server/
│   ├── alembic/
│   │   ├── versions/
│   │   │   ├── 195306bb06b8_rename_task_date_to_start_date_in_.py
│   │   │   ├── 424907f7e342_add_sync_interval_seconds_column_to_.py
│   │   │   ├── 648e7163d6ae_add_unique_constraint_to_workspace_id_.py
│   │   │   ├── 723eede5975e_initial_migration.py
│   │   │   ├── __init__.py
│   │   │   ├── a3d53bfab21d_convert_datetime_columns_to_timestamptz_.py
│   │   │   ├── cfef8e5e21e7_add_end_date_to_notion_tasks.py
│   │   │   └── f74ea4b9e097_add_active_sync_column_manually.py
│   │   ├── __init__.py
│   │   ├── env.py
│   │   ├── README
│   │   └── script.py.mako
│   ├── app/
│   │   ├── api/
│   │   │   ├── errors/
│   │   │   │   ├── __init__.py
│   │   │   │   └── error_404.py
│   │   │   ├── webhooks/
│   │   │   │   └── notion_webhooks.py
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── dashboard.py
│   │   │   ├── landing.py
│   │   │   └── refresh_cookies.py
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── config.py
│   │   │   └── logging_config.py
│   │   ├── dops/
│   │   ├── middleware/
│   │   │   └── ignore_logging.py
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   ├── notion_pages.py
│   │   │   └── users.py
│   │   ├── __init__.py
│   │   ├── main.py
│   │   └── version.py
│   ├── config/
│   ├── db/
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── notion_integration.py
│   │   │   ├── tasks.py
│   │   │   └── users.py
│   │   ├── repositories/
│   │   │   └── user.py
│   │   ├── tools/
│   │   │   ├── __init__.py
│   │   │   ├── create_missing_tables.py
│   │   │   └── recreate_tables.py
│   │   ├── __init__.py
│   │   ├── database.py
│   │   ├── deps.py
│   │   ├── redis_client.py
│   │   └── utils.py
│   ├── integrations/
│   │   ├── notion/
│   │   │   ├── __init__.py
│   │   │   ├── notion_client.py
│   │   │   ├── pages.py
│   │   │   └── utils.py
│   │   ├── oauth/
│   │   │   ├── notion/
│   │   │   │   ├── __init__.py
│   │   │   │   └── notion_callback.py
│   │   │   └── __init__.py
│   │   └── __init__.py
│   ├── middleware/
│   │   ├── __init__.py
│   │   └── ignore_logging.py
│   ├── services/
│   │   ├── crud/
│   │   │   ├── __init__.py
│   │   │   ├── tasks.py
│   │   │   └── users.py
│   │   ├── notion_syncing/
│   │   │   ├── __init__.py
│   │   │   └── webhook_service.py
│   │   ├── redis/
│   │   │   ├── __init__.py
│   │   │   └── redis.py
│   │   ├── scheduler/
│   │   ├── __init__.py
│   │   ├── notion_integrations.py
│   │   ├── notion_sync.py
│   │   └── scheduler_service.py
│   ├── utils/
│   │   ├── notion/
│   │   │   ├── __init__.py
│   │   │   ├── config.py
│   │   │   └── utils.py
│   │   ├── redis/
│   │   │   └── utils.py
│   │   ├── security/
│   │   │   ├── __init__.py
│   │   │   ├── jwt_exp_check.py
│   │   │   ├── time_stats_decoder.py
│   │   │   └── utils.py
│   │   ├── __init__.py
│   │   ├── decorators.py
│   │   └── utils.py
│   └── __init__.py
├── .gitignore
├── alembic.ini
├── CHANGELOG.md
├── DIRECTORY_STRUCTURE.md
├── LICENSE
├── main.py
├── manage.py
├── Procfile
├── railway.json
├── README.md
├── redis_test.py
├── requirements.txt
└── START_SERVER.sh
```

## Configuration

This tree excludes files and directories matching patterns from:

### .gitignore patterns:
- .venv
- *__pycache__
- .DS_Store
- .vscode
- settings.json
- .idea
- server/alembic/versions/__pycache__

### Additional exclusions:
- Python cache files (*.pyc, __pycache__)
- Hidden files and directories (except .gitignore)
- SSL certificates (*.pem, *.key)
- Database dumps (dump.rdb)
- Log files (*.log)
- Temporary files (*.tmp, *.cache)
- Node modules
- Build artifacts (*.egg-info, .pytest_cache)

To modify additional ignored extensions, edit `scripts/generate_tree.py`.
The script automatically respects all patterns in `.gitignore`.
