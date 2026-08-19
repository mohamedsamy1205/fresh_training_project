# Authentication & Session Management Documentation

This document describes the authentication architecture, session management, token claims, asymmetric key rotation, JWKS distribution, role permissions, and security dependencies implemented in the backend.

---

## 1. Overview & Session-Based Authentication Flow

The application uses **Google OAuth2** for identity verification, a database-backed **`UserSession`** model for active session/device tracking, and **RS256 signed JWTs** for stateless authorization.

```text
┌───────────────────────────┐
│     Google OAuth2 Login   │  (GET /auth/google/login)
└─────────────┬─────────────┘
              │
              ▼
┌───────────────────────────┐
│  Google Callback Handler  │  (GET /auth/google/callback)
│  - Extracts User Info     │
│  - Finds/Creates User     │
│  - Creates UserSession    │  (Stored in PostgreSQL: IP, User-Agent, Device)
│  - Signs Access & Refresh │  (Signed with RS256 using active RSA private key)
│  - Sets HTTP-Only Cookies │  (access_token, refresh_token)
└─────────────┬─────────────┘
              │
              ▼
┌───────────────────────────┐
│     API Request Auth      │  (Bearer Header OR access_token Cookie)
│  - Decoded via Public Key │
│  - Extracts user_id & sid │
│  - Verifies Permissions   │
└─────────────┬─────────────┘
              │
              ▼
┌───────────────────────────┐
│      Session Refresh      │  (POST /auth/refresh)
│  - Validates refresh_token│
│  - Checks Session active  │  (not revoked, not expired, user not locked)
│  - Updates last_seen      │
│  - Issues fresh JWT pair  │
└───────────────────────────┘
```

---

## 2. Asymmetric Key Management & JWKS (`JWTKeyManager`)

- **Dynamic RSA Key Pair**: Upon application startup (`lifespan` in `app/main.py`), a 2048-bit RSA key pair is generated dynamically with a unique Key ID (`kid`).
- **Redis Public Key Registry**: The public PEM string and current `kid` are published to Redis (`jwt:public_key`, `jwt:kid`).
- **JWKS Endpoint (`GET /auth/.well-known/jwks.json`)**: Exposes public keys formatted according to RFC 7517 (JSON Web Key Set) for external service verification:
  ```json
  {
    "keys": [
      {
        "kty": "RSA",
        "use": "sig",
        "alg": "RS256",
        "kid": "4a71bf5a-5282-4f27-a066-51d07c7a5223",
        "n": "uBv3...base64url...",
        "e": "AQAB"
      }
    ]
  }
  ```

---

## 3. JWT Tokens & Claims Structure

All tokens are signed using `RS256` and include a `kid` header matching the active RSA key pair.

### Access Token Claims (`type: "access_token"`)
| Claim | Type | Description |
| :--- | :--- | :--- |
| `sub` | `string` | User email address |
| `user_id` | `string (UUID)` | Unique User UUID |
| `role` | `string` | User role (`"investor"`, `"admin"`, `"admin_dev"`) |
| `type` | `string` | Literal `"access_token"` |
| `permissions`| `List[string]` | Granted granular permissions for the user's role |
| `sid` | `string (UUID)` | Associated `UserSession` UUID |
| `jti` | `string (UUID)` | Unique JWT identifier token UUID |
| `iat` | `integer (timestamp)` | Issuance timestamp (UTC) |
| `exp` | `integer (timestamp)` | Expiration timestamp (`ACCESS_TOKEN_EXPIRE_MINUTES`) |

### Refresh Token Claims (`type: "refresh_token"`)
| Claim | Type | Description |
| :--- | :--- | :--- |
| `sub` | `string` | User email address |
| `user_id` | `string (UUID)` | Unique User UUID |
| `sid` | `string (UUID)` | Associated `UserSession` UUID |
| `type` | `string` | Literal `"refresh_token"` |
| `jti` | `string (UUID)` | Unique JWT identifier token UUID |
| `iat` | `integer (timestamp)` | Issuance timestamp (UTC) |
| `exp` | `integer (timestamp)` | Expiration timestamp (`REFRESH_TOKEN_EXPIRE_MINUTES`) |

*(Note: Refresh tokens explicitly exclude `role` and `permissions` claims).*

---

## 4. Role Permissions Matrix (`ROLE_PERMISSIONS`)

Granular permissions are embedded into the Access Token claims:

