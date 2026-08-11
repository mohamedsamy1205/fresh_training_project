import pytest_asyncio
from redis.asyncio import Redis


@pytest_asyncio.fixture
async def redis():
    client = Redis(
        host="redis",
        port=6379,
        decode_responses=True,
    )

    yield client

    await client.flushdb()
    await client.aclose()