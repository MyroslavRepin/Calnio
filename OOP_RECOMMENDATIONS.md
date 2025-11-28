# Рекомендации по переводу проекта Calnio на ООП-архитектуру

## Обзор текущего состояния

Проект Calnio уже имеет частичную структуру ООП, однако архитектура неоднородна:
- Часть кода использует классы (например, `CalDavORM`, `NotionTaskRepository`)
- Часть кода — функциональный стиль (например, `server/services/crud/users.py`)
- Смешение бизнес-логики и работы с БД в одних классах

---

## 1. Какие классы нужны

### 1.1 Domain Models (Модели предметной области)

Эти классы отвечают за бизнес-логику и не зависят от базы данных.

```
├── domain/
│   ├── entities/
│   │   ├── user.py           # UserEntity
│   │   ├── task.py           # TaskEntity
│   │   ├── event.py          # CalDavEventEntity
│   │   ├── calendar.py       # CalendarEntity
│   │   └── integration.py    # NotionIntegrationEntity
│   │
│   ├── value_objects/
│   │   ├── email.py          # Email (ValueObject)
│   │   ├── date_range.py     # DateRange (ValueObject)
│   │   ├── sync_status.py    # SyncStatus (Enum)
│   │   └── credentials.py    # ICloudCredentials (ValueObject)
│   │
│   └── services/
│       ├── sync_service.py   # SyncDomainService
│       └── conflict_resolver.py  # ConflictResolver
```

### 1.2 Repositories (Репозитории)

Абстракция для работы с хранилищем данных.

```
├── repositories/
│   ├── base.py               # BaseRepository[T] (абстрактный)
│   ├── user_repository.py    # UserRepository
│   ├── task_repository.py    # TaskRepository
│   ├── event_repository.py   # CalDavEventRepository
│   └── integration_repository.py  # NotionIntegrationRepository
```

### 1.3 Services (Сервисы приложения)

Координация бизнес-процессов.

```
├── services/
│   ├── auth/
│   │   ├── auth_service.py           # AuthService
│   │   └── token_service.py          # TokenService
│   │
│   ├── sync/
│   │   ├── notion_sync_service.py    # NotionSyncService
│   │   ├── caldav_sync_service.py    # CalDavSyncService
│   │   └── bidirectional_sync.py     # BidirectionalSyncService
│   │
│   ├── user/
│   │   └── user_service.py           # UserService
│   │
│   └── calendar/
│       └── calendar_service.py       # CalendarService
```

### 1.4 Integrations (Интеграции с внешними системами)

Адаптеры для внешних API.

```
├── integrations/
│   ├── notion/
│   │   ├── notion_client.py    # NotionClient (уже есть)
│   │   └── notion_adapter.py   # NotionAdapter
│   │
│   ├── caldav/
│   │   ├── caldav_client.py    # CalDavClient (уже есть)
│   │   └── caldav_adapter.py   # CalDavAdapter
│   │
│   └── email/
│       └── email_service.py    # EmailService
```

### 1.5 Infrastructure

Инфраструктурные компоненты.

```
├── infrastructure/
│   ├── database/
│   │   ├── session.py          # DatabaseSession
│   │   └── unit_of_work.py     # UnitOfWork
│   │
│   ├── cache/
│   │   └── redis_cache.py      # RedisCache
│   │
│   └── scheduler/
│       └── scheduler.py        # TaskScheduler
```

---

## 2. Какие атрибуты должны быть внутри классов

### 2.1 Entity: UserEntity

```python
class UserEntity:
    id: int
    email: Email                     # ValueObject
    username: str
    icloud_credentials: ICloudCredentials | None  # ValueObject
    is_active: bool
    is_superuser: bool
    active_sync: bool
    created_at: datetime
    updated_at: datetime

    # Relationships (lazy loading)
    _notion_integration: NotionIntegrationEntity | None
    _tasks: list[TaskEntity]
    _events: list[CalDavEventEntity]
```

### 2.2 Entity: TaskEntity (UserNotionTask)

```python
class TaskEntity:
    id: int
    user_id: int
    notion_page_id: str | None
    notion_url: str | None
    title: str
    description: str | None
    status: str | None
    priority: str | None
    select_option: str | None
    start_date: datetime | None
    end_date: datetime | None
    done: bool

    # Sync metadata
    sync_source: str
    last_synced_at: datetime
    caldav_id: str | None
    has_conflict: bool
    last_modified_source: str
    sync_status: SyncStatus

    # Soft delete
    deleted: bool
    deleted_at: datetime | None
```