| Permission String | Investor Role | Admin Role | Description |
| :--- | :---: | :---: | :--- |
| `wallet:read` | Yes | Yes | View user wallet balances and details |
| `wallet:update` | No | Yes | Create and update wallet records |
| `transaction:read` | Yes | Yes | View transaction history logs |
| `transaction:create` | No | Yes | Initiate financial transaction headers |
| `mony:deposit` | No | Yes | Execute treasury-backed wallet deposits |
| `mony:withdraw` | No | Yes | Execute treasury-backed wallet withdrawals |
| `project:read` | Yes | Yes | List investment projects |
| `project:request` | Yes | No | Submit project investment requests |
| `project:create` | No | Yes | Launch and manage new projects |
| `project:close` | No | Yes | Close active projects with final valuation |
| `project:distribute_profits` | No | Yes | Distribute pro-rata project profits and collect fees |

---

## 5. Security & Access Control Dependencies (`app/core/store.py`)

| Dependency | Purpose / Behavior |
| :--- | :--- |
| `get_jwt_key_manager` | Injects the active `JWTKeyManager` instance stored on `app.state`. |
| `get_access_payload` | Resolves and validates `access_token` from cookies or `Authorization: Bearer` header. Returns decoded payload dictionary. |
| `get_refresh_payload` | Resolves and validates `refresh_token` from cookies or `Authorization: Bearer` header. Returns decoded payload dictionary. |
| `get_current_user` | Depends on `get_access_payload`, resolves the `User` from PostgreSQL by `user_id` UUID, and verifies account is not locked (`is_locked=False`). |
| `require_admin` | Depends on `get_current_user` and enforces `role == UserRole.ADMIN` (`"admin"`). |
| `require_investor` | Depends on `get_current_user` and enforces `role == UserRole.INVESTOR` (`"investor"`). |
| `authorize_user_or_admin` | Depends on `get_current_user` and path parameter `user_id: UUID`. Grants access if user is Admin **OR** if `current_user.uuid == user_id`. |
| `require_permission(perm)`| Verifies permission directly from token payload without database query. |

---

## 6. Endpoints Catalog

### 1. GET `/auth/google/login`
- **Access**: Public
- **Summary**: Initiate Google OAuth2 login
- **Behavior**: Redirects the user to Google OAuth2 consent screen.

### 2. GET `/auth/google/callback`
- **Access**: Public
- **Summary**: Google OAuth2 authentication callback
- **Behavior**: Verifies Google auth code, retrieves user profile, creates user session, generates access/refresh tokens, and sets `access_token` and `refresh_token` HTTP-only cookies. Redirects to `/`.

### 3. POST `/auth/refresh`
- **Access**: Public (requires valid `refresh_token` cookie or Bearer header)
- **Summary**: Refresh access and refresh tokens
- **Behavior**: Decodes refresh token, validates that session is not revoked and not expired, verifies user is active, updates session `last_seen`, and sets refreshed cookies.

### 4. GET `/auth/.well-known/jwks.json`
- **Access**: Public
- **Summary**: Get JSON Web Key Set (JWKS)
- **Response**: List of public RSA keys with `kid`, `n`, `e`, `alg="RS256"`, `use="sig"`.

### 5. GET `/auth/me`
- **Access**: Authenticated (`get_current_user`)
- **Summary**: Get current logged-in user profile
- **Response**:
```json
{
  "uuid": "a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d",
  "name": "John Investor",
  "email": "john.investor@example.com",
  "role": "investor"
}
```

### 6. GET `/auth/sessions`
- **Access**: Authenticated (`get_access_payload`)
- **Summary**: List active user sessions
- **Response (`List[SessionResponse]`)**:
```json
[
  {
    "uuid": "e5f6a7b8-c9d0-1e2f-3a4b-5c6d7e8f9a0b",
    "device_name": "Mac",
    "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)...",
    "ip_address": "192.168.1.50",
    "created_at": "2026-08-19T08:00:00Z",
    "last_seen": "2026-08-19T08:45:00Z",
    "expires_at": "2026-08-26T08:00:00Z",
    "revoked": false,
    "revoked_at": null,
    "is_current": true
  }
]
```

### 7. DELETE `/auth/sessions/{session_id}`
- **Access**: Authenticated (`get_access_payload`)
- **Summary**: Revoke a specific session
- **Behavior**: Marks session as revoked (`revoked=True`, `revoked_at=utcnow`). If revoked session matches current active token `sid`, clears cookies.

### 8. DELETE `/auth/sessions`
- **Access**: Authenticated (`get_access_payload`)
- **Summary**: Revoke all user sessions
- **Behavior**: Revokes all active sessions for the current user and clears authentication cookies.

### 9. POST `/auth/logout`
- **Access**: Public / Authenticated
- **Summary**: Logout user
- **Behavior**: Best-effort revokes the session associated with the incoming token and clears `access_token` and `refresh_token` cookies.
