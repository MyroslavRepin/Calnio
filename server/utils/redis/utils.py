import json
from redis import asyncio as aioredis

async def save_webhook_data(user_id: int, data: dict, redis: aioredis.Redis):
    """
    Stores webhook data in Redis, bound to the user_id.
    TTL can be set separately if needed.
    """

    data_json = json.dumps(data)

    await redis.hset(f"webhook:{user_id}", mapping={"data": data_json})
    await redis.expire(f"webhook:{user_id}", 3600)  # 1 час
    print(">>> Webhook data saved to Redis")


async def get_webhook_data(user_id: int, redis: aioredis.Redis):
    """Getting webhook data from Redis."""
    data_json = await redis.hget(f"webhook:{user_id}", "data")
    if data_json:
        return json.loads(data_json)
    return None