### 2.3 Entity: CalDavEventEntity

```python
class CalDavEventEntity:
    id: int
    user_id: int
    caldav_uid: str
    caldav_url: str
    title: str
    description: str | None
    start_time: datetime | None
    end_time: datetime | None
    notion_page_id: str | None

    # Sync metadata
    sync_source: str
    sync_status: SyncStatus
    last_synced_at: datetime
    has_conflict: bool
    last_modified_source: str

    # Soft delete
    deleted: bool
    deleted_at: datetime | None
```

### 2.4 Repository: BaseRepository

```python
class BaseRepository[T]:
    _session: AsyncSession           # Сессия БД
    _model_class: type[T]            # Класс SQLAlchemy модели
```

### 2.5 Service: UserService

```python
class UserService:
    _user_repository: UserRepository
    _auth_service: AuthService
    _email_service: EmailService
```

### 2.6 Service: NotionSyncService

```python
class NotionSyncService:
    _task_repository: TaskRepository
    _notion_adapter: NotionAdapter
    _conflict_resolver: ConflictResolver
    _scheduler: TaskScheduler
```

---

## 3. Какие методы нужны

### 3.1 BaseRepository[T] (абстрактный базовый репозиторий)

```python
class BaseRepository[T]:
    async def get_by_id(self, id: int) -> T | None
    async def get_all(self, filters: dict = None) -> list[T]
    async def create(self, entity: T) -> T
    async def update(self, entity: T) -> T
    async def delete(self, id: int) -> bool
    async def soft_delete(self, id: int) -> bool
    async def exists(self, id: int) -> bool
    async def count(self, filters: dict = None) -> int
```

### 3.2 UserRepository

```python
class UserRepository(BaseRepository[UserEntity]):
    # Наследует базовые методы + добавляет специфичные
    async def get_by_email(self, email: str) -> UserEntity | None
    async def get_by_username(self, username: str) -> UserEntity | None
    async def get_by_login(self, login: str) -> UserEntity | None  # email или username
    async def get_with_notion_integration(self, user_id: int) -> UserEntity | None
    async def get_active_sync_users(self) -> list[UserEntity]
    async def update_password(self, user_id: int, hashed_password: str) -> bool
    async def set_icloud_credentials(self, user_id: int, credentials: ICloudCredentials) -> bool
```

### 3.3 TaskRepository

```python
class TaskRepository(BaseRepository[TaskEntity]):
    async def get_by_notion_page_id(self, page_id: str) -> TaskEntity | None
    async def get_by_user_id(self, user_id: int, include_deleted: bool = False) -> list[TaskEntity]
    async def get_pending_sync(self, user_id: int) -> list[TaskEntity]
    async def get_with_conflicts(self, user_id: int) -> list[TaskEntity]
    async def bulk_create(self, tasks: list[TaskEntity]) -> list[TaskEntity]
    async def bulk_update(self, tasks: list[TaskEntity]) -> list[TaskEntity]
    async def mark_synced(self, task_id: int, source: str) -> bool
    async def mark_conflict(self, task_id: int) -> bool
    async def resolve_conflict(self, task_id: int, resolution: str) -> bool
```

### 3.4 CalDavEventRepository

```python
class CalDavEventRepository(BaseRepository[CalDavEventEntity]):
    async def get_by_caldav_uid(self, uid: str) -> CalDavEventEntity | None
    async def get_by_user_id(self, user_id: int) -> list[CalDavEventEntity]
    async def get_by_date_range(self, user_id: int, start: datetime, end: datetime) -> list[CalDavEventEntity]
    async def get_unsynced(self, user_id: int) -> list[CalDavEventEntity]
    async def sync_from_caldav(self, user_id: int, events: list[CalDavEventEntity]) -> dict
```

### 3.5 UserService

```python
class UserService:
    async def register(self, email: str, username: str, password: str) -> UserEntity
    async def login(self, login: str, password: str) -> tuple[UserEntity, str, str]  # user, access, refresh
    async def logout(self, user_id: int) -> bool
    async def get_profile(self, user_id: int) -> UserEntity
    async def update_profile(self, user_id: int, data: dict) -> UserEntity
    async def change_password(self, user_id: int, old_password: str, new_password: str) -> bool
    async def set_icloud_credentials(self, user_id: int, email: str, app_password: str) -> bool
    async def toggle_sync(self, user_id: int, active: bool) -> bool
```

