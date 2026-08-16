# Authentication & Authorization Documentation

This document describes the authentication mechanisms, session management, token claims, available roles, and security dependencies enforced across the FastAPI backend.

---

## 1. Overview & Session-Based Authentication Flow

The application uses **Google OAuth2** for primary user authentication, **PostgreSQL UserSession** for device/session tracking, and **RS256 signed JWTs** for state verification.

```text
Login / Google Callback
  ↓
Create User Session (UserSession in PostgreSQL)
  ↓
Create Access Token + Refresh Token (both containing sid)
  ↓
Access Token authenticates API requests (payload decoded, user loaded only when needed)
  ↓
Refresh Token validates active session in database and issues new tokens
  ↓
User can view active sessions (GET /auth/sessions)
  ↓
User can revoke single session (DELETE /auth/sessions/{session_id})
  ↓
User can revoke all sessions (DELETE /auth/sessions)
```

---

## 2. JWT Tokens & Claims Structure

### Access Token Claims
- `sub`: User email
- `user_id`: User UUID
- `role`: Role string (`investor`, `admin`, `admin_dev`)
- `type`: `"access_token"`
- `permissions`: List of granted permission strings
- `sid`: Unique Session UUID
- `jti`: Unique token identifier UUID
- `iat`: Token issuance timestamp
- `exp`: Expiration timestamp (`ACCESS_TOKEN_EXPIRE_MINUTES`)

### Refresh Token Claims
- `sub`: User email
- `user_id`: User UUID
- `sid`: Unique Session UUID
- `type`: `"refresh_token"`
- `jti`: Unique token identifier UUID
- `iat`: Token issuance timestamp
- `exp`: Expiration timestamp (`REFRESH_TOKEN_EXPIRE_MINUTES`)

*(Note: Refresh tokens do not contain roles or permissions).*

---

## 3. Cookie Handling

| Cookie Name | Purpose | Expiration | Attributes |
| :--- | :--- | :--- | :--- |
| `access_token` | Primary JWT token for authenticating requests | `ACCESS_TOKEN_EXPIRE_MINUTES` (30 mins) | `HttpOnly=True`, `SameSite=lax`, `Secure=False` |
| `refresh_token` | JWT token used to validate session & refresh tokens | 7 Days | `HttpOnly=True`, `SameSite=lax`, `Secure=False` |

---

## 4. Security Dependencies

### 1. `get_access_payload`
- Extracts and validates `access_token` JWT payload without database lookup.

### 2. `get_refresh_payload`
- Extracts and validates `refresh_token` JWT payload without database lookup.

### 3. `get_current_user`
- Depends on `get_access_payload` and resolves the `User` from PostgreSQL by `user_id` (UUID).

### 4. `require_permission(permission: str)`
- Validates permissions directly from the decoded Access Token payload without loading the database User.

### 5. `require_admin` / `require_investor`
- Asserts appropriate user role.

---

## 5. Endpoints Documentation

### GET `/auth/google/login`
- **Role / Access**: Public
- **Summary**: Initiate Google OAuth2 login

### GET `/auth/google/callback`
- **Role / Access**: Public
- **Summary**: Google OAuth2 authentication callback
- **Behavior**: Authenticates user, creates a new `UserSession` tracking client device info, and issues `access_token` and `refresh_token` cookies with matching `sid`.

### POST `/auth/refresh`
- **Role / Access**: Public (requires valid `refresh_token` cookie)
- **Summary**: Refresh access and refresh tokens
- **Behavior**: Validates signature and claims, verifies that the session `sid` is not revoked and not expired, updates `last_seen`, and issues new token cookies retaining the session ID.

### GET `/auth/sessions`
- **Role / Access**: Authenticated
- **Summary**: List active user sessions
- **Response**: List of active sessions with device name, IP address, user agent, timestamps, and `is_current` flag.

### DELETE `/auth/sessions/{session_id}`
- **Role / Access**: Authenticated
- **Summary**: Revoke a specific session
- **Behavior**: Revokes the session if owned by the user. If the revoked session is the current active session, clears cookies.

### DELETE `/auth/sessions`
- **Role / Access**: Authenticated
- **Summary**: Revoke all user sessions
- **Behavior**: Revokes all active sessions for the authenticated user and clears cookies.

### POST `/auth/logout`
- **Role / Access**: Public / Authenticated
- **Summary**: Logout user
- **Behavior**: Revokes the active session and clears auth cookies.

