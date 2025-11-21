Calnio/
├── calnio/
├── certbot/
│   ├── conf/
│   └── www/
├── docs/
│   ├── CELERY_REDIS_DIAGNOSTICS.md
│   ├── EXAMPLE_TRIGGERS_WITH_ENUM.py
│   ├── POSTGRESQL_ENUM_GUIDE.md
│   ├── WEBHOOK_QUICK_REFERENCE.md
│   └── WEBHOOK_TESTING.md
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
│   │   │   ├── base.css
│   │   │   ├── brutalist-components.css
│   │   │   ├── brutalist-layouts.css
│   │   │   ├── components.css
│   │   │   ├── fonts.css
│   │   │   ├── layout.css
│   │   │   ├── login.css
│   │   │   ├── main.css
│   │   │   └── variables.css
│   │   └── js/
│   │       ├── api.js
│   │       ├── brutalist-nav.js
│   │       ├── burger-menu.js
│   │       ├── dashboard.js
│   │       ├── header.js
│   │       ├── refreshThenDashboard.js
│   │       └── theme-toggle.js
│   └── templates/
│       ├── email/
│       ├── errors/
│       │   ├── 404.html
│       │   ├── error.html
│       │   └── unauthorized.html
│       └── routes/
│           ├── 500.html
│           ├── base.html
│           ├── brutalist-dashboard.html
│           ├── brutalist-landing.html
│           ├── brutalist-login.html
│           ├── brutalist-signup.html
│           ├── dashboard.html
│           ├── landing.html
│           ├── login.html
│           ├── signup.html
│           ├── tasks.html
│           ├── users.html
│           └── waitlist.html
├── grafana/
│   ├── calnio_litestar_dashboard.json
│   └── datasources.yaml
├── nginx/
│   └── conf.d/
│       └── default.conf
├── scripts/
│   ├── apscheduler_test.py
│   ├── caldav_crud_demo.py
│   ├── check_notion_access.py
│   ├── cleanup_duplicates.py
│   ├── generate_tree.py
│   ├── migrate_normalize_ids.py
│   ├── playground.py
│   └── setup_precommit.py
├── server/
│   ├── alembic/
│   │   ├── versions/
│   │   │   ├── 040918af799d_rename_column.py
│   │   │   ├── 086698cdd088_drop_default_values_from_string_to_enum.py
│   │   │   ├── 0dcff28cb147_change_column_type.py
│   │   │   ├── 19fc4fe2811f_change_column_type.py
│   │   │   ├── 23502f720669_add_default_pending_to_sync_status.py
│   │   │   ├── 346bc90683e4_merge_heads_after_branch_merge.py
│   │   │   ├── 4192080716ba_add_calendars_table.py
│   │   │   ├── 569210df4a2b_rename_caldav_uid_to_caldav_id.py
│   │   │   ├── 589f8fa06ba0_update_syncstatus_to_enum_manually.py
│   │   │   ├── 665c6414c6ba_make_icloud_email_nullable.py
│   │   │   ├── 7a35541b1b09_add_default_false_to_deleted_column.py
│   │   │   ├── 868c1b1fb071_init_fresh_migration.py
│   │   │   ├── a4ab66b804c6_convert_sync_status_to_postgresql_enum.py
│   │   │   ├── b9853889096e_add_new_collumn.py
│   │   │   ├── d93d7ae96ef5_auto_generated_migration.py
│   │   │   ├── dc86913f74d2_add_timezone_to_caldavevents_datetimes.py
│   │   │   ├── eca87c3e846a_add_deletede_to_usernotointasks_and_.py
│   │   │   ├── f0995c8c6da0_update_syncstatus_enum_values.py
│   │   │   └── fed31d6be9ea_auto_generated_migration.py
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
│   │   │   ├── add_waitlist.py
│   │   │   ├── auth.py
│   │   │   ├── brutalist.py
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
│   │   │   ├── users.py
│   │   │   └── waitlist.py
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── main_litestar.py
│   │   └── version.py
│   ├── config/
│   ├── db/
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── caldav_events.py
│   │   │   ├── calendars.py
│   │   │   ├── enums.py
│   │   │   ├── notion_integration.py
│   │   │   ├── tasks.py
│   │   │   ├── users.py
│   │   │   └── waitlist.py
│   │   ├── repositories/
│   │   │   ├── caldav_events.py
│   │   │   ├── notion_tasks.py
│   │   │   └── user.py
│   │   ├── tools/
│   │   │   ├── __init__.py
│   │   │   ├── create_all_tables.py
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
│   │   │   ├── caldav_orm.py
│   │   │   ├── playground.py
│   │   │   ├── user_calendars.py
│   │   │   └── user_events.py
│   │   ├── crud/
│   │   │   ├── __init__.py
│   │   │   ├── caldav_events.py
│   │   │   └── users.py
│   │   ├── notion_syncing/
│   │   │   ├── __init__.py
│   │   │   ├── notion_integrations.py
│   │   │   ├── notion_sync.py
│   │   │   ├── webhook_handler.py
│   │   │   └── webhook_service.py
│   │   ├── redis/
│   │   │   ├── __init__.py
│   │   │   └── redis.py
│   │   ├── scheduler/
│   │   │   ├── __init__.py
│   │   │   └── scheduler_service.py
│   │   ├── sync/
│   │   │   └── sync_manager.py
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
├── services/
│   ├── email/
│   │   ├── schemas/
│   │   ├── templates/
│   │   │   ├── account_created.html
│   │   │   ├── password_reset.html
│   │   │   ├── product_updates.html
│   │   │   └── requirements.txt
│   │   ├── utils/
│   │   │   ├── __init__.py
│   │   │   └── emails.py
│   │   ├── worker/
│   │   │   ├── __init__.py
│   │   │   └── auth.py
│   │   ├──  requirements.txt
│   │   ├── __init__.py
│   │   ├── celery_app.py
│   │   ├── Dockerfile
│   │   └── main.py
│   ├── sync/
│   │   ├── server/
│   │   │   └── app/
│   │   │       ├── api/
│   │   │       ├── core/
│   │   │       └── schemas/
│   │   └── Dockerfile
│   └── __init__.py
├── tests/
│   └── load/
│       ├── load_test.js
│       └── playground.js
├── .gitignore
├── alembic.ini
├── caldav_events.sql
├── calnio_backup.dump
├── CHANGELOG.md
├── db_schema.sql
├── DIRECTORY_STRUCTURE.md
├── docker-compose.yml
├── Dockerfile
├── LICENSE
├── loki-config.yaml
├── main.py
├── manage.py
├── ngrok.yml
├── plan-calnioCompletionRoadmap.prompt.md
├── Procfile
├── prometheus.yml
├── promtail-config.yaml
├── railway.json
├── README.md
├── requirements.txt
├── robots.txt
├── START_SERVER.sh
└── verify_enum_fix.py