### 3.6 NotionSyncService

```python
class NotionSyncService:
    async def sync_all(self, user_id: int) -> SyncResult
    async def sync_task(self, user_id: int, page_id: str) -> TaskEntity
    async def handle_webhook(self, event_type: str, data: dict) -> bool
    async def push_to_notion(self, task: TaskEntity) -> bool
    async def pull_from_notion(self, user_id: int) -> list[TaskEntity]
    async def resolve_conflicts(self, user_id: int) -> list[TaskEntity]
```

### 3.7 CalDavSyncService

```python
class CalDavSyncService:
    async def sync_all(self, user_id: int) -> SyncResult
    async def sync_calendar(self, user_id: int, calendar_name: str) -> list[CalDavEventEntity]
    async def push_event(self, event: CalDavEventEntity) -> bool
    async def pull_events(self, user_id: int, calendar_name: str) -> list[CalDavEventEntity]
    async def delete_event(self, user_id: int, event_uid: str) -> bool
```

### 3.8 AuthService

```python
class AuthService:
    def create_access_token(self, user_id: int) -> str
    def create_refresh_token(self, user_id: int) -> str
    def verify_token(self, token: str) -> dict | None
    def refresh_tokens(self, refresh_token: str) -> tuple[str, str]
    def hash_password(self, password: str) -> str
    def verify_password(self, plain: str, hashed: str) -> bool
```

---

## 4. Что передавать в `__init__`, что в методы

### 4.1 Принцип: Dependency Injection

**В `__init__` передаём:**
- Зависимости (другие сервисы, репозитории)
- Конфигурационные параметры
- Долгоживущие объекты (логгеры, пулы соединений)

**В методы передаём:**
- Данные для обработки
- Идентификаторы сущностей
- Параметры конкретной операции

### 4.2 Примеры

#### Repository

```python
class TaskRepository(BaseRepository[TaskEntity]):
    def __init__(self, session: AsyncSession):
        """
        __init__ получает:
        - session: сессия БД (долгоживущая зависимость)
        """
        self._session = session
        self._model_class = UserNotionTask

    async def get_by_user_id(self, user_id: int, include_deleted: bool = False) -> list[TaskEntity]:
        """
        Метод получает:
        - user_id: идентификатор для фильтрации
        - include_deleted: параметр конкретной операции
        """
        ...
```

#### Service

```python
class NotionSyncService:
    def __init__(
        self,
        task_repository: TaskRepository,          # Зависимость
        notion_adapter: NotionAdapter,            # Зависимость
        conflict_resolver: ConflictResolver,      # Зависимость
        logger: Logger = None                     # Опциональная зависимость
    ):
        """
        __init__ получает все зависимости для работы сервиса
        """
        self._task_repo = task_repository
        self._notion = notion_adapter
        self._resolver = conflict_resolver
        self._logger = logger or get_default_logger()

    async def sync_task(self, user_id: int, page_id: str) -> TaskEntity:
        """
        Метод получает:
        - user_id: кому принадлежит задача
        - page_id: какую страницу синхронизировать
        """
        ...
```

#### Entity (Data Class)

```python
@dataclass
class TaskEntity:
    def __init__(
        self,
        # Обязательные поля
        user_id: int,
        title: str,
        sync_source: str,
        # Опциональные поля с дефолтами
        id: int | None = None,
        description: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        done: bool = False,
        deleted: bool = False
    ):
        """
        Entity получает все свои атрибуты в __init__
        """
        ...

    def mark_as_done(self) -> None:
        """Бизнес-метод не принимает параметры — работает с self"""
        self.done = True
        self.status = "COMPLETED"

    def set_date_range(self, start: datetime, end: datetime) -> None:
        """Метод принимает данные для изменения состояния"""
        if end < start:
            raise ValueError("End date cannot be before start date")
        self.start_date = start
        self.end_date = end
```

### 4.3 Таблица: Что куда передавать

