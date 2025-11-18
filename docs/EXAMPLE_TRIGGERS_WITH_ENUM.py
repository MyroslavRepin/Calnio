"""
Example: Creating PostgreSQL Functions and Triggers with ENUM Types

This file demonstrates how to create database functions and triggers that properly
handle the syncstatus ENUM type. These are examples referenced in the problem statement.

IMPORTANT: These are EXAMPLES only. Include in a migration if needed.
"""

# Example migration snippet for creating triggers that work with enum types

EXAMPLE_TRIGGER_MIGRATION = """

def upgrade() -> None:
    # Example 1: Function that accepts enum parameter
    op.execute('''
        CREATE OR REPLACE FUNCTION set_sources_db(
            task_id VARCHAR,
            new_status syncstatus  -- ✅ Use enum type for parameter
        ) RETURNS void AS $$
        BEGIN
            UPDATE notion_tasks 
            SET sync_status = new_status,
                sync_source = 'db'
            WHERE id = task_id;
        END;
        $$ LANGUAGE plpgsql;
    ''')
    
    # Example 2: Function with v2 that compares enum values
    op.execute('''
        CREATE OR REPLACE FUNCTION set_sources_db_v2() 
        RETURNS TRIGGER AS $$
        BEGIN
            -- Compare using enum-cast literal (recommended)
            IF NEW.sync_source = 'db' AND NEW.sync_status != 'pending'::syncstatus THEN
                NEW.sync_status = 'pending'::syncstatus;
            END IF;
            
            -- Alternative: cast enum to text for comparison
            IF NEW.sync_source = 'caldav' AND NEW.sync_status::text = 'failed' THEN
                NEW.sync_status = 'pending'::syncstatus;
            END IF;
            
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    ''')
    
    # Example 3: Function that ensures sync sources are set
    op.execute('''
        CREATE OR REPLACE FUNCTION ensure_sync_sources() 
        RETURNS TRIGGER AS $$
        BEGIN
            -- Ensure sync_source is set based on which fields are populated
            IF NEW.sync_source IS NULL OR NEW.sync_source = '' THEN
                IF NEW.notion_page_id IS NOT NULL THEN
                    NEW.sync_source = 'notion';
                ELSIF NEW.caldav_id IS NOT NULL THEN
                    NEW.sync_source = 'caldav';
                ELSE
                    NEW.sync_source = 'db';
                END IF;
            END IF;
            
            -- Set initial sync_status if not provided
            IF NEW.sync_status IS NULL THEN
                NEW.sync_status = 'pending'::syncstatus;  -- ✅ Cast to enum
            END IF;
            
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    ''')
    
    # Example 4: Notification trigger (NOTIFY with enum data)
    op.execute('''
        CREATE OR REPLACE FUNCTION notify_notion_task_change() 
        RETURNS TRIGGER AS $$
        DECLARE
            payload json;
        BEGIN
            -- Build JSON payload, converting enum to text
            payload = json_build_object(
                'id', NEW.id,
                'operation', TG_OP,
                'sync_status', NEW.sync_status::text,  -- ✅ Cast enum to text for JSON
                'sync_source', NEW.sync_source
            );
            
            -- Send notification
            PERFORM pg_notify('notion_task_changes', payload::text);
            
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    ''')
    
    # Create triggers that use these functions
    op.execute('''
        DROP TRIGGER IF EXISTS ensure_sync_sources_trigger ON notion_tasks;
        CREATE TRIGGER ensure_sync_sources_trigger
            BEFORE INSERT OR UPDATE ON notion_tasks
            FOR EACH ROW
            EXECUTE FUNCTION ensure_sync_sources();
    ''')
    
    op.execute('''
        DROP TRIGGER IF EXISTS set_sources_db_trigger ON notion_tasks;
        CREATE TRIGGER set_sources_db_trigger
            BEFORE UPDATE ON notion_tasks
            FOR EACH ROW
            EXECUTE FUNCTION set_sources_db_v2();
    ''')
    
    op.execute('''
        DROP TRIGGER IF EXISTS notify_task_change_trigger ON notion_tasks;
        CREATE TRIGGER notify_task_change_trigger
            AFTER INSERT OR UPDATE OR DELETE ON notion_tasks
            FOR EACH ROW
            EXECUTE FUNCTION notify_notion_task_change();
    ''')


def downgrade() -> None:
    # Drop triggers first
    op.execute('DROP TRIGGER IF EXISTS notify_task_change_trigger ON notion_tasks')
    op.execute('DROP TRIGGER IF EXISTS set_sources_db_trigger ON notion_tasks')
    op.execute('DROP TRIGGER IF EXISTS ensure_sync_sources_trigger ON notion_tasks')
    
    # Drop functions
    op.execute('DROP FUNCTION IF EXISTS notify_notion_task_change()')
    op.execute('DROP FUNCTION IF EXISTS set_sources_db_v2()')
    op.execute('DROP FUNCTION IF EXISTS ensure_sync_sources()')
    op.execute('DROP FUNCTION IF EXISTS set_sources_db(VARCHAR, syncstatus)')
"""

# Key points when creating functions/triggers with enum types:
BEST_PRACTICES = """
1. Function Parameters:
   - Use enum type: `new_status syncstatus` NOT `new_status VARCHAR`
   - This allows direct assignment without casting

2. Comparisons in PL/pgSQL:
   - Cast literals to enum: `NEW.sync_status = 'pending'::syncstatus`
   - OR cast enum to text: `NEW.sync_status::text = 'pending'`
   - Prefer the first approach for type safety

3. Assignments:
   - Direct: `NEW.sync_status = 'pending'::syncstatus`
   - From parameter: `NEW.sync_status = param_status` (if param_status is syncstatus type)

4. JSON/Text Output:
   - Always cast to text: `NEW.sync_status::text`
   - This converts enum to its string representation

5. Trigger Timing:
   - BEFORE triggers: Can modify NEW.sync_status
   - AFTER triggers: Can only read NEW.sync_status for notifications

6. Migration Order:
   - Create enum type FIRST
   - Create columns using the enum
   - Create functions that reference the enum
   - Create triggers that call the functions
"""

if __name__ == "__main__":
    print("This file contains example code for PostgreSQL triggers/functions with enum types")
    print("Include relevant portions in an Alembic migration if needed")
    print(BEST_PRACTICES)
