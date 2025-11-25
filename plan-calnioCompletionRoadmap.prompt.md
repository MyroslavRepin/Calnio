# Plan: Завершение функционала Calnio с waitlist, Notion webhook, CalDAV синхронизацией и веб-интерфейсом

Комплексный план по завершению ключевых функций проекта Calnio: рассылка email для waitlist, стабилизация Notion webhook с исправлением кнопки "Sync Now", полная синхронизация задач между CalDAV (Apple Calendar) и Notion, и обновление веб-интерфейса для управления конфигурацией синхронизации.

## Шаги реализации

### 1. Завершить waitlist email рассылку

**Цель**: Реализовать автоматическую email рассылку для подписчиков waitlist с уведомлением о готовности проекта.

**Задачи**:
- Создать HTML email шаблон `frontend/templates/email/waitlist_launch.html` с использованием Jinja2
- Добавить функцию `send_waitlist_launch_email()` в `services/email/utils/emails.py`, используя существующий `send_html_email`
- Создать admin endpoint `/api/admin/waitlist/send-launch` в `server/app/api/add_waitlist.py` для триггера массовой рассылки
- Добавить функцию выборки всех email из модели `Waitlist` (`server/db/models/waitlist.py`)
- Добавить логирование успешных отправок и ошибок
- Опционально: добавить поле `notified` в модель `Waitlist` для отслеживания отправленных писем

**Файлы для изменения**:
- `services/email/utils/emails.py` - добавить функцию рассылки
- `server/app/api/add_waitlist.py` - добавить endpoint для триггера
- `frontend/templates/email/waitlist_launch.html` - создать шаблон письма
- `server/db/models/waitlist.py` - опционально добавить поле `notified`

---

### 2. Стабилизировать Notion webhook систему

**Цель**: Обеспечить надежную обработку всех типов Notion webhook событий с полным error handling.

**Задачи**:
- Доработать `handle_page_created()` в `server/services/notion_syncing/webhook_handler.py` - завершить логику создания задачи
- Улучшить error handling в `server/app/api/webhooks/notion_webhooks.py` - добавить try-catch для всех типов событий
- Добавить валидацию входящих webhook данных (проверка required полей)
- Расширить Redis кеширование webhook событий для дебаггинга
- Добавить unit тесты для webhook handler методов
- Улучшить логирование с разными уровнями (DEBUG, INFO, ERROR)
- Обработать edge cases: дубликаты событий, missing user/integration, invalid page_id

**Файлы для изменения**:
- `server/services/notion_syncing/webhook_handler.py` - завершить `handle_page_created`
- `server/services/notion_syncing/webhook_service.py` - улучшить `sync_webhook_data`
- `server/app/api/webhooks/notion_webhooks.py` - добавить error handling
- `server/utils/redis/utils.py` - расширить Redis утилиты

---

### 3. Исправить кнопку "Sync Now" в dashboard

**Цель**: Реализовать мгновенную синхронизацию по клику на кнопку "Sync Now" с UI feedback.

**Задачи**:
- Создать новый файл `server/app/api/sync.py` с роутером для sync endpoints
- Добавить POST endpoint `/api/sync/trigger` который:
  - Проверяет авторизацию пользователя (`@access_token_required`)
  - Получает `user_id` из токена
  - Вызывает `notion_sync_background()` из `server/services/notion_syncing/notion_sync.py`
  - Возвращает результат синхронизации (added/updated/deleted counts)
- Преобразовать `<a>` ссылку "Sync Now" в `<button>` в `frontend/templates/routes/dashboard.html` (строка 411)
- Добавить JavaScript обработчик для AJAX POST запроса к `/api/sync/trigger`
- Добавить UI элементы:
  - Loading spinner во время синхронизации
  - Success notification с количеством синхронизированных задач
  - Error notification при ошибке
- Включить роутер в `server/app/main.py`

**Файлы для создания**:
- `server/app/api/sync.py` - новый endpoint для мгновенной синхронизации