| Компонент         | В `__init__`                              | В методы                                |
|-------------------|-------------------------------------------|-----------------------------------------|
| **Repository**    | `session`, `model_class`                  | `id`, `entity`, `filters`, `limit`      |
| **Service**       | `repositories`, `adapters`, `config`      | `user_id`, `data`, `options`            |
| **Entity**        | Все атрибуты сущности                     | Данные для бизнес-операций              |
| **Adapter**       | `client`, `config`, `credentials`         | Параметры конкретного запроса           |
| **ValueObject**   | Все данные (immutable)                    | Методы обычно без параметров            |

---

## 5. Как организовать CRUD через репозитории

### 5.1 Базовый Generic-репозиторий

```python
from abc import ABC, abstractmethod
from typing import TypeVar, Generic, Type
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, update
from sqlalchemy.orm import DeclarativeBase

T = TypeVar("T", bound=DeclarativeBase)


class BaseRepository(ABC, Generic[T]):
    """Абстрактный базовый репозиторий с CRUD-операциями"""

    def __init__(self, session: AsyncSession, model_class: Type[T]):
        self._session = session
        self._model_class = model_class

    # ==================== CREATE ====================
    async def create(self, entity_data: dict) -> T:
        """Создание новой записи"""
        entity = self._model_class(**entity_data)
        self._session.add(entity)
        await self._session.commit()
        await self._session.refresh(entity)
        return entity

    async def bulk_create(self, entities_data: list[dict]) -> list[T]:
        """Массовое создание записей"""
        entities = [self._model_class(**data) for data in entities_data]
        self._session.add_all(entities)
        await self._session.commit()
        return entities

    # ==================== READ ====================
    async def get_by_id(self, id: int) -> T | None:
        """Получение по ID"""
        stmt = select(self._model_class).where(self._model_class.id == id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all(
        self,
        filters: dict | None = None,
        limit: int | None = None,
        offset: int = 0
    ) -> list[T]:
        """Получение списка с фильтрацией и пагинацией"""
        stmt = select(self._model_class)

        if filters:
            for field, value in filters.items():
                if hasattr(self._model_class, field):
                    stmt = stmt.where(getattr(self._model_class, field) == value)

        if limit:
            stmt = stmt.limit(limit).offset(offset)

        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def exists(self, id: int) -> bool:
        """Проверка существования"""
        entity = await self.get_by_id(id)
        return entity is not None

    async def count(self, filters: dict | None = None) -> int:
        """Подсчёт записей"""
        entities = await self.get_all(filters=filters)
        return len(entities)

    # ==================== UPDATE ====================
    async def update(self, id: int, update_data: dict) -> T | None:
        """Обновление записи"""
        entity = await self.get_by_id(id)
        if not entity:
            return None

        for field, value in update_data.items():
            if hasattr(entity, field):
                setattr(entity, field, value)

        await self._session.commit()
        await self._session.refresh(entity)
        return entity

    async def bulk_update(self, updates: list[dict]) -> list[T]:
        """Массовое обновление (каждый dict должен содержать 'id')"""
        updated = []
        for upd in updates:
            id = upd.pop("id", None)
            if id:
                entity = await self.update(id, upd)
                if entity:
                    updated.append(entity)
        return updated

    # ==================== DELETE ====================
    async def delete(self, id: int) -> bool:
        """Жёсткое удаление"""
        entity = await self.get_by_id(id)
        if not entity:
            return False

        await self._session.delete(entity)
        await self._session.commit()
        return True

    async def soft_delete(self, id: int) -> bool:
        """Мягкое удаление (если есть поля deleted/deleted_at)"""
        from datetime import datetime, UTC

        entity = await self.get_by_id(id)
        if not entity:
            return False

        if hasattr(entity, "deleted"):
            entity.deleted = True
        if hasattr(entity, "deleted_at"):
            entity.deleted_at = datetime.now(UTC)

        await self._session.commit()
        return True
```

### 5.2 Конкретная реализация: TaskRepository

