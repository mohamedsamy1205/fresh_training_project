import pytest
from cryptography.hazmat.primitives import serialization

from app.core.jwt_key_manager import JWTKeyManager


@pytest.mark.asyncio
async def test_generate_new_keys_on_startup(redis):

    key_manager = JWTKeyManager(redis)

    # First startup
    await key_manager.initialize()

    first_kid = key_manager.get_kid()
    first_public_key = key_manager.get_public_key()

    # Second startup
    await key_manager.initialize()

    second_kid = key_manager.get_kid()
    second_public_key = key_manager.get_public_key()

    # New keys should be generated
    assert first_kid != second_kid
    assert first_public_key != second_public_key

    # Redis should contain the latest key
    stored_kid = await redis.get("jwt:kid")
    stored_public_key = await redis.get("jwt:public_key")

    assert stored_kid == second_kid

    assert stored_public_key == second_public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode("utf-8")