**Файлы для изменения**:
- `frontend/templates/routes/dashboard.html` - заменить ссылку на button с JS
- `server/app/main.py` - добавить sync router
- Опционально создать `frontend/static/js/sync.js` для JavaScript логики

---

### 4. Реализовать полную CalDAV → Database синхронизацию

**Цель**: Полностью загрузить все события из Apple Calendar (через CalDAV) в локальную базу данных.

**Задачи**:
- Завершить метод `sync_caldav_to_db()` в `server/services/sync/sync_manager.py`:
  - Использовать `CalDavORM` для получения всех календарей пользователя
  - Для каждого календаря получить все события через `caldav_client.py`
  - Парсить iCal данные через `CaldavEventsRepository.parse_ical_full()`
  - Создавать записи в таблице `CalDavEvent` (`server/db/models/caldav_events.py`)
  - Создавать соответствующие записи в `UserNotionTask` с полем `caldav_id`
- Добавить bulk insert для оптимизации при большом количестве событий
- Реализовать логику проверки существующих событий по `caldav_uid` (избежать дубликатов)
- Добавить обработку deleted событий из CalDAV
- Интегрировать �� `CaldavEventsRepository` (`server/db/repositories/caldav_events.py`)

**Файлы для изменения**:
- `server/services/sync/sync_manager.py` - завершить `sync_caldav_to_db()`
- `server/db/repositories/caldav_events.py` - добавить методы для bulk операций
- `server/services/caldav/caldav_orm.py` - расширить методы получения событий

---

### 5. Реализовать двустороннюю синхронизацию CalDAV ↔ Notion

**Цель**: Обеспечить автоматическую двустороннюю синхронизацию задач между Apple Calendar и Notion с разрешением конфликтов.

**Текущее состояние**:
- Частично реализован метод `sync_caldav_to_db()` в `sync_manager.py` (строки 148-200)
- Используется сравнение timestamp для определения направления синхронизации
- `last_modified_source` и `sync_source` поля для отслеживания источника изменений

**Задачи**:

**5.1. CalDAV → Notion синхронизация**:
- Завершить логику обновления Notion страниц при изменении CalDAV событий
- Использовать `NotionTaskRepository.update()` для обновления задач в Notion
- Использовать Notion API (`get_notion_client`) для создания/обновления страниц в Notion database
- Учитывать `duplicated_template_id` из `UserNotionIntegration` для корректной database

**5.2. Notion → CalDAV синхронизация**:
- Реализовать обновление CalDAV событий при изменении Notion страниц
- Использовать `CalDavORM.Event.update()` для модификации iCal событий
- Обрабатывать удаление: синхронизировать `deleted=True` флаг между системами

**5.3. Конфликт-резолюция**:
- Реализовать стратегию "last-write-wins" по `updated_at` timestamp
- Логировать конфликты для будущего анализа
- Добавить поле `has_conflict` в `UserNotionTask` для пометки конфликтных задач
- Опционально: добавить UI для ручного разрешения конфликтов

**5.4. Интеграция с scheduler**:
- Добавить `SyncService.sync_user_events()` в `scheduler_service.py`
- Запускать полную синхронизацию каждые 5-15 минут (configurable)
- Только для пользователей с `active_sync=True`

**Файлы для изменения**:
- `server/services/sync/sync_manager.py` - завершить все методы синхронизации
- `server/services/scheduler/scheduler_service.py` - добавить sync job
- `server/db/repositories/notion_tasks.py` - добавить методы для Notion API взаимодействия
- `server/services/caldav/caldav_orm.py` - добавить методы обновления событий

---

### 6. Создать веб-интерфейс для управления конфигурацией синхронизации

**Цель**: Предоставить пользователю полный контроль над настройками синхронизации через dashboard.

**Задачи**:

