"""
Tests for the sync scheduler functionality.
"""
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.services.scheduler import SyncScheduler


class TestSyncScheduler:
    """Test cases for the SyncScheduler class."""
    
    def test_scheduler_initialization(self):
        """Test that scheduler initializes correctly."""
        scheduler = SyncScheduler()
        assert scheduler.scheduler is not None
        assert scheduler.user_jobs == {}
    
    def test_scheduler_start_stop(self):
        """Test scheduler start and stop functionality."""
        scheduler = SyncScheduler()
        
        # Test start
        scheduler.start()
        assert scheduler.scheduler.running
        
        # Test stop
        scheduler.shutdown()
        assert not scheduler.scheduler.running
    
    def test_add_remove_sync_job(self):
        """Test adding and removing sync jobs."""
        scheduler = SyncScheduler()
        scheduler.start()
        
        try:
            # Test adding job
            user_id = 123
            interval = 30
            scheduler.add_user_sync_job(user_id, interval)
            assert user_id in scheduler.user_jobs
            
            # Test removing job
            scheduler.remove_user_sync_job(user_id)
            assert user_id not in scheduler.user_jobs
            
        finally:
            scheduler.shutdown()
    
    def test_sync_interval_validation(self):
        """Test that sync intervals are handled correctly."""
        scheduler = SyncScheduler()
        scheduler.start()
        
        try:
            # Test valid interval
            scheduler.add_user_sync_job(1, 30)
            assert 1 in scheduler.user_jobs
            
            # Test updating interval
            scheduler.add_user_sync_job(1, 60)
            assert 1 in scheduler.user_jobs  # Should still be there with updated job
            
        finally:
            scheduler.shutdown()


class TestUserModel:
    """Test cases for User model changes."""
    
    def test_sync_interval_default(self):
        """Test that sync_interval has correct default value."""
        from backend.app.models.users import User
        
        # Check that the model has the sync_interval field
        assert hasattr(User, 'sync_interval')
        
        # Check that mapped_column has default value
        sync_interval_column = User.__table__.columns['sync_interval']
        assert sync_interval_column.default.arg == 30


if __name__ == "__main__":
    # Run basic tests without pytest
    print("Running basic scheduler tests...")
    
    test_scheduler = TestSyncScheduler()
    test_scheduler.test_scheduler_initialization()
    print("✅ Scheduler initialization test passed")
    
    test_scheduler.test_scheduler_start_stop()
    print("✅ Scheduler start/stop test passed")
    
    test_scheduler.test_add_remove_sync_job()
    print("✅ Add/remove sync job test passed")
    
    test_scheduler.test_sync_interval_validation()
    print("✅ Sync interval validation test passed")
    
    test_model = TestUserModel()
    test_model.test_sync_interval_default()
    print("✅ User model test passed")
    
    print("🎉 All tests passed!")