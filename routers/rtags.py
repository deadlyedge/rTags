# routers/rtags.py
from typing import List, AsyncGenerator, Any
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from openai import OpenAI
import hashlib
from redis.asyncio import Redis
from utils.ai_utils import get_perplexity_client, get_redis_client, close_redis_client

router = APIRouter()


async def get_redis() -> AsyncGenerator[Redis, Any]:
    """Dependency to get a Redis connection."""
    redis_client = await get_redis_client()
    try:
        yield redis_client
    finally:
        await close_redis_client(redis_client)


class TagRequest(BaseModel):
    text: str = Field(..., description="The input text to analyze.")
    reference_websites: List[str] = Field(
        ..., description="A list of reference website URLs."
    )


class TagResponse(BaseModel):
    tags: List[str] = Field(..., description="The extracted tags.")


def generate_cache_key(text: str, reference_websites: List[str]) -> str:
    """Generates a unique cache key based on the input text and reference websites."""
    combined_input = text + ",".join(sorted(reference_websites))
    key = hashlib.sha256(combined_input.encode()).hexdigest()
    return key


async def get_tags_from_perplexity(
    text: str, reference_websites: List[str], redis_client: Redis, perplexity_client: OpenAI
) -> List[str]:
    """
    Gets relevant tags from the Perplexity API based on the provided text and reference websites.
    Uses Redis for caching.
    """
    cache_key = generate_cache_key(text, reference_websites)

    cached_result = await redis_client.get(cache_key)
    if cached_result:
        print("Cache hit!")
        # Redis stores data as bytes, so decode and split the string
        return cached_result.decode().split(",")

    print("Cache miss. Querying Perplexity API...")

    # Optimized prompt
    system_prompt = """You are a tag extraction assistant. Extract 5 relevant tags from the given text and reference websites. Return only the tags, separated by commas."""
    user_prompt = (
        f"""Text: {text}\nReference Websites: {", ".join(reference_websites)}"""
    )

    try:
        response = perplexity_client.chat.completions.create(
            model="sonar",  # or other models you prefer
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=50,
        )

        content = response.choices[0].message.content or ""
        tags = [tag.strip() for tag in content.split(",") if tag.strip()]
        if len(tags) < 5:
            tags = [tag.strip() for tag in content.split("\n") if tag.strip()]

        tags = tags[:5]

        # Store the result in Redis (as a comma-separated string)
        await redis_client.set(cache_key, ",".join(tags), ex=3600)  # 1 hour expiration
        return tags

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error communicating with Perplexity API: {e}"
        )


@router.post("", response_model=TagResponse)
async def extract_tags(
    request: TagRequest,
    redis_client: Redis = Depends(get_redis),
    perplexity_client: OpenAI = Depends(get_perplexity_client),
):
    """
    API endpoint to extract tags from the provided text and reference websites.
    Uses Redis for caching.
    """
    if not request.text:
        raise HTTPException(status_code=400, detail="Text cannot be empty.")
    if not request.reference_websites:
        raise HTTPException(
            status_code=400, detail="Reference websites list cannot be empty."
        )
    if len(request.reference_websites) > 10:
        raise HTTPException(
            status_code=400, detail="Too many reference websites(max 10)."
        )

    tags = await get_tags_from_perplexity(
        request.text, request.reference_websites, redis_client, perplexity_client
    )
    return TagResponse(tags=tags)
