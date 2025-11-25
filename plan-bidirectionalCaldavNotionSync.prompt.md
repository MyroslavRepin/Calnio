# Plan: Bidirectional CalDAV ↔ Notion Sync Implementation

## TL;DR
Implement two-way synchronization between CalDAV (Apple Calendar) and Notion using your existing models (`CalDavEvent`, `UserNotionTask`) and sync infrastructure. The system will detect changes from both sources, resolve conflicts using timestamps, and propagate updates bidirectionally. Leverage your existing `SyncService`, CalDAV ORM, and Notion API clients to minimize new code.

---

## Core Architecture Overview

**Your Current State:**
- ✅ Models: `CalDavEvent` and `UserNotionTask` with sync metadata
- ✅ CalDAV client: [`caldav_orm.py`](server/services/caldav/caldav_orm.py) with CRUD operations
- ✅ Notion client: [`notion_client.py`](server/integrations/notion/notion_client.py) and sync functions
- ✅ Sync manager: [`sync_manager.py`](server/services/sync/sync_manager.py) with basic bidirectional logic
- ⚠️ **Gap**: No automated triggers for real-time sync, incomplete CalDAV → Notion write operations

---

## Steps

### 1. **Complete CalDAV → Notion Sync Pipeline** 
Enhance [`sync_manager.py`](server/services/sync/sync_manager.py) `sync_caldav_to_db()` to write changes to Notion API
- After updating `UserNotionTask` in DB, call Notion API to update/create corresponding Notion page
- Use existing `NotionTaskRepository.update_pages_by_ids()` pattern
- Map CalDAV fields → Notion properties: `title`, `description`, `start_date`, `end_date`
- **Files**: `sync_manager.py`, `notion_sync.py`, `notion_tasks.py` repository

### 2. **Complete Notion → CalDAV Sync Pipeline**
Finish [`sync_db_to_caldav()`](server/services/sync/sync_manager.py) to push Notion changes to CalDAV
- For `UserNotionTask` with `sync_status=pending` and `last_modified_source=notion`, push to CalDAV
- Use `CalDavORM.Event.create()` or `update()` from [`caldav_orm.py`](server/services/caldav/caldav_orm.py)
- Generate proper iCal format with `icalendar` library (already in use)
- Mark `sync_status=success` after successful push
- **Files**: `sync_manager.py`, `caldav_orm.py`

### 3. **Add Conflict Detection & Resolution**
Implement conflict handling when both sources change simultaneously
- Use `last_modified_source` and timestamps (`updated_at`, `last_modified_caldav`) as in your existing code
- Set `has_conflict=True` when timestamps differ by < 5 seconds
- Strategy: **Last-write-wins** (already partially implemented) or user-configurable
- Log conflicts to [`logs/`](logs/) for user review in dashboard
- **Files**: `sync_manager.py`, add new `conflict_resolver.py` helper

### 4. **Create Scheduled Sync Job**
Use APScheduler (already in project) to run sync every N minutes
- Create job in [`apscheduler_test.py`](scripts/apscheduler_test.py) pattern or new `scheduler.py`
- Job calls `SyncService.sync_user_events()` for each active user
- Run every 5-15 minutes (configurable per user in `users` table)
- Add `last_sync_at` column to `users` table to track sync health
- **Files**: New `server/services/scheduler/sync_scheduler.py`, `main.py` to start scheduler

### 5. **Add Real-Time Sync Triggers**
Implement webhooks/polling for instant updates
- **Notion**: Use existing webhook handler in [`postgres_trigger.py`](server/services/postgres_trigger.py) pattern
- **CalDAV**: Poll for changes via `ctag`/`sync-token` (CalDAV standard) every 2-5 minutes
- Trigger immediate `SyncService` run when change detected
- **Files**: `caldav_polling.py`, update `notion_sync.py` webhook handlers