**6.1. Frontend (Dashboard UI)**:
- Создать новый компонент "Sync Settings" в `frontend/templates/routes/dashboard.html`
- Добавить UI элементы:
  - Toggle switch для `active_sync` (включить/выключить автоматическую синхронизацию)
  - Dropdown для выбора CalDAV календарей (Personal, Work, etc.)
  - Dropdown для выбора Notion database (из `UserNotionIntegration.duplicated_template_id`)
  - Slider или input для настройки интервала синхронизации (5/10/15/30 минут)
  - Кнопка "Save Settings"
  - Секция "Sync Status" с отображением последней синхронизации
- Использовать существующие CSS стили из `frontend/static/css/` и следовать coding guidelines (external CSS, semantic HTML)
- Добавить JavaScript для AJAX сохранения настроек

**6.2. Backend API endpoints**:
- Расширить `server/app/api/dashboard.py`:
  - GET `/api/settings/sync` - получить текущие настройки синхронизации
  - POST `/api/settings/sync` - обновить настройки синхронизации
  - GET `/api/calendars/list` - получить список CalDAV календарей пользователя
  - GET `/api/notion/databases` - получить список Notion databases пользователя
- Добавить валидацию входных данных (Pydantic schemas)
- Обновлять поля в модели `User` (`active_sync`) и `UserNotionIntegration`

**6.3. Database изменения**:
- Опционально добавить новую таблицу `SyncConfiguration` для расширенных настроек:
  - `user_id` (FK)
  - `selected_calendar_name` (str)
  - `selected_notion_database_id` (str)
  - `sync_interval_minutes` (int)
  - `last_sync_at` (datetime)
  - `sync_direction` (enum: 'both', 'caldav_to_notion', 'notion_to_caldav')

**Файлы для изменения**:
- `frontend/templates/routes/dashboard.html` - добавить Sync Settings секцию
- `server/app/api/dashboard.py` - добавить API endpoints
- Опционально: `server/db/models/` - создать `sync_configuration.py`
- `frontend/static/css/` - добавить стили для новых компонентов

---

## Архитектурные соображения

### Структура синхронизации

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Action                              │
│                  (Click "Sync Now" button)                       │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                     API: /api/sync/trigger                       │
│              (server/app/api/sync.py)                            │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│               SyncService (sync_manager.py)                      │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  1. sync_caldav_to_db()                                  │   │
│  │     - Fetch CalDAV events via caldav_client.py           │   │
│  │     - Parse iCal data                                    │   │
│  │     - Store in CalDavEvent table                         │   │
│  │     - Create UserNotionTask records                      │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  2. notion_sync_background()                             │   │
│  │     - Fetch Notion pages via notion_client.py            │   │
│  │     - Update UserNotionTask table                        │   │
│  │     - Handle added/updated/deleted pages                 │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  3. Bidirectional Sync (CalDAV ↔ Notion)                │   │
│  │     - Compare timestamps (last_modified_caldav vs        │   │
│  │       notion_updated_at)                                 │   │
│  │     - Sync newer → older                                 │   │
│  │     - Update both CalDavEvent and UserNotionTask         │   │
│  │     - Push changes to Notion API and CalDAV              │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Background Scheduler                          │
│              (scheduler_service.py)                              │
│         Every 5-15 minutes (if active_sync=True)                 │
└─────────────────────────────────────────────────────────────────┘
```

### Поток данных синхронизации

```
CalDAV (iCloud)              Database              Notion
     │                          │                     │
     │  1. Fetch events         │                     │
     ├─────────────────────────►│                     │
     │                          │                     │
     │                          │  2. Create tasks    │
     │                          ├────────────────────►│
     │                          │                     │
     │                          │  3. Fetch pages     │
     │                          │◄────────────────────┤
     │                          │                     │
     │  4. Compare timestamps & │                     │
     │     resolve conflicts    │                     │
     │                          │                     │
     │  5. Push updates         │  6. Push updates    │
     │◄─────────────────────────┼────────────────────►│
