# Notion Webhook Handler - Testing Guide

## Quick Start Test Script

Save this as `test_webhook.py` and run it to verify the handler works with all event types:

```python
import asyncio
import aiohttp
import json
from datetime import datetime

# Configuration
WEBHOOK_URL = "http://localhost:8000/webhooks/notion/"

# Test data with valid workspace_id and entity.id
WORKSPACE_ID = "550e8400e29b41d4a716446655440000"  # Replace with your actual workspace UUID
ENTITY_ID = "284a5558-72b4-8086-82c3-da846290d940"  # Replace with your actual entity UUID

async def test_webhook(event_type: str, payload: dict, description: str):
    """Send a webhook test and print results"""
    print(f"\n{'='*80}")
    print(f"TEST: {description}")
    print(f"{'='*80}")
    print(f"Event Type: {event_type}")
    print(f"Payload:\n{json.dumps(payload, indent=2)}")
    print(f"\nSending to: {WEBHOOK_URL}")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(WEBHOOK_URL, json=payload) as resp:
                status = resp.status
                response_data = await resp.json()
                print(f"\n✓ Status: {status}")
                print(f"✓ Response: {json.dumps(response_data, indent=2)}")
                
                if status == 200 and "error" not in response_data:
                    print("✓ SUCCESS: Webhook processed without errors")
                elif "error" in response_data:
                    print(f"⚠ WARNING: {response_data.get('error')}")
                else:
                    print(f"✗ FAILED: Unexpected status {status}")
    except Exception as e:
        print(f"✗ ERROR: {e}")

async def run_tests():
    """Run all test cases"""
    
    # ========================================================================
    # Test 1: page.created with minimal payload
    # ========================================================================
    await test_webhook(
        "page.created",
        {
            "type": "page.created",
            "entity": {"id": ENTITY_ID},
            "workspace_id": WORKSPACE_ID,
            # Note: NO data field (this caused the original crash)
        },
        "page.created with minimal payload (NO data field)"
    )
    
    await asyncio.sleep(1)
    
    # ========================================================================
    # Test 2: page.created with data field (but no updated_properties)
    # ========================================================================
    await test_webhook(
        "page.created",
        {
            "type": "page.created",
            "entity": {"id": ENTITY_ID},
            "workspace_id": WORKSPACE_ID,
            "data": None,  # data is present but None
        },
        "page.created with data=None (edge case)"
    )
    
    await asyncio.sleep(1)
    
    # ========================================================================
    # Test 3: page.properties_updated with updated_properties
    # ========================================================================
    await test_webhook(
        "page.properties_updated",
        {
            "type": "page.properties_updated",
            "entity": {"id": ENTITY_ID},
            "workspace_id": WORKSPACE_ID,
            "data": {
                "updated_properties": ["Title", "Status", "Priority"]
            },
        },
        "page.properties_updated with updated_properties list"
    )
    
    await asyncio.sleep(1)
    
    # ========================================================================
    # Test 4: page.properties_updated with empty updated_properties
    # ========================================================================
    await test_webhook(
        "page.properties_updated",
        {
            "type": "page.properties_updated",
            "entity": {"id": ENTITY_ID},
            "workspace_id": WORKSPACE_ID,
            "data": {
                "updated_properties": []
            },
        },
        "page.properties_updated with empty updated_properties list"
    )
    
    await asyncio.sleep(1)
    
    # ========================================================================
    # Test 5: page.deleted event
    # ========================================================================
    await test_webhook(
        "page.deleted",
        {
            "type": "page.deleted",
            "entity": {"id": ENTITY_ID},
            "workspace_id": WORKSPACE_ID,
        },
        "page.deleted event (no data field expected)"
    )
    
    await asyncio.sleep(1)
    
    # ========================================================================
    # Test 6: Payload with extra unknown fields (should be ignored)
    # ========================================================================
    await test_webhook(
        "page.created",
        {
            "type": "page.created",
            "entity": {"id": ENTITY_ID},
            "workspace_id": WORKSPACE_ID,
            "extra_field_1": "should be ignored",
            "extra_field_2": {"nested": "data"},
        },
        "page.created with extra unknown fields (should be ignored gracefully)"
    )
    
    await asyncio.sleep(1)
    
    # ========================================================================
    # Test 7: Missing type (should still work with "unknown" default)
    # ========================================================================
    await test_webhook(
        "unknown (type missing)",
        {
            "entity": {"id": ENTITY_ID},
            "workspace_id": WORKSPACE_ID,
            # Note: NO type field
        },
        "page event with missing type field (should default to 'unknown')"
    )
    
    await asyncio.sleep(1)
    
    # ========================================================================
    # Test 8: Invalid entity.id UUID format (should error gracefully)
    # ========================================================================
    await test_webhook(
        "page.created",
        {
            "type": "page.created",
            "entity": {"id": "not-a-valid-uuid"},
            "workspace_id": WORKSPACE_ID,
        },
        "page.created with invalid entity.id format"
    )
    
    await asyncio.sleep(1)
    
    # ========================================================================
    # Test 9: Invalid workspace_id UUID format (should error gracefully)
    # ========================================================================
    await test_webhook(
        "page.created",
        {
            "type": "page.created",
            "entity": {"id": ENTITY_ID},
            "workspace_id": "not-a-valid-uuid",
        },
        "page.created with invalid workspace_id format"
    )
    
    await asyncio.sleep(1)
    
    # ========================================================================
    # Test 10: Missing entity.id (should error gracefully)
    # ========================================================================
    await test_webhook(
        "page.created",
        {
            "type": "page.created",
            "entity": {},  # No id field
            "workspace_id": WORKSPACE_ID,
        },
        "page.created with missing entity.id"
    )
    
    print(f"\n{'='*80}")
    print("All tests completed!")
    print(f"{'='*80}\n")

if __name__ == "__main__":
    print("Notion Webhook Handler - Test Suite")
    print("Make sure your FastAPI server is running on http://localhost:8000")
    asyncio.run(run_tests())
```

