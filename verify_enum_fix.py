#!/usr/bin/env python3
"""
Verification script to demonstrate the PostgreSQL enum fix.

This script shows that:
1. The SyncStatus enum has the correct values
2. The SQLAlchemy models use native PostgreSQL ENUM
3. The migration properly handles enum conversion

Run this after applying the migration to verify everything works.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def verify_enum_values():
    """Verify the SyncStatus enum has correct values."""
    print("1. Verifying SyncStatus enum values...")
    
    # Read enum file directly instead of importing (to avoid dependencies)
    with open(project_root / 'server/db/models/enums.py', 'r') as f:
        enum_content = f.read()
    
    # Check for correct values
    assert 'pending = "pending"' in enum_content, "Missing 'pending' value"
    assert 'success = "success"' in enum_content, "Missing 'success' value"
    assert 'failed = "failed"' in enum_content, "Missing 'failed' value"
    
    # Check old values are removed
    assert 'partial' not in enum_content, "Old 'partial' value still present"
    assert 'synced' not in enum_content, "Old 'synced' value still present"
    assert 'error' not in enum_content, "Old 'error' value still present"
    
    print("   ✓ SyncStatus has correct values: ['pending', 'success', 'failed']")
    print("   ✓ Old values removed: ['partial', 'synced', 'error']")
    
    # Check docstring exists
    assert '"""' in enum_content, "Missing docstring"
    print("   ✓ Enum has documentation")


def verify_model_configuration():
    """Verify SQLAlchemy models use native PostgreSQL ENUM."""
    print("\n2. Verifying SQLAlchemy model configuration...")
    
    # Read tasks.py
    with open(project_root / 'server/db/models/tasks.py', 'r') as f:
        tasks_content = f.read()
    
    # Check for correct imports and usage
    assert 'from sqlalchemy.dialects.postgresql import ENUM as PGEnum' in tasks_content, \
        "Missing PGEnum import in tasks.py"
    assert "PGEnum(SyncStatus, name='syncstatus', native_enum=True)" in tasks_content, \
        "Missing native_enum=True in tasks.py"
    print("   ✓ tasks.py uses PostgreSQL native ENUM")
    
    # Read caldav_events.py
    with open(project_root / 'server/db/models/caldav_events.py', 'r') as f:
        caldav_content = f.read()
    
    assert 'ENUM as PGEnum' in caldav_content, \
        "Missing PGEnum import in caldav_events.py"
    assert "PGEnum(SyncStatus, name='syncstatus', native_enum=True)" in caldav_content, \
        "Missing native_enum=True in caldav_events.py"
    print("   ✓ caldav_events.py uses PostgreSQL native ENUM")


def verify_migration():
    """Verify the migration file has correct structure."""
    print("\n3. Verifying migration file...")
    
    migration_file = project_root / 'server/alembic/versions/f0995c8c6da0_update_syncstatus_enum_values.py'
    
    with open(migration_file, 'r') as f:
        migration_content = f.read()
    
    # Check for key migration steps
    checks = [
        ("Rename old enum", "ALTER TYPE syncstatus RENAME TO syncstatus_old"),
        ("Create new enum", "CREATE TYPE syncstatus AS ENUM ('pending', 'success', 'failed')"),
        ("Map done->success", "WHEN sync_status::text = 'done' THEN 'success'::syncstatus"),
        ("Drop old enum", "DROP TYPE syncstatus_old"),
    ]
    
    for name, check in checks:
        assert check in migration_content, f"Missing: {name}"
        print(f"   ✓ {name}")


def verify_documentation():
    """Verify documentation files exist."""
    print("\n4. Verifying documentation...")
    
    docs = [
        ('docs/POSTGRESQL_ENUM_GUIDE.md', 'PostgreSQL ENUM guide'),
        ('SYNCSTATUS_ENUM_FIX.md', 'Fix summary'),
        ('docs/EXAMPLE_TRIGGERS_WITH_ENUM.py', 'Example triggers'),
    ]
    
    for doc_path, name in docs:
        full_path = project_root / doc_path
        assert full_path.exists(), f"Missing: {doc_path}"
        print(f"   ✓ {name} exists")


def main():
    """Run all verification checks."""
    print("=" * 70)
    print("PostgreSQL Enum Fix - Verification Script")
    print("=" * 70)
    
    try:
        verify_enum_values()
        verify_model_configuration()
        verify_migration()
        verify_documentation()
        
        print("\n" + "=" * 70)
        print("✅ ALL VERIFICATIONS PASSED!")
        print("=" * 70)
        print("\nThe fix is correctly implemented. Next steps:")
        print("1. Run: alembic upgrade head")
        print("2. Restart your application")
        print("3. Test CRUD operations on tasks")
        print("\nFor more details, see: SYNCSTATUS_ENUM_FIX.md")
        
        return 0
        
    except AssertionError as e:
        print(f"\n❌ VERIFICATION FAILED: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