```

---

## Дополнительные вопросы для уточнения

### 1. Стратегия разрешения конфликтов

**Вопрос**: Какой приоритет при конфликтах синхронизации (когда событие изменено в обеих системах одновременно)?

**Варианты**:
- **A) Last-write-wins (по timestamp)** - побеждает последнее изменение по времени (рекомендуется для MVP)
- **B) Manual resolution с UI** - пользователь видит конфликт и выбирает какую версию сохранить
- **C) Configurable per-user priority** - пользователь настраивает приоритет: Notion всегда главный или CalDAV всегда главный
- **D) Smart merge** - попытка объединить изменения (например, title из Notion, dates из CalDAV)

**Рекомендация**: Начать с варианта A (last-write-wins), затем добавить B для advanced пользователей.

---

### 2. Частота автоматической синхронизации

**Вопрос**: Текущий scheduler запускается каждые 5 минут (`scheduler_service.py` строка 37). Нужно ли:

**Варианты**:
- **A) Оставить фиксированные 5 минут** - просто и предсказуемо
- **B) Сделать configurable через веб-интерфейс** - пользователь выбирает 5/10/15/30/60 минут
- **C) Адаптивная частота** - чаще синхронизировать для активных пользователей, реже для неактивных
- **D) Real-time через webhooks** - мгновенная синхронизация через Notion webhooks (уже частично реализовано)

**Рекомендация**: Вариант B (configurable) + использовать existing Notion webhooks для real-time обновлений от Notion.

---

### 3. Email шаблон для waitlist

**Вопрос**: Какой тип email отправлять подписчикам waitlist?

**Варианты**:
- **A) Простой текстовый** - "Calnio is live! Sign up at [link]" (быстро реализовать)
- **B) HTML с feature highlights** - красивый дизайн с описанием фич, screenshots, pricing
- **C) Серия писем** - Welcome email → Progress updates (2-3 письма) → Launch announcement
- **D) Персонализированный** - с именем пользователя, custom discount code

**Рекомендация**: Начать с варианта B (HTML с features), затем добавить D (discount codes) для early adopters.

---

### 4. Обработка удаленных событий

**Вопрос**: Как синхронизировать удаление событий между CalDAV и Notion?

**Варианты**:
- **A) Soft delete с флагом** - `deleted=True` в базе, событие скрыто но не удалено (используется сейчас)
- **B) Hard delete из обеих систем** - полное удаление, синхронизируется немедленно
- **C) Архивация** - перемещение в архивную таблицу или Notion database
- **D) Configurable** - пользователь выбирает поведение в настройках

**Рекомендация**: Вариант A (soft delete) для безопасности данных + добавить UI для восстановления удаленных.

---

### 5. Производительность при большом количестве событий

**Вопрос**: Как оптимизировать синхронизацию для пользователей с 1000+ событий?

**Варианты**:
- **A) Incremental sync** - синхронизировать только изменения с последней синхронизации (по `updated_at`)
- **B) Batch processing** - обрабатывать события пакетами по 50-100
- **C) Background tasks (Celery)** - длительные синхронизации в фоновых задачах
- **D) Pagination** - ограничить initial sync определенным периодом (последние 3 месяца)

**Рекомендация**: Комбинация A (incremental) + B (batching) для оптимальной производительности.

---

## Приоритизация задач

### Phase 1: MVP (Минимально работающий продукт)
1. ✅ **Task 3**: Исправить кнопку "Sync Now" (критично для UX)
2. ✅ **Task 2**: Стабилизировать Notion webhooks (критично для надежности)
3. ✅ **Task 4**: CalDAV → Database синхронизация (основа для двусторонней синхронизации)

### Phase 2: Core Features
4. ✅ **Task 5**: Двусторонняя синхронизация CalDAV ↔ Notion (главная фича)
5. ✅ **Task 6**: Веб-интерфейс для конфигурации (важно для пользователей)

### Phase 3: Marketing & Launch
6. ✅ **Task 1**: Waitlist email рассылка (для запуска)

---

## Технические детали

### Необходимые зависимости (уже установлены)
- `caldav` - для работы с CalDAV протоколом
- `notion-client` - официальный Notion API клиент
- `apscheduler` - для background scheduler
- `redis` - для кеширования webhook событий
- `sqlalchemy` - ORM для database
- `fastapi` - веб-фреймворк
- `jinja2` - шаблонизация

### Database Schema изменения

**Опционально добавить**:
- `Waitlist.notified` (Boolean) - для отслеживания отправленных писем
- `SyncConfiguration` table - для расширенных настроек синхронизации
- `SyncLog` table - для логирования истории синхронизаций

**Существующие таблицы**:
- `User` - с полем `active_sync`
- `UserNotionIntegration` - с `duplicated_template_id`
- `UserNotionTask` - с `caldav_id`, `sync_source`, `last_modified_source`
- `CalDavEvent` - для хранения CalDAV событий
- `Waitlist` - для email подписчиков

---

## Тестирование

### Unit Tests
- `tests/test_webhook_handler.py` - тесты для Notion webhook обработчиков
- `tests/test_sync_manager.py` - тесты для синхронизации
- `tests/test_email_service.py` - тесты для email рассылки

### Integration Tests
- Полная синхронизация CalDAV → Notion → CalDAV
- Webhook обработка с реальными Notion событиями
- Email отправка с реальным SMTP

### Manual Testing Checklist
- [ ] Создание события в CalDAV → появляется в Notion
- [ ] Создание страницы в Notion → появляется в CalDAV
- [ ] Обновление события в CalDAV → обновляется в Notion
- [ ] Обновление страницы в Notion → обновляется в CalDAV
- [ ] Удаление события в CalDAV → помечается deleted в Notion
- [ ] Удаление страницы в Notion → помечается deleted в CalDAV
- [ ] Кнопка "Sync Now" работает с UI feedback
- [ ] Waitlist email доставляется корректно
- [ ] Настройки синхронизации сохраняются и применяются

---

## Оценка времени

| Task | Описание | Оценка времени |
|------|----------|---------------|
| 1 | Waitlist email рассылка | 2-3 часа |
| 2 | Стабилизация Notion webhooks | 4-6 часов |
| 3 | Исправление кнопки "Sync Now" | 2-3 часа |
| 4 | CalDAV → Database синхронизация | 6-8 часов |
| 5 | Двусторонняя синхронизация | 10-12 часов |
| 6 | Веб-интерфейс для конфигурации | 6-8 часов |
| **Итого** | | **30-40 часов** |

---

## Следующие шаги

1. **Уточнить вопросы** из раздела "Дополнительные вопросы"
2. **Начать с Task 3** (Sync Now button) - быстрая win для UX
3. **Параллельно работать над Task 2** (Webhook stabilization)
4. **После MVP**: приоритизировать Task 4 и 5 (Core sync functionality)
5. **Перед запуском**: завершить Task 1 и 6 (Marketing + UI)

---

## Риски и митигация

| Риск | Вероятность | Влияние | Митигация |
|------|------------|---------|-----------|
| CalDAV API rate limiting | Средняя | Высокое | Добавить exponential backoff, кеширование |
| Notion API changes | Низкая | Высокое | Использовать официальный SDK, версионирование API |
| Конфликты синхронизации | Высокая | Среднее | Реализовать четкую стратегию разрешения |
| Email deliverability | Средняя | Среднее | Использовать проверенный SMTP, настроить SPF/DKIM |
| Performance с большими данными | Средняя | Высокое | Incremental sync, pagination, background jobs |

---

## Ресурсы и документация

- [Notion API Documentation](https://developers.notion.com/)
- [CalDAV Protocol Spec (RFC 4791)](https://datatracker.ietf.org/doc/html/rfc4791)
- [APScheduler Documentation](https://apscheduler.readthedocs.io/)
- Existing project docs: `docs/WEBHOOK_QUICK_REFERENCE.md`, `docs/POSTGRESQL_ENUM_GUIDE.md`

