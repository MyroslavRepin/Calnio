import redis.asyncio as redis
from server.app.core.config import settings
from server.app.core.logging_config import logger

# Variable to store redis client
_redis_client: redis.Redis | None = None

# Initialize redis connection
async def init_redis() -> redis.Redis:
    global _redis_client
    if _redis_client is None:
        redis_url = settings.redis_connection_url
        logger.info(f"🔌 Connecting to Redis: {redis_url.split('@')[-1] if '@' in redis_url else redis_url}")
        _redis_client = redis.from_url(
            redis_url,
            decode_responses=True
        )
        pong = await _redis_client.ping()
        logger.info(f"🔌 Redis connected successfully: {pong}")
    return _redis_client

# Universal method to get redis client
async def get_redis() -> redis.Redis:
    global _redis_client
    if _redis_client is None:
        redis_url = settings.redis_connection_url
        logger.info(f"🔌 Connecting to Redis (from get_redis): {redis_url.split('@')[-1] if '@' in redis_url else redis_url}")
        _redis_client = redis.from_url(
            redis_url,
            decode_responses=True
        )
        pong = await _redis_client.ping()
        logger.info(f"🔌 Redis connected successfully: {pong}")
    return _redis_client

# Close redis connection
async def close_redis():
    global _redis_client
    if _redis_client:
        await _redis_client.close()
        logger.info("Redis connection closed")
        _redis_client = None