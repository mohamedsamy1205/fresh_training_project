# API Overview & Route Map

This document outlines the API organization, route prefixes, global conventions, and full route catalog for the FastAPI Financial System.

---

## 1. Global API Information

- **Base URL**: `http://localhost:8000`
- **Interactive Swagger Documentation**: `http://localhost:8000/docs`
- **ReDoc Documentation**: `http://localhost:8000/redoc`
- **Default Content Type**: `application/json`

---

## 2. Route Architecture & Prefixes

Endpoints are strictly organized by role-based route prefixes:

| Role / Category | Route Prefix | Access Control Dependency | Description |
| :--- | :--- | :--- | :--- |
| **Public / Auth** | `/auth` | None | Open authentication, OAuth callbacks, and token refresh endpoints. |
| **Admin** | `/admin` | `require_admin` | Administrative management of users, treasury money movements, and projects. |
| **Investor** | `/investor` | `require_investor` | Investor-facing wallet management, transactions, and investment submission. |

---

## 3. Complete Route Map

| Method | Endpoint Path | Role | Summary | Tag |
| :--- | :--- | :--- | :--- | :--- |
| **GET** | `/auth/google/login` | Public | Initiate Google OAuth2 login | Auth |
| **GET** | `/auth/google/callback` | Public | Google OAuth2 authentication callback | Auth |
| **POST** | `/auth/refresh` | Public | Refresh access token | Auth |
| **POST** | `/admin/users` | Admin | Create user | Admin Users |
| **GET** | `/admin/users/{user_id}` | Admin | Get user details | Admin Users |
| **GET** | `/admin/users` | Admin | List all users | Admin Users |
| **PUT** | `/admin/users/{user_id}` | Admin | Update user details | Admin Users |
| **DELETE** | `/admin/users/{user_id}` | Admin | Delete user account | Admin Users |
| **GET** | `/investor/wallet/{user_id}` | Investor | Get wallet by user ID | Investor Wallet |
| **POST** | `/investor/wallet` | Investor | Create investor wallet | Investor Wallet |
| **POST** | `/investor/wallet/update_blance` | Investor | Update wallet balance | Investor Wallet |
| **POST** | `/investor/transactions` | Investor | Create transaction | Investor Transactions |
| **GET** | `/investor/transactions/sender/{user_id}` | Investor | Get transactions by sender ID | Investor Transactions |
| **GET** | `/investor/transactions/wallet/{wallet_id}` | Investor | Get transactions by wallet ID | Investor Transactions |
| **POST** | `/admin/money-movements/deposit` | Admin | Deposit funds into user wallet | Admin Money Movements |
| **POST** | `/admin/money-movements/withdraw` | Admin | Withdraw funds from user wallet | Admin Money Movements |
| **POST** | `/admin/projects` | Admin | Create investment project | Admin Projects |
| **GET** | `/admin/projects/{project_id}/analytics` | Admin | Get project investment analytics | Admin Projects |
| **POST** | `/admin/projects/requests/{request_id}/approve` | Admin | Approve investment request | Admin Projects |
| **POST** | `/admin/projects/requests/{request_id}/reject` | Admin | Reject investment request | Admin Projects |
| **POST** | `/admin/projects/{project_id}/close` | Admin | Close active project | Admin Projects |
| **POST** | `/admin/projects/{project_id}/distribute-profits` | Admin | Distribute project profits/losses | Admin Projects |
| **POST** | `/investor/projects/{project_id}/investment-requests` | Investor | Submit investment request | Investor Projects |

---

## 4. Request & Response Standards

### Request Headers
Most requests require:
```http
Content-Type: application/json
```

For protected routes, authentication cookies must be supplied:
```http
Cookie: access_token=<JWT_ACCESS_TOKEN>
```

### Standardized Error Format
All application errors return a structured JSON body with HTTP status code:
```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE_STRING",
    "message": "Human-readable error explanation",
    "details": null
  }
}
```
