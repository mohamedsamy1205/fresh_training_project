# API Overview & Route Catalog

This document outlines the global API organization, route prefixes, access control dependencies, rate limits, and the comprehensive route catalog for the FastAPI Financial & Investment Backend.

---

## 1. Global API Information

- **Base URL**: `http://localhost:8000`
- **Interactive OpenAPI (Swagger) Documentation**: `http://localhost:8000/docs`
- **ReDoc Documentation**: `http://localhost:8000/redoc`
- **Default Content-Type**: `application/json`
- **Supported Authentication Schemes**:
  - HTTP-only Cookies (`access_token`, `refresh_token`)
  - Authorization Header (`Bearer <JWT_ACCESS_TOKEN>`)

---

## 2. Route Architecture & Prefixes

Endpoints are organized into modular routers categorized by domain and access tier:

| Domain / Category | Route Prefix | Access Control Dependency | Description |
| :--- | :--- | :--- | :--- |
| **Auth & Sessions** | `/auth` | Public / `get_access_payload` | OAuth2 Google login, token refresh, JWKS, and session management. |
| **Admin Users** | `/admin/users` | `require_admin` | Administrative CRUD operations, list pagination, and role assignment. |
| **Wallets** | `/wallet` | `authorize_user_or_admin` / `require_admin` / `get_current_user` | Rate-limited wallet creation and balance queries. |
| **Transactions** | `/investor/transactions` | `get_current_user` | Page/Limit paginated financial transaction audit trails. |
| **Money Movements** | `/admin/money-movements` | `require_admin` | Idempotent treasury deposits and withdrawals with double-entry ledgers. |
| **Projects (Admin)** | `/admin/projects` | `require_admin` | Project creation, analytics, request approvals, closures, and profit distributions. |
| **Projects (Investor)**| `/investor/projects` | `require_investor` | Investor project investment request submissions. |
| **Projects (General)** | `/projects` | `get_current_user` / `require_admin` | Global cached project listings with personalized investor statuses and creation. |

---

## 3. Complete Route Map

| Method | Endpoint Path | Access Level | Rate Limit | Summary | Tag |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **GET** | `/auth/google/login` | Public | - | Initiate Google OAuth2 login | Auth |
| **GET** | `/auth/google/callback` | Public | - | Google OAuth2 authentication callback | Auth |
| **POST** | `/auth/refresh` | Public | - | Refresh access & refresh tokens | Auth |
| **GET** | `/auth/.well-known/jwks.json` | Public | - | Get public keys in JWKS format | Auth |
| **GET** | `/auth/me` | Authenticated | - | Get current logged-in user details | Auth |
| **GET** | `/auth/sessions` | Authenticated | - | List active user sessions | Auth |
| **DELETE** | `/auth/sessions/{session_id}` | Authenticated | - | Revoke a specific user session | Auth |
| **DELETE** | `/auth/sessions` | Authenticated | - | Revoke all user sessions | Auth |
| **POST** | `/auth/logout` | Public / Auth | - | Logout user & revoke session | Auth |
| **POST** | `/admin/users` | Admin | - | Create user account | Admin Users |
| **GET** | `/admin/users/get/{user_id}` | Admin | - | Get user details by UUID | Admin Users |
| **GET** | `/admin/users` | Admin | - | List all users (paginated & sorted) | Admin Users |
| **GET** | `/admin/users/users` | Admin | - | Get all users alias (limit: 100) | Admin Users |
| **PUT** | `/admin/users/{user_id}` | Admin | - | Update user details by UUID | Admin Users |
| **DELETE** | `/admin/users/{user_id}` | Admin | - | Delete user account by UUID | Admin Users |
| **GET** | `/wallet/admin/{user_id}` | Admin or Self | 5 req / 60s | Get wallet list for a user UUID | Investor Wallet |
| **POST** | `/wallet/admin` | Admin | 3 req / day | Create investor wallet | Investor Wallet |
| **GET** | `/wallet/me` | Authenticated | 5 req / 60s | Get current logged-in user wallets | Investor Wallet |
| **GET** | `/investor/transactions/user/{user_id}` | Authenticated | 5 req / 60s | Get paginated transactions by sender user UUID | Investor Transactions |
| **POST** | `/admin/money-movements/deposit` | Admin | - | Deposit funds into user wallet & treasury (201 Created) | Admin Money Movements |
| **POST** | `/admin/money-movements/withdraw` | Admin | - | Withdraw funds from user wallet & treasury (200 OK) | Admin Money Movements |
| **GET** | `/projects` | Authenticated | - | List all projects with cached response & investor status | Admin Projects |
| **POST** | `/projects` | Admin | - | Generic project creation endpoint (201 Created) | Admin Projects |
| **POST** | `/admin/projects` | Admin | - | Create investment project (201 Created) | Admin Projects |
| **GET** | `/admin/projects/{project_id}/analytics` | Admin | - | Get project investment analytics & metrics | Admin Projects |
| **GET** | `/admin/projects/{project_id}/investment-requests` | Admin | - | List all investment requests for a project | Admin Projects |
| **DELETE** | `/admin/projects/{project_id}` | Admin | - | Delete project and all associated records | Admin Projects |
| **POST** | `/admin/projects/requests/{request_id}/approve` | Admin | - | Approve investment request with idempotency key | Admin Projects |
| **POST** | `/admin/projects/requests/{request_id}/reject` | Admin | - | Reject investment request | Admin Projects |
| **POST** | `/admin/projects/{project_id}/close` | Admin | - | Close active project (requires $\ge 2$ investors) | Admin Projects |
| **POST** | `/admin/projects/{project_id}/distribute-profits` | Admin | - | Distribute pro-rata profits/losses with 20% fee | Admin Projects |
| **POST** | `/investor/projects/{project_id}/investment-requests` | Investor | - | Submit investment request for active project | Investor Projects |

---

## 4. Request & Response Standards

### Authentication Headers & Cookies
Requests to protected endpoints accept credentials via either:
1. **Cookie** (Automatic in browser sessions):
   ```http
   Cookie: access_token=<JWT_ACCESS_TOKEN>; refresh_token=<JWT_REFRESH_TOKEN>
   ```
2. **Authorization Header** (Standard for API clients / mobile):
   ```http
   Authorization: Bearer <JWT_ACCESS_TOKEN>
   ```

### Standardized Error Format
All application errors follow the structured JSON error envelope:

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE_STRING",
    "message": "Human-readable explanation of error",
    "details": null
  }
}
```

### Monetary Formatting Standard (`MoneyAmount`)
- Monetary numbers are represented as clean decimal strings formatted to **2 fixed decimal places** (e.g. `"1500.50"`, `"0.00"`).
- Leading zeros are sanitized automatically (e.g. `"00050.00"` $\to$ `"50.00"`).
- Database persistence uses PostgreSQL `NUMERIC(18, 4)` for high-precision math without rounding errors.
