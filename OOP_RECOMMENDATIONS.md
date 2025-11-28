# Рекомендации по рефакторингу на ООП

Этот документ содержит рекомендации по улучшению архитектуры проекта Calnio с использованием принципов объектно-ориентированного программирования (ООП). Основная цель — сделать код более модульным, читаемым и легко расширяемым.

---

## Оглавление

1. [Паттерн Base Repository](#1-паттерн-base-repository)
2. [UserRepository — Работа с пользователями](#2-userrepository--работа-с-пользователями)
3. [NotionTaskRepository — Улучшение](#3-notiontaskrepository--улучшение)
4. [CalDavEventRepository — Новый класс](#4-caldaveventrepository--новый-класс)
5. [CalendarRepository — Работа с календарями](#5-calendarrepository--работа-с-календарями)
6. [SyncService — Унификация синхронизации](#6-syncservice--унификация-синхронизации)
7. [BaseModel для схем (Pydantic)](#7-basemodel-для-схем-pydantic)
8. [Service Layer Pattern](#8-service-layer-pattern)
9. [Дополнительные рекомендации](#9-дополнительные-рекомендации)

---

## 1. Паттерн Base Repository

### Проблема
В текущем коде функции CRUD разбросаны по разным файлам (`server/services/crud/users.py`, `server/db/repositories/notion_tasks.py`) и используют разные подходы — где-то функции, где-то классы.

### Решение
Создать абстрактный базовый класс `BaseRepository` с общими методами CRUD:

### Файл: `server/db/repositories/base.py`

```python
from abc import ABC, abstractmethod
from typing import TypeVar, Generic, List, Optional, Type
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from server.db.database import Base

ModelType = TypeVar("ModelType", bound=Base)

class BaseRepository(ABC, Generic[ModelType]):
    """
    Абстрактный базовый репозиторий с общими CRUD-операциями.
    
    Атрибуты:
        model (Type[ModelType]): SQLAlchemy модель для работы с таблицей
        session (AsyncSession): Сессия базы данных
    """
    
    model: Type[ModelType]
    
    def __init__(self, session: AsyncSession):
        """
        Инициализация репозитория.
        
        Args:
            session: Асинхронная сессия SQLAlchemy
        """
        self.session = session
    
    # ==================== CREATE ====================
    async def create(self, **kwargs) -> ModelType:
        """
        Создать новую запись.
        
        Args:
            **kwargs: Атрибуты новой записи
            
        Returns:
            ModelType: Созданный объект
        """
        instance = self.model(**kwargs)
        self.session.add(instance)
        await self.session.commit()
        await self.session.refresh(instance)
        return instance
    
    # ==================== READ ====================
    async def get_by_id(self, id: int) -> Optional[ModelType]:
        """
        Получить запись по ID.
        
        Args:
            id: Идентификатор записи
            
        Returns:
            Optional[ModelType]: Найденная запись или None
        """
        stmt = select(self.model).where(self.model.id == id)
        result = await self.session.execute(stmt)
        return result.scalars().first()
    
    async def get_all(self, limit: int = 100, offset: int = 0) -> List[ModelType]:
        """
        Получить все записи с пагинацией.
        
        Args:
            limit: Максимальное количество записей
            offset: Смещение
            
        Returns:
            List[ModelType]: Список записей
        """
        stmt = select(self.model).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def get_by_filter(self, **filters) -> List[ModelType]:
        """
        Получить записи по фильтрам.
        
        Args:
            **filters: Условия фильтрации (field=value)
            
        Returns:
            List[ModelType]: Найденные записи
        """
        stmt = select(self.model)
        for field, value in filters.items():
            stmt = stmt.where(getattr(self.model, field) == value)
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def get_one_by_filter(self, **filters) -> Optional[ModelType]:
        """
        Получить одну запись по фильтрам.
        
        Args:
            **filters: Условия фильтрации
            
        Returns:
            Optional[ModelType]: Найденная запись или None
        """
        results = await self.get_by_filter(**filters)
        return results[0] if results else None
    
    # ==================== UPDATE ====================
    async def update(self, id: int, **kwargs) -> Optional[ModelType]:
        """
        Обновить запись по ID.
        
        Args:
            id: Идентификатор записи
            **kwargs: Новые значения атрибутов
            
        Returns:
            Optional[ModelType]: Обновлённая запись или None
        """
        instance = await self.get_by_id(id)
        if not instance:
            return None
        for key, value in kwargs.items():
            if hasattr(instance, key):
                setattr(instance, key, value)
        await self.session.commit()
        await self.session.refresh(instance)
        return instance
    
    # ==================== DELETE ====================
    async def delete(self, id: int) -> bool:
        """
        Удалить запись по ID.
        
        Args:
            id: Идентификатор записи
            
        Returns:
            bool: True если запись удалена, False если не найдена
        """
        instance = await self.get_by_id(id)
        if not instance:
            return False
        await self.session.delete(instance)
        await self.session.commit()
        return True
    
    async def soft_delete(self, id: int) -> bool:
        """
        Мягкое удаление (пометить deleted=True).
        
        Args:
            id: Идентификатор записи
            
        Returns:
            bool: True если запись помечена как удалённая
        """
        from datetime import datetime, timezone
        return await self.update(id, deleted=True, deleted_at=datetime.now(timezone.utc)) is not None
    
    # ==================== HELPERS ====================
    async def exists(self, id: int) -> bool:
        """
        Проверить существование записи.
        
        Args:
            id: Идентификатор записи
            
        Returns:
            bool: True если запись существует
        """
        return await self.get_by_id(id) is not None
    
    async def count(self, **filters) -> int:
        """
        Подсчитать количество записей.
        
        Args:
            **filters: Условия фильтрации
            
        Returns:
            int: Количество записей
        """
        from sqlalchemy import func
        stmt = select(func.count(self.model.id))
        for field, value in filters.items():
            stmt = stmt.where(getattr(self.model, field) == value)
        result = await self.session.execute(stmt)
        return result.scalar() or 0
```

---

## 2. UserRepository — Работа с пользователями

### Проблема
В `server/services/crud/users.py` находятся обычные функции (не класс). Это затрудняет расширение и тестирование.

### Решение
Создать класс `UserRepository`, наследующий от `BaseRepository`:

### Файл: `server/db/repositories/user.py`

```python
from typing import Optional, List
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from server.db.repositories.base import BaseRepository
from server.db.models.users import User
from server.app.schemas.users import UserCreate
from server.utils.security.utils import create_hash


class UserRepository(BaseRepository[User]):
    """
    Репозиторий для работы с пользователями.
    
    Расширяет BaseRepository специфичными для User методами.
    
    Атрибуты:
        model: User — SQLAlchemy модель пользователя
    """
    
    model = User
    
    def __init__(self, session: AsyncSession):
        """
        Args:
            session: Асинхронная сессия SQLAlchemy
        """
        super().__init__(session)
    
    # ==================== СПЕЦИФИЧНЫЕ МЕТОДЫ ====================
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """
        Найти пользователя по email.
        
        Args:
            email: Email пользователя
            
        Returns:
            Optional[User]: Пользователь или None
        """
        stmt = select(User).where(User.email == email)
        result = await self.session.execute(stmt)
        return result.scalars().first()
    
    async def get_by_username(self, username: str) -> Optional[User]:
        """
        Найти пользователя по username.
        
        Args:
            username: Имя пользователя
            
        Returns:
            Optional[User]: Пользователь или None
        """
        stmt = select(User).where(User.username == username)
        result = await self.session.execute(stmt)
        return result.scalars().first()
    
    async def get_by_login(self, login: str) -> Optional[User]:
        """
        Найти пользователя по email ИЛИ username.
        
        Args:
            login: Email или username
            
        Returns:
            Optional[User]: Пользователь или None
        """
        stmt = select(User).where(
            or_(User.email == login, User.username == login)
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()
    
    async def create_user(self, user_data: UserCreate) -> User:
        """
        Создать нового пользователя.
        
        Args:
            user_data: Данные для создания пользователя (Pydantic схема)
            
        Returns:
            User: Созданный пользователь
            
        Raises:
            ValueError: Если пользователь с таким email/username уже существует
        """
        # Проверка на существующего пользователя
        existing = await self.get_by_login(user_data.email)
        if not existing:
            existing = await self.get_by_username(user_data.username)
        
        if existing:
            raise ValueError(
                f"Пользователь с email '{user_data.email}' или username '{user_data.username}' уже существует."
            )
        
        return await self.create(
            email=user_data.email,
            username=user_data.username,
            hashed_password=user_data.hashed_password,
            is_superuser=user_data.is_superuser
        )
    
    async def update_password(self, user_id: int, new_password: str) -> Optional[User]:
        """
        Обновить пароль пользователя.
        
        Args:
            user_id: ID пользователя
            new_password: Новый пароль (не хешированный)
            
        Returns:
            Optional[User]: Обновлённый пользователь или None
        """
        hashed = create_hash(new_password)
        return await self.update(user_id, hashed_password=hashed)
    
    async def update_icloud_credentials(
        self, 
        user_id: int, 
        icloud_email: str, 
        app_specific_password: str
    ) -> Optional[User]:
        """
        Обновить iCloud учётные данные.
        
        Args:
            user_id: ID пользователя
            icloud_email: Email iCloud
            app_specific_password: Пароль приложения
            
        Returns:
            Optional[User]: Обновлённый пользователь
        """
        return await self.update(
            user_id,
            icloud_email=icloud_email,
            app_specific_password=app_specific_password
        )
    
    async def get_active_sync_users(self) -> List[User]:
        """
        Получить всех пользователей с активной синхронизацией.
        
        Returns:
            List[User]: Пользователи с active_sync=True и настроенным iCloud
        """
        stmt = select(User).where(
            User.active_sync.is_(True),
            User.icloud_email.is_not(None),
            User.app_specific_password.is_not(None)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def toggle_active_sync(self, user_id: int, enabled: bool) -> Optional[User]:
        """
        Переключить статус активной синхронизации.
        
        Args:
            user_id: ID пользователя
            enabled: Включить/выключить
            
        Returns:
            Optional[User]: Обновлённый пользователь
        """
        return await self.update(user_id, active_sync=enabled)
```

---

## 3. NotionTaskRepository — Улучшение

### Проблема
Текущий `NotionTaskRepository` в `server/db/repositories/notion_tasks.py` уже использует класс, но:
- Не наследует от базового репозитория
- Содержит бизнес-логику вперемешку с доступом к данным
- Сам управляет сессиями через `async_get_db_cm()`

### Решение
Рефакторить с наследованием от `BaseRepository`:

### Файл: `server/db/repositories/notion_tasks.py`

```python
from datetime import datetime, timezone
from typing import Optional, List

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from notion_client import AsyncClient

from server.db.repositories.base import BaseRepository
from server.db.models.tasks import UserNotionTask
from server.app.schemas.notion_pages import NotionTask
from server.utils.notion.utils import normalize_notion_id, to_utc_datetime


class NotionTaskRepository(BaseRepository[UserNotionTask]):
    """
    Репозиторий для работы с Notion задачами в БД.
    
    Атрибуты:
        model: UserNotionTask — SQLAlchemy модель задачи
        user_id: ID пользователя для фильтрации
    """
    
    model = UserNotionTask
    
    def __init__(self, session: AsyncSession, user_id: Optional[int] = None):
        """
        Args:
            session: Асинхронная сессия SQLAlchemy
            user_id: ID пользователя (опционально)
        """
        super().__init__(session)
        self.user_id = user_id
    
    # ==================== СПЕЦИФИЧНЫЕ МЕТОДЫ ====================
    
    async def get_by_notion_page_id(self, page_id: str) -> Optional[UserNotionTask]:
        """
        Найти задачу по Notion page ID.
        
        Args:
            page_id: ID страницы в Notion
            
        Returns:
            Optional[UserNotionTask]: Найденная задача
        """
        normalized_id = normalize_notion_id(page_id)
        stmt = select(UserNotionTask).where(
            UserNotionTask.notion_page_id == normalized_id
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()
    
    async def get_user_tasks(
        self, 
        user_id: int,
        include_deleted: bool = False
    ) -> List[UserNotionTask]:
        """
        Получить все задачи пользователя.
        
        Args:
            user_id: ID пользователя
            include_deleted: Включать удалённые задачи
            
        Returns:
            List[UserNotionTask]: Список задач
        """
        stmt = select(UserNotionTask).where(UserNotionTask.user_id == user_id)
        if not include_deleted:
            stmt = stmt.where(UserNotionTask.deleted.is_(False))
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def upsert_from_notion(
        self,
        user_id: int,
        notion_data: dict,
        sync_source: str = "notion"
    ) -> UserNotionTask:
        """
        Создать или обновить задачу из данных Notion.
        
        Args:
            user_id: ID пользователя
            notion_data: Данные страницы из Notion API
            sync_source: Источник синхронизации
            
        Returns:
            UserNotionTask: Созданная или обновлённая задача
        """
        notion_task = NotionTask.from_notion(notion_data)
        page_id_normalized = normalize_notion_id(notion_task.notion_page_id)
        
        existing = await self.get_by_notion_page_id(page_id_normalized)
        
        task_data = {
            "user_id": user_id,
            "notion_page_id": page_id_normalized,
            "notion_url": notion_task.notion_page_url,
            "title": notion_task.title,
            "description": notion_task.description,
            "start_date": to_utc_datetime(notion_task.start_date),
            "end_date": to_utc_datetime(notion_task.end_date),
            "status": notion_task.status,
            "done": notion_task.done,
            "priority": notion_task.priority,
            "select_option": notion_task.select_option,
            "sync_source": sync_source,
            "last_synced_at": datetime.now(timezone.utc),
            "last_modified_source": sync_source
        }
        
        if existing:
            return await self.update(existing.id, **task_data)
        else:
            return await self.create(**task_data)
    
    async def sync_deleted_tasks(
        self,
        user_id: int,
        current_notion_page_ids: List[str]
    ) -> List[str]:
        """
        Пометить как удалённые задачи, которых нет в Notion.
        
        Args:
            user_id: ID пользователя
            current_notion_page_ids: Текущие ID страниц в Notion
            
        Returns:
            List[str]: Список ID удалённых задач
        """
        # Нормализуем ID
        normalized_ids = [normalize_notion_id(pid) for pid in current_notion_page_ids]
        
        # Получаем все задачи пользователя
        user_tasks = await self.get_user_tasks(user_id)
        
        deleted_ids = []
        for task in user_tasks:
            if task.notion_page_id not in normalized_ids:
                await self.soft_delete(task.id)
                deleted_ids.append(task.notion_page_id)
        
        return deleted_ids
    
    async def get_by_caldav_id(self, caldav_id: str) -> Optional[UserNotionTask]:
        """
        Найти задачу по CalDAV ID.
        
        Args:
            caldav_id: UID события в CalDAV
            
        Returns:
            Optional[UserNotionTask]: Найденная задача
        """
        stmt = select(UserNotionTask).where(
            UserNotionTask.caldav_id == caldav_id
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()
    
    async def get_tasks_for_sync(self, user_id: int) -> List[UserNotionTask]:
        """
        Получить задачи для синхронизации с CalDAV.
        
        Возвращает задачи с заполненными датами начала и окончания.
        
        Args:
            user_id: ID пользователя
            
        Returns:
            List[UserNotionTask]: Задачи для синхронизации
        """
        stmt = select(UserNotionTask).where(
            UserNotionTask.user_id == user_id,
            UserNotionTask.start_date.is_not(None),
            UserNotionTask.end_date.is_not(None),
            UserNotionTask.deleted.is_(False)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()
```

---

## 4. CalDavEventRepository — Новый класс

### Проблема
В `server/db/repositories/caldav_events.py` есть класс `CaldavEventsRepository`, но он:
- Смешивает работу с БД и внешним CalDAV сервером
- Не наследует от базового репозитория
- Содержит много дублированного кода

### Решение
Разделить на два класса:
1. `CalDavEventRepository` — работа с БД
2. `CalDavClient` — работа с внешним CalDAV сервером

### Файл: `server/db/repositories/caldav_events.py`

```python
from datetime import datetime, timezone
from typing import Optional, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from server.db.repositories.base import BaseRepository
from server.db.models.caldav_events import CalDavEvent


class CalDavEventRepository(BaseRepository[CalDavEvent]):
    """
    Репозиторий для работы с CalDAV событиями в БД.
    
    Атрибуты:
        model: CalDavEvent — SQLAlchemy модель события
    """
    
    model = CalDavEvent
    
    def __init__(self, session: AsyncSession):
        """
        Args:
            session: Асинхронная сессия SQLAlchemy
        """
        super().__init__(session)
    
    # ==================== СПЕЦИФИЧНЫЕ МЕТОДЫ ====================
    
    async def get_by_caldav_uid(
        self, 
        user_id: int, 
        caldav_uid: str
    ) -> Optional[CalDavEvent]:
        """
        Найти событие по CalDAV UID.
        
        Args:
            user_id: ID пользователя
            caldav_uid: UID события в CalDAV
            
        Returns:
            Optional[CalDavEvent]: Найденное событие
        """
        stmt = select(CalDavEvent).where(
            CalDavEvent.user_id == user_id,
            CalDavEvent.caldav_uid == caldav_uid
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()
    
    async def get_user_events(
        self, 
        user_id: int,
        include_deleted: bool = False
    ) -> List[CalDavEvent]:
        """
        Получить все события пользователя.
        
        Args:
            user_id: ID пользователя
            include_deleted: Включать удалённые события
            
        Returns:
            List[CalDavEvent]: Список событий
        """
        stmt = select(CalDavEvent).where(CalDavEvent.user_id == user_id)
        if not include_deleted:
            stmt = stmt.where(CalDavEvent.deleted.is_(False))
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def get_user_event_uids(self, user_id: int) -> List[str]:
        """
        Получить список UID событий пользователя.
        
        Args:
            user_id: ID пользователя
            
        Returns:
            List[str]: Список CalDAV UID
        """
        stmt = select(CalDavEvent.caldav_uid).where(
            CalDavEvent.user_id == user_id
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def upsert_event(
        self,
        user_id: int,
        caldav_uid: str,
        title: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        description: Optional[str] = None,
        caldav_url: Optional[str] = None,
        sync_source: str = "caldav"
    ) -> CalDavEvent:
        """
        Создать или обновить событие.
        
        Args:
            user_id: ID пользователя
            caldav_uid: UID события
            title: Заголовок
            start_time: Время начала
            end_time: Время окончания
            description: Описание
            caldav_url: URL события в CalDAV
            sync_source: Источник синхронизации
            
        Returns:
            CalDavEvent: Созданное или обновлённое событие
        """
        existing = await self.get_by_caldav_uid(user_id, caldav_uid)
        
        event_data = {
            "user_id": user_id,
            "caldav_uid": caldav_uid,
            "title": title,
            "description": description,
            "start_time": start_time,
            "end_time": end_time,
            "caldav_url": caldav_url,
            "sync_source": sync_source,
            "last_synced_at": datetime.now(timezone.utc)
        }
        
        if existing:
            return await self.update(existing.id, **event_data)
        else:
            return await self.create(**event_data)
    
    async def sync_deleted_events(
        self,
        user_id: int,
        current_caldav_uids: List[str]
    ) -> List[str]:
        """
        Пометить как удалённые события, которых нет в CalDAV.
        
        Args:
            user_id: ID пользователя
            current_caldav_uids: Текущие UID событий в CalDAV
            
        Returns:
            List[str]: Список UID удалённых событий
        """
        user_events = await self.get_user_events(user_id)
        
        deleted_uids = []
        for event in user_events:
            if event.caldav_uid not in current_caldav_uids:
                await self.soft_delete(event.id)
                deleted_uids.append(event.caldav_uid)
        
        return deleted_uids
    
    async def get_events_by_notion_page_id(
        self, 
        notion_page_id: str
    ) -> List[CalDavEvent]:
        """
        Найти события по Notion page ID.
        
        Args:
            notion_page_id: ID страницы Notion
            
        Returns:
            List[CalDavEvent]: Найденные события
        """
        stmt = select(CalDavEvent).where(
            CalDavEvent.notion_page_id == notion_page_id
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()
```

---

## 5. CalendarRepository — Работа с календарями

### Проблема
Сейчас нет отдельного репозитория для работы с календарями в БД. Логика размазана по `user_calendars.py`.

### Решение
Создать `CalendarRepository`:

### Файл: `server/db/repositories/calendar.py`

```python
from typing import Optional, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from server.db.repositories.base import BaseRepository
from server.db.models.calendars import Calendar


class CalendarRepository(BaseRepository[Calendar]):
    """
    Репозиторий для работы с календарями в БД.
    
    Атрибуты:
        model: Calendar — SQLAlchemy модель календаря
    """
    
    model = Calendar
    
    def __init__(self, session: AsyncSession):
        """
        Args:
            session: Асинхронная сессия SQLAlchemy
        """
        super().__init__(session)
    
    # ==================== СПЕЦИФИЧНЫЕ МЕТОДЫ ====================
    
    async def get_by_uid(
        self, 
        user_id: int, 
        uid: str
    ) -> Optional[Calendar]:
        """
        Найти календарь по UID.
        
        Args:
            user_id: ID пользователя
            uid: UID календаря
            
        Returns:
            Optional[Calendar]: Найденный календарь
        """
        stmt = select(Calendar).where(
            Calendar.user_id == user_id,
            Calendar.uid == uid
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()
    
    async def get_by_name(
        self, 
        user_id: int, 
        name: str
    ) -> Optional[Calendar]:
        """
        Найти календарь по имени.
        
        Args:
            user_id: ID пользователя
            name: Имя календаря
            
        Returns:
            Optional[Calendar]: Найденный календарь
        """
        stmt = select(Calendar).where(
            Calendar.user_id == user_id,
            Calendar.name == name
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()
    
    async def get_user_calendars(self, user_id: int) -> List[Calendar]:
        """
        Получить все календари пользователя.
        
        Args:
            user_id: ID пользователя
            
        Returns:
            List[Calendar]: Список календарей
        """
        stmt = select(Calendar).where(Calendar.user_id == user_id)
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def upsert_calendar(
        self,
        user_id: int,
        uid: str,
        name: Optional[str] = None,
        url: Optional[str] = None,
        color: Optional[str] = None
    ) -> Calendar:
        """
        Создать или обновить календарь.
        
        Args:
            user_id: ID пользователя
            uid: UID календаря
            name: Имя календаря
            url: URL календаря
            color: Цвет
            
        Returns:
            Calendar: Созданный или обновлённый календарь
        """
        existing = await self.get_by_uid(user_id, uid)
        
        calendar_data = {
            "user_id": user_id,
            "uid": uid,
            "name": name,
            "url": url,
            "color": color
        }
        
        if existing:
            return await self.update(existing.id, **calendar_data)
        else:
            return await self.create(**calendar_data)
```

---

## 6. SyncService — Унификация синхронизации

### Проблема
Текущий `SyncService` в `server/services/sync/sync_manager.py`:
- Напрямую работает с ORM и репозиториями
- Содержит много дублированного кода
- Сложно расширять для новых источников

### Решение
Создать базовый `BaseSyncService` и конкретные реализации:

### Файл: `server/services/sync/base.py`

```python
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum


class SyncDirection(Enum):
    """Направление синхронизации."""
    SOURCE_TO_TARGET = "source_to_target"
    TARGET_TO_SOURCE = "target_to_source"
    BIDIRECTIONAL = "bidirectional"


@dataclass
class SyncResult:
    """Результат синхронизации."""
    created: int = 0
    updated: int = 0
    deleted: int = 0
    errors: List[str] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []


class BaseSyncService(ABC):
    """
    Абстрактный базовый класс для сервисов синхронизации.
    
    Атрибуты:
        user_id: ID пользователя
        direction: Направление синхронизации
    """
    
    def __init__(self, user_id: int, direction: SyncDirection = SyncDirection.BIDIRECTIONAL):
        """
        Args:
            user_id: ID пользователя
            direction: Направление синхронизации
        """
        self.user_id = user_id
        self.direction = direction
    
    @abstractmethod
    async def fetch_source_items(self) -> List[Dict[str, Any]]:
        """
        Получить элементы из источника.
        
        Returns:
            List[Dict]: Элементы из источника
        """
        pass
    
    @abstractmethod
    async def fetch_target_items(self) -> List[Dict[str, Any]]:
        """
        Получить элементы из целевого хранилища.
        
        Returns:
            List[Dict]: Элементы из цели
        """
        pass
    
    @abstractmethod
    async def create_in_target(self, item: Dict[str, Any]) -> bool:
        """
        Создать элемент в целевом хранилище.
        
        Args:
            item: Данные элемента
            
        Returns:
            bool: Успешность операции
        """
        pass
    
    @abstractmethod
    async def update_in_target(self, item: Dict[str, Any]) -> bool:
        """
        Обновить элемент в целевом хранилище.
        
        Args:
            item: Данные элемента
            
        Returns:
            bool: Успешность операции
        """
        pass
    
    @abstractmethod
    async def delete_in_target(self, item_id: str) -> bool:
        """
        Удалить элемент из целевого хранилища.
        
        Args:
            item_id: ID элемента
            
        Returns:
            bool: Успешность операции
        """
        pass
    
    @abstractmethod
    def get_item_uid(self, item: Dict[str, Any]) -> str:
        """
        Получить уникальный идентификатор элемента.
        
        Args:
            item: Элемент
            
        Returns:
            str: UID элемента
        """
        pass
    
    @abstractmethod
    def items_are_equal(
        self, 
        source_item: Dict[str, Any], 
        target_item: Dict[str, Any]
    ) -> bool:
        """
        Сравнить два элемента на идентичность.
        
        Args:
            source_item: Элемент из источника
            target_item: Элемент из цели
            
        Returns:
            bool: True если элементы идентичны
        """
        pass
    
    async def sync(self) -> SyncResult:
        """
        Выполнить синхронизацию.
        
        Returns:
            SyncResult: Результат синхронизации
        """
        result = SyncResult()
        
        try:
            source_items = await self.fetch_source_items()
            target_items = await self.fetch_target_items()
            
            source_uids = {self.get_item_uid(item): item for item in source_items}
            target_uids = {self.get_item_uid(item): item for item in target_items}
            
            # Создать новые
            for uid, item in source_uids.items():
                if uid not in target_uids:
                    if await self.create_in_target(item):
                        result.created += 1
            
            # Обновить существующие
            for uid, source_item in source_uids.items():
                if uid in target_uids:
                    target_item = target_uids[uid]
                    if not self.items_are_equal(source_item, target_item):
                        if await self.update_in_target(source_item):
                            result.updated += 1
            
            # Удалить отсутствующие
            for uid in target_uids:
                if uid not in source_uids:
                    if await self.delete_in_target(uid):
                        result.deleted += 1
                        
        except Exception as e:
            result.errors.append(str(e))
        
        return result
```

### Файл: `server/services/sync/caldav_sync.py`

```python
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from server.services.sync.base import BaseSyncService, SyncDirection
from server.db.repositories.caldav_events import CalDavEventRepository
from server.db.repositories.notion_tasks import NotionTaskRepository
from server.services.caldav.caldav_orm import CalDavORM
from server.utils.utils import extract_uid, ensure_datetime_with_tz


class CalDavToDbSyncService(BaseSyncService):
    """
    Сервис синхронизации CalDAV → БД.
    
    Атрибуты:
        session: Сессия БД
        caldav_orm: ORM для работы с CalDAV
        calendar_name: Имя календаря для синхронизации
    """
    
    def __init__(
        self, 
        user_id: int, 
        session: AsyncSession,
        calendar_name: str = "Personal"
    ):
        """
        Args:
            user_id: ID пользователя
            session: Сессия БД
            calendar_name: Имя календаря
        """
        super().__init__(user_id, SyncDirection.SOURCE_TO_TARGET)
        self.session = session
        self.calendar_name = calendar_name
        self.caldav_orm = CalDavORM(user_id=user_id)
        self.event_repo = CalDavEventRepository(session)
        self._calendar = None
    
    async def _ensure_authenticated(self):
        """Убедиться, что CalDAV клиент авторизован."""
        if not self.caldav_orm.client:
            await self.caldav_orm.authenticate()
            self._calendar = await self.caldav_orm.Calendar.get_by_name(self.calendar_name)
    
    async def fetch_source_items(self) -> List[Dict[str, Any]]:
        """Получить события из CalDAV."""
        await self._ensure_authenticated()
        events = await self.caldav_orm.Event.all(
            calendar_uid=extract_uid(self._calendar.id)
        )
        return [
            {
                "uid": extract_uid(e.url),
                "title": e.title,
                "description": e.description,
                "start_time": ensure_datetime_with_tz(e.start),
                "end_time": ensure_datetime_with_tz(e.end),
                "url": str(e.url)
            }
            for e in events
        ]
    
    async def fetch_target_items(self) -> List[Dict[str, Any]]:
        """Получить события из БД."""
        events = await self.event_repo.get_user_events(self.user_id)
        return [
            {
                "uid": e.caldav_uid,
                "title": e.title,
                "description": e.description,
                "start_time": e.start_time,
                "end_time": e.end_time,
                "url": e.caldav_url
            }
            for e in events
        ]
    
    async def create_in_target(self, item: Dict[str, Any]) -> bool:
        """Создать событие в БД."""
        await self.event_repo.upsert_event(
            user_id=self.user_id,
            caldav_uid=item["uid"],
            title=item["title"],
            start_time=item.get("start_time"),
            end_time=item.get("end_time"),
            description=item.get("description"),
            caldav_url=item.get("url"),
            sync_source="caldav"
        )
        return True
    
    async def update_in_target(self, item: Dict[str, Any]) -> bool:
        """Обновить событие в БД."""
        return await self.create_in_target(item)  # upsert
    
    async def delete_in_target(self, item_id: str) -> bool:
        """Удалить событие из БД."""
        event = await self.event_repo.get_by_caldav_uid(self.user_id, item_id)
        if event:
            await self.event_repo.soft_delete(event.id)
            return True
        return False
    
    def get_item_uid(self, item: Dict[str, Any]) -> str:
        """Получить UID элемента."""
        return item["uid"]
    
    def items_are_equal(
        self, 
        source_item: Dict[str, Any], 
        target_item: Dict[str, Any]
    ) -> bool:
        """Сравнить два события."""
        return (
            source_item["title"] == target_item["title"] and
            source_item.get("description") == target_item.get("description") and
            source_item.get("start_time") == target_item.get("start_time") and
            source_item.get("end_time") == target_item.get("end_time")
        )
```

---

## 7. BaseModel для схем (Pydantic)

### Проблема
Pydantic схемы в `server/app/schemas/` не имеют общего базового класса с общими настройками.

### Решение
Создать базовую схему:

### Файл: `server/app/schemas/base.py`

```python
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class BaseSchema(BaseModel):
    """
    Базовая схема с общими настройками.
    
    Все схемы должны наследоваться от этого класса.
    """
    model_config = ConfigDict(
        from_attributes=True,  # Позволяет создавать из ORM моделей
        populate_by_name=True,  # Позволяет использовать alias
        validate_assignment=True,  # Валидация при присваивании
        str_strip_whitespace=True,  # Удаляет пробелы в строках
    )


class TimestampMixin(BaseModel):
    """Миксин для полей created_at и updated_at."""
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class SoftDeleteMixin(BaseModel):
    """Миксин для мягкого удаления."""
    deleted: bool = False
    deleted_at: Optional[datetime] = None


# Пример использования:
class TaskBase(BaseSchema, TimestampMixin, SoftDeleteMixin):
    """Базовая схема задачи."""
    title: str
    description: Optional[str] = None


class TaskCreate(TaskBase):
    """Схема для создания задачи."""
    user_id: int


class TaskUpdate(BaseSchema):
    """Схема для обновления задачи."""
    title: Optional[str] = None
    description: Optional[str] = None


class TaskResponse(TaskBase):
    """Схема ответа для задачи."""
    id: int
    user_id: int
```

---

## 8. Service Layer Pattern

### Проблема
Бизнес-логика смешана с доступом к данным. Нет чёткого разделения между слоями.

### Решение
Ввести слой сервисов между API и репозиториями:

### Файл: `server/services/user_service.py`

```python
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from server.db.repositories.user import UserRepository
from server.db.models.users import User
from server.app.schemas.users import UserCreate
from server.utils.security.utils import verify_password, create_hash
from server.app.core.logging_config import logger


class UserService:
    """
    Сервис для работы с пользователями.
    
    Содержит бизнес-логику, связанную с пользователями.
    
    Атрибуты:
        repo: Репозиторий пользователей
    """
    
    def __init__(self, session: AsyncSession):
        """
        Args:
            session: Асинхронная сессия SQLAlchemy
        """
        self.repo = UserRepository(session)
    
    async def authenticate(
        self, 
        login: str, 
        password: str
    ) -> Optional[User]:
        """
        Аутентифицировать пользователя.
        
        Args:
            login: Email или username
            password: Пароль
            
        Returns:
            Optional[User]: Пользователь если аутентификация успешна
        """
        user = await self.repo.get_by_login(login)
        
        if not user:
            logger.debug(f"User not found: {login}")
            return None
        
        if not user.hashed_password:
            logger.debug(f"User has no password: {login}")
            return None
        
        if not verify_password(password, user.hashed_password):
            logger.debug(f"Invalid password for: {login}")
            return None
        
        return user
    
    async def register(self, user_data: UserCreate) -> User:
        """
        Зарегистрировать нового пользователя.
        
        Args:
            user_data: Данные пользователя
            
        Returns:
            User: Созданный пользователь
            
        Raises:
            ValueError: Если пользователь уже существует
        """
        # Хешируем пароль если ещё не захеширован
        if not user_data.hashed_password.startswith("$2b$"):
            user_data.hashed_password = create_hash(user_data.hashed_password)
        
        return await self.repo.create_user(user_data)
    
    async def get_by_id(self, user_id: int) -> Optional[User]:
        """
        Получить пользователя по ID.
        
        Args:
            user_id: ID пользователя
            
        Returns:
            Optional[User]: Пользователь
        """
        return await self.repo.get_by_id(user_id)
    
    async def update_profile(
        self,
        user_id: int,
        username: Optional[str] = None,
        email: Optional[str] = None
    ) -> Optional[User]:
        """
        Обновить профиль пользователя.
        
        Args:
            user_id: ID пользователя
            username: Новый username
            email: Новый email
            
        Returns:
            Optional[User]: Обновлённый пользователь
        """
        update_data = {}
        if username:
            update_data["username"] = username
        if email:
            update_data["email"] = email
        
        if not update_data:
            return await self.repo.get_by_id(user_id)
        
        return await self.repo.update(user_id, **update_data)
    
    async def change_password(
        self,
        user_id: int,
        old_password: str,
        new_password: str
    ) -> bool:
        """
        Сменить пароль пользователя.
        
        Args:
            user_id: ID пользователя
            old_password: Старый пароль
            new_password: Новый пароль
            
        Returns:
            bool: True если пароль успешно сменён
        """
        user = await self.repo.get_by_id(user_id)
        if not user or not user.hashed_password:
            return False
        
        if not verify_password(old_password, user.hashed_password):
            return False
        
        await self.repo.update_password(user_id, new_password)
        return True
```

---

## 9. Дополнительные рекомендации

### 9.1. Unit of Work Pattern

Для управления транзакциями рекомендуется использовать паттерн Unit of Work:

```python
from sqlalchemy.ext.asyncio import AsyncSession

class UnitOfWork:
    """
    Unit of Work для управления транзакциями.
    
    Использование:
        async with UnitOfWork(session) as uow:
            await uow.users.create(...)
            await uow.tasks.create(...)
            await uow.commit()
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self._users = None
        self._tasks = None
        self._events = None
    
    @property
    def users(self):
        if self._users is None:
            from server.db.repositories.user import UserRepository
            self._users = UserRepository(self.session)
        return self._users
    
    @property
    def tasks(self):
        if self._tasks is None:
            from server.db.repositories.notion_tasks import NotionTaskRepository
            self._tasks = NotionTaskRepository(self.session)
        return self._tasks
    
    @property
    def events(self):
        if self._events is None:
            from server.db.repositories.caldav_events import CalDavEventRepository
            self._events = CalDavEventRepository(self.session)
        return self._events
    
    async def commit(self):
        await self.session.commit()
    
    async def rollback(self):
        await self.session.rollback()
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            await self.rollback()
```

### 9.2. Dependency Injection

Использовать DI для инъекции зависимостей в FastAPI:

```python
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from server.db.deps import async_get_db
from server.services.user_service import UserService


def get_user_service(
    session: AsyncSession = Depends(async_get_db)
) -> UserService:
    return UserService(session)


# Использование в endpoint:
@router.get("/users/{user_id}")
async def get_user(
    user_id: int,
    user_service: UserService = Depends(get_user_service)
):
    return await user_service.get_by_id(user_id)
```

### 9.3. Структура папок после рефакторинга

```
server/
├── app/
│   ├── api/
│   │   ├── deps.py              # Зависимости FastAPI (DI)
│   │   ├── auth.py
│   │   └── dashboard.py
│   ├── schemas/
│   │   ├── base.py              # Базовые схемы Pydantic
│   │   ├── users.py
│   │   ├── tasks.py
│   │   └── events.py
│   └── core/
│       └── config.py
├── db/
│   ├── database.py
│   ├── deps.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── users.py
│   │   ├── tasks.py
│   │   └── caldav_events.py
│   └── repositories/
│       ├── __init__.py
│       ├── base.py              # Базовый репозиторий
│       ├── user.py              # UserRepository
│       ├── notion_tasks.py      # NotionTaskRepository
│       ├── caldav_events.py     # CalDavEventRepository
│       └── calendar.py          # CalendarRepository
├── services/
│   ├── __init__.py
│   ├── user_service.py          # Сервис пользователей
│   ├── task_service.py          # Сервис задач
│   ├── sync/
│   │   ├── base.py              # Базовый класс синхронизации
│   │   ├── caldav_sync.py       # Синхронизация CalDAV
│   │   └── notion_sync.py       # Синхронизация Notion
│   └── caldav/
│       ├── caldav_client.py     # Клиент CalDAV
│       └── caldav_orm.py        # ORM для CalDAV
└── utils/
    └── uow.py                   # Unit of Work
```

---

## Заключение

### Приоритет рефакторинга:

1. **Высокий приоритет:**
   - Создать `BaseRepository` (основа для всех репозиториев)
   - Рефакторить `UserRepository` (часто используется)
   - Улучшить `NotionTaskRepository`

2. **Средний приоритет:**
   - Создать `CalDavEventRepository`
   - Создать `CalendarRepository`
   - Ввести Service Layer

3. **Низкий приоритет:**
   - Рефакторить синхронизацию (`SyncService`)
   - Внедрить Unit of Work
   - Унифицировать схемы Pydantic

### Преимущества:

- **Модульность:** Каждый класс отвечает за одну сущность
- **Тестируемость:** Легко мокать репозитории в тестах
- **Расширяемость:** Просто добавлять новые методы
- **Повторное использование:** Базовые классы содержат общую логику
- **Читаемость:** Понятная структура кода