```python
from datetime import datetime
from sqlalchemy import select, and_, or_
from server.db.models.tasks import UserNotionTask
from server.db.models.enums import SyncStatus


class TaskRepository(BaseRepository[UserNotionTask]):
    """Репозиторий для работы с задачами Notion"""

    def __init__(self, session: AsyncSession):
        super().__init__(session, UserNotionTask)

    # ==================== Специфичные методы READ ====================

    async def get_by_notion_page_id(self, page_id: str) -> UserNotionTask | None:
        """Поиск по Notion page ID"""
        stmt = select(self._model_class).where(
            self._model_class.notion_page_id == page_id
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_user_id(
        self,
        user_id: int,
        include_deleted: bool = False
    ) -> list[UserNotionTask]:
        """Получение всех задач пользователя"""
        conditions = [self._model_class.user_id == user_id]

        if not include_deleted:
            conditions.append(
                or_(
                    self._model_class.deleted.is_(False),
                    self._model_class.deleted.is_(None)
                )
            )

        stmt = select(self._model_class).where(and_(*conditions))
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_pending_sync(self, user_id: int) -> list[UserNotionTask]:
        """Получение задач, ожидающих синхронизации"""
        stmt = select(self._model_class).where(
            self._model_class.user_id == user_id,
            self._model_class.sync_status == SyncStatus.pending,
            self._model_class.deleted.is_(False)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_with_conflicts(self, user_id: int) -> list[UserNotionTask]:
        """Получение задач с конфликтами синхронизации"""
        stmt = select(self._model_class).where(
            self._model_class.user_id == user_id,
            self._model_class.has_conflict.is_(True)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    # ==================== Специфичные методы UPDATE ====================

    async def mark_synced(
        self,
        task_id: int,
        source: str,
        sync_status: SyncStatus = SyncStatus.synced
    ) -> bool:
        """Пометить задачу как синхронизированную"""
        return await self.update(task_id, {
            "sync_status": sync_status,
            "last_synced_at": datetime.now(UTC),
            "last_modified_source": source
        }) is not None

    async def mark_conflict(self, task_id: int) -> bool:
        """Пометить конфликт синхронизации"""
        return await self.update(task_id, {
            "has_conflict": True,
            "sync_status": SyncStatus.conflict
        }) is not None

    async def resolve_conflict(
        self,
        task_id: int,
        resolution: str  # "keep_local" | "keep_remote" | "merge"
    ) -> bool:
        """Разрешить конфликт"""
        return await self.update(task_id, {
            "has_conflict": False,
            "sync_status": SyncStatus.pending
        }) is not None

    # ==================== Sync-специфичные методы ====================

    async def upsert_from_notion(
        self,
        user_id: int,
        page_id: str,
        data: dict
    ) -> UserNotionTask:
        """Создать или обновить задачу из Notion"""
        existing = await self.get_by_notion_page_id(page_id)

        if existing:
            return await self.update(existing.id, {
                **data,
                "sync_source": "notion",
                "last_synced_at": datetime.now(UTC)
            })

        return await self.create({
            "user_id": user_id,
            "notion_page_id": page_id,
            **data,
            "sync_source": "notion",
            "last_synced_at": datetime.now(UTC)
        })
```

### 5.3 Использование в сервисе

```python
class NotionSyncService:
    def __init__(
        self,
        task_repository: TaskRepository,
        notion_adapter: NotionAdapter
    ):
        self._tasks = task_repository
        self._notion = notion_adapter

    async def sync_page(self, user_id: int, page_id: str) -> UserNotionTask:
        """Синхронизация одной страницы из Notion"""
        # Получаем данные из Notion
        notion_data = await self._notion.get_page(page_id)

        # Upsert через репозиторий
        task = await self._tasks.upsert_from_notion(
            user_id=user_id,
            page_id=page_id,
            data={
                "title": notion_data.title,
                "description": notion_data.description,
                "start_date": notion_data.start_date,
                "end_date": notion_data.end_date,
                "status": notion_data.status,
                "priority": notion_data.priority,
                "done": notion_data.done
            }
        )

        return task
```

---

## 6. Как разделить бизнес-логику и работу с БД

### 6.1 Принцип разделения

```
┌─────────────────────────────────────────────────────────────────┐
│                     API / Controllers                            │
│   (FastAPI routers — только HTTP, валидация, авторизация)       │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Application Services                          │
│   (Координация, оркестрация, бизнес-процессы)                   │
│   UserService, NotionSyncService, CalDavSyncService             │
└─────────────────────┬───────────────────────────────────────────┘
                      │
          ┌───────────┼───────────┐
          ▼           ▼           ▼
┌─────────────┐ ┌──────────┐ ┌─────────────┐
│  Domain     │ │Repositories│ │  Adapters   │
│  Services   │ │(БД)       │ │(внешние API)│
│             │ │           │ │             │
│ Conflict    │ │ User      │ │ Notion      │
│ Resolver    │ │ Task      │ │ CalDav      │
└─────────────┘ │ Event     │ │ Email       │
                └───────────┘ └─────────────┘
```

