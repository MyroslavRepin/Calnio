"""
Tests for the SyncService two-way CalDAV synchronization with LWW conflict resolution.
"""

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from types import SimpleNamespace

from server.services.sync.sync_manager import SyncService
from server.db.models.caldav_events import CalDavEvent
from server.db.models import UserNotionTask
from server.db.models.enums import SyncStatus


class TestGetLatestTimestamp:
    """Tests for the _get_latest_timestamp helper method."""
    
    def test_uses_updated_at_when_available(self):
        """Test that updated_at is used when available."""
        service = SyncService(user_id=1)
        
        now = datetime.now(timezone.utc)
        earlier = now - timedelta(hours=1)
        
        record = SimpleNamespace(updated_at=now, created_at=earlier)
        result = service._get_latest_timestamp(record)
        
        assert result == now
    
    def test_falls_back_to_created_at(self):
        """Test that created_at is used when updated_at is None."""
        service = SyncService(user_id=1)
        
        created = datetime.now(timezone.utc)
        record = SimpleNamespace(updated_at=None, created_at=created)
        result = service._get_latest_timestamp(record)
        
        assert result == created
    
    def test_handles_naive_datetime(self):
        """Test that naive datetimes are converted to UTC."""
        service = SyncService(user_id=1)
        
        naive_dt = datetime(2024, 1, 1, 12, 0, 0)
        record = SimpleNamespace(updated_at=naive_dt, created_at=None)
        result = service._get_latest_timestamp(record)
        
        assert result.tzinfo == timezone.utc
    
    def test_handles_missing_timestamps(self):
        """Test that current UTC time is used when both timestamps are None."""
        service = SyncService(user_id=1)
        
        record = SimpleNamespace(updated_at=None, created_at=None)
        before = datetime.now(timezone.utc)
        result = service._get_latest_timestamp(record)
        after = datetime.now(timezone.utc)
        
        assert before <= result <= after
        assert result.tzinfo == timezone.utc


