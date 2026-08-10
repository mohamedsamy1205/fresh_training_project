from app.core.exceptions import RateLimitExceededException
from app.core.store import get_current_user
from app.platform.users.model.user import User
from fastapi import Depends, HTTPException, Request, status
from redis.asyncio import Redis

from app.core.redis import get_redis


class RateLimiter:
    def __init__(
        self,
        redis: Redis,
        limit: int,
        window: int,
    ):
        self.redis = redis
        self.limit = limit
        self.window = window

    async def __call__(
        self,
        request: Request,
        current_user
    ):

        userId = current_user.uuid
        endpoint = request.url.path

        key = f"rate_limit:{userId}:{endpoint}"

        current_count = await self.redis.incr(key)

        if current_count == 1:
            await self.redis.expire(key, self.window)

        if current_count > self.limit:
            raise RateLimitExceededException(
                details={
                    "limit": self.limit,
                    "window": f"{self.window} sec",
                }
            )


def rate_limit(limit: int, window: int):

    async def dependency(
        request: Request,
        redis: Redis = Depends(get_redis),
        current_user: User = Depends(get_current_user)
    ):
        limiter = RateLimiter(
            redis=redis,
            limit=limit,
            window=window,
        )

        await limiter(request,current_user)

    return dependency