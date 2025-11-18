"""
Script to check Notion integration access and available databases
"""
import asyncio
import sys
sys.path.insert(0, '/Users/myroslavrepin/Documents/dev/Calnio')

from server.db.deps import async_get_db_cm
from server.integrations.notion.notion_client import get_notion_client
from sqlalchemy import text


async def check_notion_access(user_id: int):
    async with async_get_db_cm() as db:
        # Query user and integration using raw SQL to avoid model issues
        query = text("""
            SELECT 
                u.id, u.username,
                ni.access_token, ni.workspace_name, ni.workspace_id, 
                ni.bot_id, ni.duplicated_template_id
            FROM users u
            LEFT JOIN notion_integrations ni ON u.id = ni.user_id
            WHERE u.id = :user_id
        """)

        result = await db.execute(query, {"user_id": user_id})
        row = result.fetchone()

        if not row:
            print(f"❌ User {user_id} not found")
            return

        user_id, username, access_token, workspace_name, workspace_id, bot_id, database_id = row

        if not access_token:
            print(f"❌ User {username} (ID: {user_id}) has no Notion integration")
            return

        print(f"✅ User: {username} (ID: {user_id})")
        print(f"✅ Notion Integration found")
        print(f"   - Workspace: {workspace_name}")
        print(f"   - Workspace ID: {workspace_id}")
        print(f"   - Bot ID: {bot_id}")
        print(f"   - Database ID (duplicated_template_id): {database_id or 'NOT SET'}")

        # Test Notion API
        notion = get_notion_client(access_token)

        print("\n🔍 Testing Notion API access...")

        # Try search
        try:
            search_result = await notion.search()
            print(f"✅ Search successful: {len(search_result.get('results', []))} results")

            for obj in search_result.get('results', []):
                obj_type = obj.get('object')
                obj_id = obj.get('id')
                title = 'Untitled'

                if obj_type == 'database':
                    title_prop = obj.get('title', [])
                    if title_prop:
                        title = ''.join([t.get('plain_text', '') for t in title_prop])
                elif obj_type == 'page':
                    props = obj.get('properties', {})
                    title_prop = props.get('title', {}).get('title', [])
                    if title_prop:
                        title = ''.join([t.get('plain_text', '') for t in title_prop])

                print(f"   - {obj_type}: {title} (ID: {obj_id})")

        except Exception as e:
            print(f"❌ Search failed: {e}")

        # Try search with filter
        try:
            db_search = await notion.search(filter={"property": "object", "value": "database"})
            databases = db_search.get('results', [])
            print(f"\n✅ Database search: {len(databases)} databases found")

            for db_obj in databases:
                db_id = db_obj.get('id')
                title_prop = db_obj.get('title', [])
                title = ''.join([t.get('plain_text', '') for t in title_prop]) if title_prop else 'Untitled'
                print(f"   - Database: {title} (ID: {db_id})")

                # Try to query this database
                try:
                    query_result = await notion.databases.query(database_id=db_id)
                    pages = len(query_result.get('results', []))
                    print(f"     └─ {pages} pages in this database")
                except Exception as e:
                    print(f"     └─ Error querying: {e}")

        except Exception as e:
            print(f"❌ Database search failed: {e}")


if __name__ == "__main__":
    user_id = int(input("Enter user_id to check (default 3): ") or "3")
    asyncio.run(check_notion_access(user_id))