### 6.2 Слои и их ответственности

| Слой                  | Ответственность                                        | Пример                              |
|-----------------------|--------------------------------------------------------|-------------------------------------|
| **API/Controllers**   | HTTP, валидация, авторизация, формирование ответов     | `auth.py`, `dashboard.py`           |
| **Application Service**| Оркестрация бизнес-процессов, транзакции              | `UserService`, `NotionSyncService`  |
| **Domain Service**    | Чистая бизнес-логика без зависимостей                  | `ConflictResolver`, `SyncValidator` |
| **Repository**        | CRUD и запросы к БД                                    | `TaskRepository`, `UserRepository`  |
| **Adapter**           | Интеграция с внешними системами                        | `NotionAdapter`, `CalDavAdapter`    |
| **Entity/Model**      | Структура данных + бизнес-правила                      | `TaskEntity`, `UserEntity`          |

### 6.3 Пример разделения: Создание задачи

**БЫЛО (смешение):**
```python
# В webhook_handler.py — и логика, и БД, и Notion
async def handle_page_created(self, db: AsyncSession, user: User, user_id: int, page_id: str):
    notion_client = get_notion_client(user.notion_integration.access_token)
    page = await notion_client.pages.retrieve(page_id=page_id)
    notion_page = NotionTask.from_notion(page)

    stmt = select(UserNotionTask).where(...)
    result = await db.execute(stmt)
    task = result.scalar_one_or_none()

    if task:
        return {"error": "Task already exists"}

    new_task = UserNotionTask(...)
    db.add(new_task)
    await db.commit()
```

**СТАЛО (разделение):**

```python
# 1. Adapter (работа с Notion API)
class NotionAdapter:
    async def get_page(self, page_id: str) -> NotionPageDTO:
        page = await self._client.pages.retrieve(page_id=page_id)
        return NotionPageDTO.from_notion(page)


# 2. Repository (работа с БД)
class TaskRepository:
    async def exists_by_notion_page_id(self, user_id: int, page_id: str) -> bool:
        stmt = select(UserNotionTask.id).where(
            UserNotionTask.user_id == user_id,
            UserNotionTask.notion_page_id == page_id
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def create_from_notion(self, user_id: int, page_id: str, data: dict) -> UserNotionTask:
        ...


# 3. Application Service (оркестрация)
class NotionSyncService:
    def __init__(
        self,
        task_repo: TaskRepository,
        notion_adapter: NotionAdapter,
        logger: Logger
    ):
        self._tasks = task_repo
        self._notion = notion_adapter
        self._logger = logger

    async def handle_page_created(self, user_id: int, page_id: str) -> TaskEntity | None:
        """Бизнес-логика создания задачи из Notion"""

        # Проверка через репозиторий
        if await self._tasks.exists_by_notion_page_id(user_id, page_id):
            self._logger.warning(f"Task already exists for page {page_id}")
            return None

        # Получение данных через адаптер
        notion_page = await self._notion.get_page(page_id)

        # Валидация бизнес-правил (можно вынести в Domain Service)
        if not notion_page.title:
            raise BusinessError("Task must have a title")

        # Создание через репозиторий
        task = await self._tasks.create_from_notion(
            user_id=user_id,
            page_id=page_id,
            data=notion_page.to_dict()
        )

        return task


# 4. Controller (только HTTP)
@router.post("/webhooks/notion")
async def notion_webhook(
    request: Request,
    sync_service: NotionSyncService = Depends(get_sync_service)
):
    data = await request.json()
    page_id = data["page"]["id"]
    user_id = get_user_id_from_webhook(data)

    try:
        task = await sync_service.handle_page_created(user_id, page_id)
        return {"status": "ok", "task_id": task.id if task else None}
    except BusinessError as e:
        raise HTTPException(400, str(e))
```

### 6.4 Где что находится

| Действие                                  | Где реализовано           |
|-------------------------------------------|---------------------------|
| Валидация HTTP-запроса                    | Controller (Pydantic)     |
| Авторизация                               | Controller (middleware)   |
| Проверка "существует ли уже?"             | Repository                |
| Получение данных из Notion                | Adapter                   |
| Проверка бизнес-правил ("нужен title")    | Domain Service / Entity   |
| Логирование                               | Application Service       |
| Создание записи в БД                      | Repository                |
| Формирование HTTP-ответа                  | Controller                |