### 6. **Add Sync Status Tracking & UI**
Show sync status in brutalist dashboard
- Add API endpoint `/api/v1/sync/status` returning last sync time, conflict count
- Update [`brutalist-dashboard.html`](frontend/templates/brutalist-dashboard.html) to show sync badge
- Add `/dashboard/conflicts` page to show and resolve conflicts
- **Files**: New `sync_api.py`, update dashboard template

---

## Further Considerations

### 1. **Soft Deletion Sync**
Currently `deleted=True` flag exists but not fully synced. Should deleted Notion tasks remove CalDAV events? Or archive? **Recommendation**: Add user preference toggle.

### 2. **Initial Sync Strategy**
When user first connects CalDAV, should it: (A) Import all existing CalDAV events → Notion, (B) Export all Notion tasks → CalDAV, or (C) Merge both? **Recommendation**: Option C with conflict resolution UI.

### 3. **Performance Optimization**
Sync only changed items using:
- CalDAV `sync-token` (supported by iCloud)
- Notion `last_edited_time` filter
- Redis cache for "last processed timestamp"
**Tip**: Store sync tokens in `users` table or Redis

### 4. **Error Handling**
Add retry logic with exponential backoff for:
- Network failures (CalDAV server down)
- Rate limits (Notion API: 3 req/sec)
- Invalid data (missing required fields)
**Tip**: Use `tenacity` library for retries

---

## Speed-Up Tips for Building This

1. **Reuse Existing Code Heavily**
   - Your `sync_caldav_to_db()` already has 80% of the logic
   - Copy-paste the timestamp comparison pattern from lines 165-209 in `sync_manager.py`
   - Use `NotionTaskRepository` methods as-is, just call them from sync

2. **Start with Polling, Not Webhooks**
   - Scheduled job (step 4) is faster to implement than real-time webhooks
   - Get basic sync working first, optimize latency later

3. **Skip UI Initially**
   - Log conflicts to file, view manually in dashboard later
   - Focus on backend sync correctness first

4. **Use Feature Flags**
   - Add `enable_caldav_sync` boolean to `users` table
   - Only sync for opted-in users during testing
   - Prevents breaking existing Notion-only users

5. **Test with One User**
   - Your own account with both CalDAV and Notion connected
   - Create test events in both directions
   - Monitor logs in [`logs/app_2025-11-22.log`](logs/app_2025-11-22.log)

6. **Batch Operations**
   - Instead of syncing one event at a time, collect all changes, then bulk create/update
   - CalDAV: Use `batch` operations
   - Notion: Send multiple `pages.update()` in parallel with `asyncio.gather()`

7. **Add Telemetry Early**
   - Use your existing `logger` extensively
   - Add metrics: `sync_duration`, `events_synced`, `conflicts_detected`
   - Helps debug timing issues before they become problems

8. **Incremental Rollout**
   - Week 1: CalDAV → Notion only (read from CalDAV, write to Notion)
   - Week 2: Notion → CalDAV (reverse direction)
   - Week 3: Full bidirectional with conflict resolution
   - Week 4: Real-time triggers + UI

---

## Key Files to Modify

| File | Changes Needed |
|------|----------------|
| [`sync_manager.py`](server/services/sync/sync_manager.py) | Complete both sync directions, add conflict logic |
| [`caldav_orm.py`](server/services/caldav/caldav_orm.py) | Add `Event.update()` and `Event.create()` (partially exists) |
| [`notion_sync.py`](server/services/notion_syncing/notion_sync.py) | Call from CalDAV sync, add reverse sync function |
| [`users.py` model](server/db/models/tasks.py) | Add `enable_caldav_sync`, `caldav_sync_token`, `last_sync_at` columns |
| [`brutalist-dashboard.html`](frontend/templates/brutalist-dashboard.html) | Add sync status widget, conflict count |
| New: `sync_scheduler.py` | APScheduler job to run sync every 5-15 min |
| New: `sync_api.py` | API endpoints for manual sync trigger, status check |

---

**Estimated Timeline**: 2-3 weeks for full implementation, 3-5 days for MVP (one-way sync + scheduled job).