@pytest.mark.asyncio
class TestSyncCalDavToDbLWW:
    """Tests for the sync_caldav_to_db method with LWW conflict resolution."""
    
    async def test_creates_new_local_event_from_remote(self):
        """Test that a remote event without local counterpart is created locally."""
        service = SyncService(user_id=1)
        
        # Mock database session
        mock_db = AsyncMock()
        mock_db.commit = AsyncMock()
        mock_db.rollback = AsyncMock()
        mock_db.add = MagicMock()
        
        # Mock execute results  
        mock_scalars = MagicMock()
        mock_scalars.all = MagicMock(return_value=[])  # No local events
        mock_scalars.first = MagicMock(return_value=None)  # No existing event
        
        mock_execute_result = MagicMock()
        mock_execute_result.scalars = MagicMock(return_value=mock_scalars)
        
        mock_db.execute = AsyncMock(return_value=mock_execute_result)
        
        # Mock CalDAV ORM
        mock_calendar = SimpleNamespace(id="cal123")
        service.caldav_orm.authenticate = AsyncMock()
        service.caldav_orm.Calendar.get_by_name = AsyncMock(return_value=mock_calendar)
        
        # Mock remote event
        remote_event = SimpleNamespace(
            uid="event123",
            url="https://caldav.example.com/event123",
            title="Test Event",
            description="Test Description",
            start=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            end=datetime(2024, 1, 1, 13, 0, 0, tzinfo=timezone.utc)
        )
        service.caldav_orm.Event.all = AsyncMock(return_value=[remote_event])
        
        # Mock repository methods
        service.repo.fetch_ical_event = AsyncMock(return_value="VCALENDAR...")
        service.repo.parse_ical_full = AsyncMock(return_value=[{
            "uid": "event123",
            "title": "Test Event",
            "description": "Test Description",
            "created": datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc),
            "last_modified": datetime(2024, 1, 1, 11, 0, 0, tzinfo=timezone.utc),
        }])
        
        # Run sync
        await service.sync_caldav_to_db(
            user_id=1,
            calendar_name="Personal",
            db=mock_db
        )
        
        # Verify new event was added
        assert mock_db.add.call_count >= 2  # CalDavEvent + UserNotionTask
        mock_db.commit.assert_called()
    
    async def test_lww_remote_newer_updates_local(self):
        """Test that when remote is newer, local is updated."""
        service = SyncService(user_id=1)
        
        # Mock database session
        mock_db = AsyncMock()
        mock_db.commit = AsyncMock()
        mock_db.rollback = AsyncMock()
        
        # Create mock local event (older timestamp)
        local_timestamp = datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
        mock_local_event = MagicMock(spec=CalDavEvent)
        mock_local_event.caldav_uid = "event123"
        mock_local_event.updated_at = local_timestamp
        mock_local_event.created_at = local_timestamp
        mock_local_event.title = "Old Title"
        
        # Mock execute for local events query - using side_effect for different queries
        def execute_side_effect(stmt):
            stmt_str = str(stmt)
            
            mock_scalars = MagicMock()
            if "caldav_events" in stmt_str and "SELECT" in stmt_str and "WHERE" in stmt_str and "user_id" in stmt_str:
                # First query: get all local events
                mock_scalars.all = MagicMock(return_value=[mock_local_event])
            else:
                # Other queries: notion tasks
                mock_scalars.first = MagicMock(return_value=None)
            
            mock_result = MagicMock()
            mock_result.scalars = MagicMock(return_value=mock_scalars)
            return mock_result
        
        mock_db.execute = AsyncMock(side_effect=execute_side_effect)
        
        # Mock CalDAV ORM
        mock_calendar = SimpleNamespace(id="cal123")
        service.caldav_orm.authenticate = AsyncMock()
        service.caldav_orm.Calendar.get_by_name = AsyncMock(return_value=mock_calendar)
        
        # Mock remote event (newer timestamp)
        remote_timestamp = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        remote_event = SimpleNamespace(
            uid="event123",
            url="https://caldav.example.com/event123",
            title="New Title",
            description="New Description",
            start=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            end=datetime(2024, 1, 1, 13, 0, 0, tzinfo=timezone.utc)
        )
        service.caldav_orm.Event.all = AsyncMock(return_value=[remote_event])
        
        # Mock repository methods
        service.repo.fetch_ical_event = AsyncMock(return_value="VCALENDAR...")
        service.repo.parse_ical_full = AsyncMock(return_value=[{
            "uid": "event123",
            "title": "New Title",
            "description": "New Description",
            "created": local_timestamp,
            "last_modified": remote_timestamp,
        }])
        
        # Run sync
        await service.sync_caldav_to_db(
            user_id=1,
            calendar_name="Personal",
            db=mock_db
        )
        
        # Verify local event was updated
        assert mock_local_event.title == "New Title"
        assert mock_local_event.description == "New Description"
        mock_db.commit.assert_called()
    
    async def test_handles_network_error_gracefully(self):
        """Test that network errors are handled gracefully with rollback."""
        service = SyncService(user_id=1)
        
        # Mock database session
        mock_db = AsyncMock()
        mock_db.commit = AsyncMock()
        mock_db.rollback = AsyncMock()
        
        # Mock CalDAV ORM to raise network error
        service.caldav_orm.authenticate = AsyncMock()
        service.caldav_orm.Calendar.get_by_name = AsyncMock(
            side_effect=Exception("Network timeout")
        )
        
        # Run sync and expect exception
        with pytest.raises(Exception) as exc_info:
            await service.sync_caldav_to_db(
                user_id=1,
                calendar_name="Personal",
                db=mock_db
            )
        
        assert "Network timeout" in str(exc_info.value)
        mock_db.rollback.assert_called()
    
    async def test_handles_parsing_error_gracefully(self):
        """Test that parsing errors are handled gracefully and logged."""
        service = SyncService(user_id=1)
        
        # Mock database session
        mock_db = AsyncMock()
        mock_db.commit = AsyncMock()
        mock_db.rollback = AsyncMock()
        
        # Mock execute results
        mock_scalars = MagicMock()
        mock_scalars.all = MagicMock(return_value=[])  # No local events
        
        mock_execute_result = MagicMock()
        mock_execute_result.scalars = MagicMock(return_value=mock_scalars)
        
        mock_db.execute = AsyncMock(return_value=mock_execute_result)
        
        # Mock CalDAV ORM
        mock_calendar = SimpleNamespace(id="cal123")
        service.caldav_orm.authenticate = AsyncMock()
        service.caldav_orm.Calendar.get_by_name = AsyncMock(return_value=mock_calendar)
        
        # Mock remote event
        remote_event = SimpleNamespace(
            uid="event123",
            url="https://caldav.example.com/event123",
            title="Test Event",
            description="Test",
            start=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            end=datetime(2024, 1, 1, 13, 0, 0, tzinfo=timezone.utc)
        )
        service.caldav_orm.Event.all = AsyncMock(return_value=[remote_event])
        
        # Mock repository to raise parsing error
        service.repo.fetch_ical_event = AsyncMock(return_value="INVALID")
        service.repo.parse_ical_full = AsyncMock(
            side_effect=Exception("Parsing error")
        )
        
        # Run sync - should not raise, but log and continue
        await service.sync_caldav_to_db(
            user_id=1,
            calendar_name="Personal",
            db=mock_db
        )
        
        # Sync should complete despite parsing error (no exceptions raised)
        # The event with parsing error should be skipped
        assert True  # If we get here, no exception was raised
