import base64
import uuid

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa


class JWTKeyManager:
    REDIS_PUBLIC_KEY = "jwt:public_key"
    REDIS_KID = "jwt:kid"

    def __init__(self, redis):
        self.redis = redis

        self.private_key = None
        self.public_key = None
        self.kid = None

    async def initialize(self):
        """
        Generate a completely new RSA key pair
        every time the application starts.
        """

        # Generate private key
        self.private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )

        # Derive public key
        self.public_key = self.private_key.public_key()

        # Generate new key ID
        self.kid = str(uuid.uuid4())

        # Store ONLY public information in Redis
        public_pem = self.public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        ).decode("utf-8")

        await self.redis.set(
            self.REDIS_PUBLIC_KEY,
            public_pem,
        )

        await self.redis.set(
            self.REDIS_KID,
            self.kid,
        )

    def get_private_key(self):
        if self.private_key is None:
            raise RuntimeError("JWT key manager is not initialized")

        return self.private_key

    def get_public_key(self):
        if self.public_key is None:
            raise RuntimeError("JWT key manager is not initialized")

        return self.public_key

    def get_kid(self):
        if self.kid is None:
            raise RuntimeError("JWT key manager is not initialized")

        return self.kid

    def get_jwks(self):
        """
        Return current public key in JWKS format.
        """

        public_numbers = self.get_public_key().public_numbers()

        n = self._base64url_encode(
            public_numbers.n.to_bytes(
                (public_numbers.n.bit_length() + 7) // 8,
                byteorder="big",
            )
        )

        e = self._base64url_encode(
            public_numbers.e.to_bytes(
                (public_numbers.e.bit_length() + 7) // 8,
                byteorder="big",
            )
        )

        return {
            "keys": [
                {
                    "kty": "RSA",
                    "use": "sig",
                    "alg": "RS256",
                    "kid": self.get_kid(),
                    "n": n,
                    "e": e,
                }
            ]
        }

    @staticmethod
    def _base64url_encode(value: bytes) -> str:
        return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")