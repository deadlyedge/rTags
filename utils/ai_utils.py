# utils/external_api_utils.py
import os
import redis.asyncio as redis
from openai import OpenAI
from redis.asyncio import Redis
from dotenv import load_dotenv

load_dotenv()

PERPLEXITY_API_KEY = os.environ.get("PERPLEXITY_API_KEY")
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379")

if not PERPLEXITY_API_KEY:
    raise ValueError("PERPLEXITY_API_KEY environment variable not set.")


def get_perplexity_client() -> OpenAI:
    """Initializes and returns a Perplexity API client."""
    return OpenAI(
        api_key=PERPLEXITY_API_KEY,
        base_url="https://api.perplexity.ai",
    )


async def get_redis_client() -> Redis:
    """Initializes and returns a Redis client."""
    return redis.from_url(REDIS_URL)


async def close_redis_client(redis_client: Redis):
    """Closes the Redis client."""
    await redis_client.aclose()