## Manual Testing with curl

### Test 1: page.created (Original problem case)
```bash
curl -X POST http://localhost:8000/webhooks/notion/ \
  -H "Content-Type: application/json" \
  -d '{
    "type": "page.created",
    "entity": {"id": "284a5558-72b4-8086-82c3-da846290d940"},
    "workspace_id": "550e8400e29b41d4a716446655440000"
  }'
```

**Expected Response:**
```json
{
  "message": "Notion webhook processed successfully",
  "event_type": "page.created",
  "page_id": "284a555872b4808682c3da846290d940",
  "workspace_id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": 7
}
```

**Expected Logs:**
```
Payload keys received: ['type', 'entity', 'workspace_id']
Event type: page.created
Page ID (entity.id): 284a5558-72b4-8086-82c3-da846290d940 → hex: 284a555872b4808682c3da846290d940
Workspace ID: 550e8400e29b41d4a716446655440000 → standard: 550e8400-e29b-41d4-a716-446655440000
'data' field note: Field 'data' in payload.data is None (this is normal for page.created)
Event type 'page.created' does not use 'updated_properties'; skipping
User found: user_id=7, email=user@example.com
Webhook data saved to Redis for user_id=7
Webhook sync completed successfully
```

### Test 2: page.properties_updated
```bash
curl -X POST http://localhost:8000/webhooks/notion/ \
  -H "Content-Type: application/json" \
  -d '{
    "type": "page.properties_updated",
    "entity": {"id": "284a5558-72b4-8086-82c3-da846290d940"},
    "workspace_id": "550e8400e29b41d4a716446655440000",
    "data": {
      "updated_properties": ["Title", "Status"]
    }
  }'
```

**Expected Logs:**
```
Event type: page.properties_updated
Updated properties keys: ['Title', 'Status']
```

### Test 3: page.deleted
```bash
curl -X POST http://localhost:8000/webhooks/notion/ \
  -H "Content-Type: application/json" \
  -d '{
    "type": "page.deleted",
    "entity": {"id": "284a5558-72b4-8086-82c3-da846290d940"},
    "workspace_id": "550e8400e29b41d4a716446655440000"
  }'
```

## Expected Behavior Summary

| Test Case | Input | Expected Behavior |
|-----------|-------|-------------------|
| page.created (no data) | Minimal payload | ✓ Success, logs field missing warning |
| page.created (data=None) | data field set to null | ✓ Success, logs field is None |
| page.properties_updated | Has updated_properties | ✓ Success, logs properties |
| page.deleted | Only entity and workspace_id | ✓ Success, no crash |
| Extra unknown fields | Unknown field in payload | ✓ Success, fields ignored |
| Missing type | No type field | ✓ Success, type defaults to "unknown" |
| Invalid entity.id UUID | Non-UUID string | ✗ Error, logs UUID parse failure |
| Invalid workspace_id UUID | Non-UUID string | ✗ Error, logs UUID parse failure |
| Missing entity | entity field absent | ✗ Error, returns "Entity field missing" |
| Missing entity.id | No id in entity | ✗ Error, returns "Entity ID missing" |
| User not found | Valid UUIDs but user doesn't exist | ✗ Error, returns "User not found" |

## Debugging

### Check Redis Data
After a webhook is processed, check Redis to see what was stored:

```bash
# Connect to Redis
redis-cli

# Get webhook data for user 7
HGETALL webhook:7

# View the data field
HGET webhook:7 data
```

The data will show:
```json
{
  "user_id": 7,
  "page_id": "284a555872b4808682c3da846290d940",
  "workspace_id": "550e8400-e29b-41d4-a716-446655440000",
  "event_type": "page.created",
  "payload_keys": ["type", "entity", "workspace_id"],
  "extracted_fields": {
    "type": "page.created",
    "page_id": "284a555872b4808682c3da846290d940",
    "workspace_id": "550e8400-e29b-41d4-a716-446655440000",
    "user_id": 7,
    "updated_properties": null
  },
  "missing_fields": {
    "data": "Field 'data' in payload.data is None"
  }
}
```

### Check Application Logs
The handler logs at multiple levels:

```bash
# For DEBUG logs (all field extraction details):
tail -f logs/app.log | grep "Successfully extracted"

# For WARNING logs (fields missing):
tail -f logs/app.log | grep "Field extraction warning"

# For ERROR logs (critical failures):
tail -f logs/app.log | grep "error"
```

## Key Assertions

If you want to add automated tests, verify:

1. ✓ `page.created` without data field doesn't crash
2. ✓ `page.properties_updated` without updated_properties doesn't crash
3. ✓ Both UUID formats (with/without dashes) are handled
4. ✓ User lookup by workspace_id succeeds
5. ✓ Redis storage includes extracted_fields and missing_fields
6. ✓ `sync_webhook_data()` is called for all events
7. ✓ Error responses are returned for truly missing critical fields
8. ✓ All logs are present for debugging