---

## 7. Как построить архитектуру services / repositories / models

### 7.1 Рекомендуемая структура директорий

```
server/
├── app/
│   ├── api/                      # HTTP Controllers (routers)
│   │   ├── __init__.py
│   │   ├── auth.py               # AuthController
│   │   ├── dashboard.py          # DashboardController
│   │   ├── webhooks/
│   │   │   └── notion.py         # NotionWebhookController
│   │   └── errors/
│   │       └── handlers.py
│   │
│   ├── core/                     # Конфигурация приложения
│   │   ├── config.py
│   │   ├── logging.py
│   │   └── security.py
│   │
│   └── schemas/                  # Pydantic DTOs для API
│       ├── user.py               # UserCreateDTO, UserResponseDTO
│       ├── task.py               # TaskDTO, TaskCreateDTO
│       └── common.py             # PaginationDTO, ErrorDTO
│
├── domain/                       # Бизнес-логика (чистая, без зависимостей)
│   ├── entities/                 # Сущности предметной области
│   │   ├── __init__.py
│   │   ├── user.py               # UserEntity
│   │   ├── task.py               # TaskEntity
│   │   └── event.py              # CalDavEventEntity
│   │
│   ├── value_objects/            # Неизменяемые объекты-значения
│   │   ├── email.py              # Email
│   │   ├── date_range.py         # DateRange
│   │   └── sync_status.py        # SyncStatus (Enum)
│   │
│   ├── services/                 # Доменные сервисы (чистая логика)
│   │   ├── conflict_resolver.py  # ConflictResolver
│   │   └── sync_validator.py     # SyncValidator
│   │
│   └── exceptions.py             # Бизнес-исключения
│
├── infrastructure/               # Инфраструктура (БД, кэш, внешние системы)
│   ├── database/
│   │   ├── __init__.py
│   │   ├── session.py            # AsyncSession factory
│   │   ├── base.py               # Base SQLAlchemy model
│   │   └── models/               # SQLAlchemy ORM models
│   │       ├── user.py           # User (ORM)
│   │       ├── task.py           # UserNotionTask (ORM)
│   │       └── event.py          # CalDavEvent (ORM)
│   │
│   ├── repositories/             # Реализации репозиториев
│   │   ├── __init__.py
│   │   ├── base.py               # BaseRepository[T]
│   │   ├── user_repository.py    # UserRepository
│   │   ├── task_repository.py    # TaskRepository
│   │   └── event_repository.py   # CalDavEventRepository
│   │
│   ├── cache/
│   │   └── redis.py              # RedisCache
│   │
│   └── adapters/                 # Адаптеры для внешних систем
│       ├── notion/
│       │   ├── client.py         # NotionClient
│       │   └── adapter.py        # NotionAdapter
│       │
│       ├── caldav/
│       │   ├── client.py         # CalDavClient
│       │   └── adapter.py        # CalDavAdapter
│       │
│       └── email/
│           └── smtp_adapter.py   # SmtpEmailAdapter
│
├── services/                     # Application Services (координация)
│   ├── __init__.py
│   ├── auth_service.py           # AuthService
│   ├── user_service.py           # UserService
│   ├── sync/
│   │   ├── notion_sync.py        # NotionSyncService
│   │   ├── caldav_sync.py        # CalDavSyncService
│   │   └── bidirectional.py      # BidirectionalSyncService
│   │
│   └── scheduler/
│       └── sync_scheduler.py     # SyncSchedulerService
│
├── utils/                        # Утилиты
│   ├── decorators.py
│   └── helpers.py
│
└── dependencies/                 # Dependency Injection
    ├── __init__.py
    └── containers.py             # DI Container
```

### 7.2 Принципы построения

#### 7.2.1 Направление зависимостей (Dependency Rule)

```
Controllers → Services → Repositories/Adapters
                ↓
             Domain
```

- **Domain** — не зависит ни от чего
- **Repositories/Adapters** — зависят только от Domain
- **Services** — зависят от Domain, Repositories, Adapters
- **Controllers** — зависят от Services, Schemas

#### 7.2.2 Dependency Injection

