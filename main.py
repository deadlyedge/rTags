from typing import List, Dict, AsyncGenerator, Any
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, Field
from openai import OpenAI
import os
import hashlib
import redis.asyncio as redis
from redis.asyncio import Redis
from dotenv import load_dotenv # Add dotenv to load redis url

# Load environment variables from .env file
load_dotenv()

# Environment variables
PERPLEXITY_API_KEY = os.environ.get("PERPLEXITY_API_KEY")
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379")  # Default to localhost

if not PERPLEXITY_API_KEY:
    raise ValueError("PERPLEXITY_API_KEY environment variable not set.")

app = FastAPI(
    title="Tag Extractor API",
    description="Extracts relevant tags from text and reference websites using the Perplexity API.",
    version="1.0.0",
)


async def get_redis() -> AsyncGenerator[Redis, Any]:
    """Dependency to get a Redis connection."""
    redis_client = redis.from_url(REDIS_URL)
    try:
        yield redis_client
    finally:
        await redis_client.close()


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
    text: str, reference_websites: List[str], redis_client: Redis
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

    client = OpenAI(
        api_key=PERPLEXITY_API_KEY,
        base_url="https://api.perplexity.ai",
    )

    # Construct the prompt for the Perplexity API
    prompt = f"""
    You are a helpful assistant that extracts relevant tags from a given text and reference websites.
    Please extract 5 tags related to the given text based on the text and websites provided. Return only the tags.

    Text:
    {text}

    Reference Websites:
    {", ".join(reference_websites)}
    """

    try:
        response = client.chat.completions.create(
            model="sonar",  # or other models you prefer
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant that extracts relevant tags from a given text and reference websites. Please extract 5 tags related to the given text based on the text and websites provided.",
                },
                {"role": "user", "content": prompt},
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


@app.post("/extract_tags", response_model=TagResponse)
async def extract_tags(
    request: TagRequest, redis_client: Redis = Depends(get_redis)
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
        request.text, request.reference_websites, redis_client
    )
    return TagResponse(tags=tags)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
