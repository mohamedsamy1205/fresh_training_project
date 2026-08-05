# Authentication & Authorization Documentation

This document describes the authentication mechanisms, token management, available roles, and security dependencies enforced across the FastAPI backend.

---

## 1. Overview & Login Flow

The application uses **Google OAuth2** for primary user authentication and **JWT (JSON Web Tokens)** for session management.

### Google OAuth2 Login Flow
1. **Initiate Login**: Client issues `GET /auth/google/login`.
2. **Google Redirect**: Server redirects client to Google OAuth2 authorization page.
3. **User Authentication**: User grants access on Google.
4. **OAuth Callback**: Google redirects user back to `GET /auth/google/callback`.
5. **Token Generation & Cookie Setting**:
   - The server extracts user info (email, name).
   - If the user does not exist in the database, a new user profile is created with default role `investor` and provider `google`.
   - The server signs an `access_token` (expires based on `ACCESS_TOKEN_EXPIRE_MINUTES`) and a `refresh_token` (expires in 7 days).
   - The tokens are set in the client browser as `HTTPOnly` cookies.

---

## 2. JWT & Cookie Handling

Tokens are stored in client cookies rather than Authorization headers:

| Cookie Name | Purpose | Expiration | Attributes |
| :--- | :--- | :--- | :--- |
| `access_token` | Primary JWT token for authenticating requests | `ACCESS_TOKEN_EXPIRE_MINUTES` (e.g., 30 mins) | `HttpOnly=True`, `SameSite=lax`, `Secure=False` |
| `refresh_token` | JWT token used to issue new `access_token` pairs | 7 Days | `HttpOnly=True`, `SameSite=lax`, `Secure=False` |

---

## 3. User Roles

Defined in `app.common.enums.UserRole`:

- `admin`: Full system access, money movements, project creation/closing, profit distribution, user administration.
- `admin_dev`: Developer/administrator role.
- `investor`: Investor user role for managing individual wallets, creating transactions, and submitting project investment requests.

---

## 4. Security Dependencies

The security layer (`app/core/security.py`) provides three FastAPI dependencies:

### 1. `get_current_user`
- **Behavior**: Extracts `access_token` cookie from request. Decodes JWT payload, validates `sub` claim (user email), and queries `User` from PostgreSQL database.
- **Error Behavior**:
  - `401 Unauthorized`: Token missing, invalid, or expired.
  - `401 Unauthorized` / `404 Not Found`: User payload invalid or user not found.

### 2. `require_admin`
- **Behavior**: Invokes `get_current_user`. Asserts `current_user.role == UserRole.ADMIN`.
- **Error Behavior**:
  - `403 Forbidden`: User role is not `admin`.

### 3. `require_investor`
- **Behavior**: Invokes `get_current_user`. Asserts `current_user.role == UserRole.INVESTOR`.
- **Error Behavior**:
  - `403 Forbidden`: User role is not `investor`.

---

## 5. Endpoints Documentation

### GET `/auth/google/login`
- **Role / Access**: Public
- **Summary**: Initiate Google OAuth2 login
- **Description**: Redirects the user browser to Google's OAuth2 authorization page.
- **Headers**: None
- **Query Parameters**: None
- **Response**: `302 Found` redirect to Google OAuth2 URL.

---

### GET `/auth/google/callback`
- **Role / Access**: Public
- **Summary**: Google OAuth2 authentication callback
- **Description**: Handles callback code from Google, creates user if missing, generates JWT tokens, and sets `access_token` & `refresh_token` HTTP-only cookies.
- **Headers**: None
- **Query Parameters**: Provided automatically by Google (`code`, `state`).
- **Response**: `302 Found` redirect to `http://localhost:8000/docs` with `Set-Cookie` headers.

---

### POST `/auth/refresh`
- **Role / Access**: Public (requires valid `refresh_token` cookie)
- **Summary**: Refresh access token
- **Description**: Reads `refresh_token` from request cookies, validates token signature, and issues a new access token pair.
- **Headers**: `Content-Type: application/json`
- **Cookies**: `refresh_token` (Required)
- **Request Body**: None
- **Response Schema (`200 OK`)**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1Ni...",
  "refresh_token": "eyJhbGciOiJIUzI1Ni...",
  "token_type": "bearer"
}
```
- **Error Responses**:
  - `401 Unauthorized`: `{"detail": "No refresh token"}` or `{"success": false, "error": {"code": "UNAUTHORIZED", "message": "Invalid or expired token"}}`
