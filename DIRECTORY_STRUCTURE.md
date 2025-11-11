Calnio/
├── backend/
│   └── app/
│       └── tools/
│           ├── caldav/
│           │   ├── __init__.py
│           │   ├── models.py
│           │   ├── orm.py
│           │   └── README.md
│           └── __init__.py
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
├── generated_docs/
│   ├── WEBHOOK_QUICK_REFERENCE.md
│   └── WEBHOOK_TESTING.md
├── logs/
├── loki-setup/
├── scripts/
│   ├── apscheduler_test.py
│   ├── caldav_crud_demo.py
│   ├── cleanup_duplicates.py
│   ├── generate_tree.py
│   ├── migrate_normalize_ids.py
│   ├── playground.py
│   └── setup_precommit.py
├── server/
│   ├── alembic/
│   │   ├── versions/
│   │   │   ├── 4192080716ba_add_calendars_table.py
│   │   │   └── 868c1b1fb071_init_fresh_migration.py
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
│   │   │   ├── caldav_events.py
│   │   │   ├── notion_pages.py
│   │   │   └── users.py
│   │   ├── __init__.py
│   │   ├── main.py
│   │   └── version.py
│   ├── config/
│   ├── db/
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── caldav_events.py
│   │   │   ├── calendars.py
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
│   │   ├── caldav/
│   │   │   ├── __init__.py
│   │   │   ├── caldav_client.py
│   │   │   ├── caldav_fetch.py
│   │   │   ├── caldav_orm.py
│   │   │   └── playground.py
│   │   ├── crud/
│   │   │   ├── __init__.py
│   │   │   ├── caldav_events.py
│   │   │   ├── tasks.py
│   │   │   └── users.py
│   │   ├── notion_syncing/
│   │   │   ├── __init__.py
│   │   │   ├── notion_integrations.py
│   │   │   ├── notion_sync.py
│   │   │   └── webhook_service.py
│   │   ├── redis/
│   │   │   ├── __init__.py
│   │   │   └── redis.py
│   │   ├── scheduler/
│   │   │   ├── __init__.py
│   │   │   └── scheduler_service.py
│   │   ├── sync/
│   │   ├── __init__.py
│   │   └── postgres_trigger.py
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
├── robots.txt
└── START_SERVER.sh