```python
# dependencies/containers.py
from functools import lru_cache

class Container:
    @staticmethod
    @lru_cache
    def get_task_repository(session: AsyncSession) -> TaskRepository:
        return TaskRepository(session)

    @staticmethod
    @lru_cache
    def get_notion_adapter(access_token: str) -> NotionAdapter:
        client = NotionClient(access_token)
        return NotionAdapter(client)

    @staticmethod
    def get_notion_sync_service(
        session: AsyncSession,
        access_token: str
    ) -> NotionSyncService:
        return NotionSyncService(
            task_repository=Container.get_task_repository(session),
            notion_adapter=Container.get_notion_adapter(access_token)
        )


# В FastAPI endpoint
@router.post("/sync")
async def sync_tasks(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    service = Container.get_notion_sync_service(
        session=db,
        access_token=user.notion_integration.access_token
    )
    result = await service.sync_all(user.id)
    return result
```

### 7.3 Пример полного flow

#### Синхронизация задачи из Notion:

```
1. Controller получает webhook
   ↓
2. Controller вызывает NotionSyncService.handle_webhook()
   ↓
3. NotionSyncService:
   a. Через NotionAdapter получает данные страницы
   b. Через TaskRepository проверяет существование
   c. Через ConflictResolver (Domain Service) разрешает конфликты
   d. Через TaskRepository создаёт/обновляет
   ↓
4. Controller формирует ответ
```

```python
# 1. Controller
@router.post("/webhooks/notion")
async def notion_webhook(
    request: Request,
    sync_service: NotionSyncService = Depends(get_sync_service)
):
    payload = await request.json()
    event_type = payload.get("type")
    page_id = payload.get("page", {}).get("id")

    if event_type == "page.created":
        result = await sync_service.handle_page_created(page_id)
    elif event_type == "page.updated":
        result = await sync_service.handle_page_updated(page_id)

    return {"status": "processed", "result": result}


# 2. Application Service
class NotionSyncService:
    def __init__(
        self,
        task_repo: TaskRepository,
        notion_adapter: NotionAdapter,
        conflict_resolver: ConflictResolver
    ):
        self._tasks = task_repo
        self._notion = notion_adapter
        self._resolver = conflict_resolver

    async def handle_page_created(self, user_id: int, page_id: str) -> dict:
        # Получаем данные из Notion
        notion_page = await self._notion.get_page(page_id)

        # Проверяем существование
        existing = await self._tasks.get_by_notion_page_id(page_id)
        if existing:
            return {"status": "skipped", "reason": "already_exists"}

        # Создаём задачу
        task = await self._tasks.create(
            user_id=user_id,
            notion_page_id=page_id,
            title=notion_page.title,
            description=notion_page.description,
            start_date=notion_page.start_date,
            end_date=notion_page.end_date,
            sync_source="notion"
        )

        return {"status": "created", "task_id": task.id}


# 3. Repository
class TaskRepository(BaseRepository[UserNotionTask]):
    async def get_by_notion_page_id(self, page_id: str) -> UserNotionTask | None:
        stmt = select(self._model).where(
            self._model.notion_page_id == page_id
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()


# 4. Adapter
class NotionAdapter:
    def __init__(self, client: AsyncClient):
        self._client = client

    async def get_page(self, page_id: str) -> NotionPageDTO:
        raw = await self._client.pages.retrieve(page_id=page_id)
        return NotionPageDTO.from_notion(raw)
```

---

## Заключение

### Ключевые принципы перехода на ООП:

1. **Разделяй ответственности**: Каждый класс делает одно дело
2. **Используй Dependency Injection**: Передавай зависимости в `__init__`
3. **Repository Pattern**: Инкапсулируй работу с БД
4. **Adapter Pattern**: Инкапсулируй работу с внешними API
5. **Service Layer**: Оркестрируй бизнес-процессы
6. **Domain Layer**: Держи бизнес-логику чистой от инфраструктуры

### Рекомендуемый порядок рефакторинга:

1. ✅ Создать `BaseRepository` с CRUD-операциями
2. ✅ Перенести `server/services/crud/users.py` в `UserRepository`
3. ✅ Рефакторить `NotionTaskRepository` — убрать Notion API
4. ✅ Создать `NotionAdapter` для работы с API
5. ✅ Создать `NotionSyncService` для оркестрации
6. ✅ Повторить для CalDAV

### Преимущества после рефакторинга:

- **Тестируемость**: Легко мокать репозитории и адаптеры
- **Читаемость**: Понятно, что где находится
- **Расширяемость**: Легко добавлять новые интеграции
- **Поддержка**: Изменения в одном месте не ломают другие
