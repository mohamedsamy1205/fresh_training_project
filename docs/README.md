# Financial & Investment Management Backend

Welcome to the official technical documentation for the FastAPI Financial & Investment Management Backend. This documentation serves as the authoritative reference for frontend engineers, system integration teams, and backend developers.

---

## 1. Project Purpose

The system provides a secure, production-grade financial platform designed for managing investment projects, investor wallets, transactional ledgers, treasury money movements, and platform user administration.

---

## 2. Main Business Idea

The platform enables investors to fund investment projects while enforcing strict financial and operational guarantees:
- **Wallet & Treasury Management**: Every investor owns a dedicated wallet. A central Company Treasury Vault facilitates deposits and withdrawals.
- **Double-Entry Ledger Accounting**: All money movements produce balanced debit and credit ledger entries alongside immutable transaction headers.
- **Project Lifecycle & Investment Flow**: Admins launch investment projects. Investors submit investment requests. Admins approve or reject requests. Active projects are closed upon reaching maturity (requiring a minimum of 2 active investors) and profits/losses are distributed proportionally.
- **Financial Guarantees**: Idempotency key tracking prevents double-spending or duplicate execution. Pessimistic row-level database locking (`SELECT ... FOR UPDATE`) prevents race conditions and deadlocks.

---

## 3. Backend Architecture Overview

The codebase is organized into a modular layered architecture:

```
app/
├── business/               # Business domain modules
│   ├── mony_movements/     # Treasury deposit & withdrawal engine
│   ├── projects/           # Projects, investments & analytics
│   ├── transaction/        # Transaction & ledger audit logs
│   └── wallet/             # Investor wallet management
├── common/                 # Common enums & shared utilities
├── core/                   # Application core (config, DB, exceptions, security)
├── platform/               # Platform infrastructural modules
│   ├── auth/               # Google OAuth2 & JWT token refresh
│   └── users/              # User management & administration
└── main.py                 # FastAPI application entrypoint
```

---

## 4. Main Business Modules

| Module | Location | Description |
| :--- | :--- | :--- |
| **Auth** | `app/platform/auth` | OAuth2 Google login and JWT refresh token management |
| **Users** | `app/platform/users` | User CRUD operations and role assignment |
| **Wallets** | `app/business/wallet` | Investor wallet creation and balance tracking |
| **Transactions** | `app/business/transaction` | Transaction history, sender queries, and paginated wallet logs |
| **Pagination** | `app/common/pagination` | Reusable Keyset (Cursor) and Limit-Offset pagination helper module |
| **Money Movements** | `app/business/mony_movements` | Idempotent treasury deposit and withdrawal operations with double-entry accounting |
| **Projects** | `app/business/projects` | Project creation, analytics, investment requests, project closing, and profit distribution |

---

## 5. Authentication & Role-Based Access Control

The platform enforces Role-Based Access Control (RBAC) across three access levels:
- **Public Endpoints**: Unauthenticated access (e.g., login, OAuth callbacks, token refresh).
- **Admin Endpoints (`/admin/*`)**: Requires `require_admin` dependency (user role `admin`).
- **Investor Endpoints (`/investor/*`)**: Requires `require_investor` dependency (user role `investor`).

Authentication tokens are issued as JWTs and stored securely in HTTP-only cookies (`access_token` and `refresh_token`).

---

## 6. Financial Flow & Concurrency Overview

Money movements adhere to strict financial standards:
1. **Idempotency Check**: Requests supply a unique `idempotency_key`. Duplicate submissions return cached transaction results without re-executing state changes.
2. **Pessimistic Locking**: Wallets are locked via `SELECT ... FOR UPDATE` ordered deterministically by primary key to avoid deadlocks (`AB-BA` ordering).
3. **Double-Entry Ledger**: Every deposit/withdrawal generates immutable credit and debit entries in `ledger_entries` alongside `transactions` records.

---

## 7. Database & Persistence Layer

The database layer utilizes **PostgreSQL** with **SQLAlchemy ORM** and **Alembic** migrations. Key tables include:
- `users`: User profiles, email credentials, roles (`admin`, `admin_dev`, `investor`).
- `wallets`: User and treasury financial balances (`user`, `treasury`).
- `transactions`: Immutable header records for financial transactions.
- `ledger_entries`: Double-entry accounting audit logs (`debit`, `credit`).
- `projects`: Investment projects (`active`, `closed`, `distributed`).
- `investment_requests`: Investor applications (`pending`, `approved`, `rejected`).
- `investments`: Confirmed project investments.

---

## 8. Technology Stack

- **Framework**: FastAPI (Python 3.10+)
- **Validation**: Pydantic v2
- **ORM & DB**: SQLAlchemy, PostgreSQL
- **Migrations**: Alembic
- **Auth**: Authlib, PyJWT / Passlib
- **Containerization**: Docker, Docker Compose
- **Environment**: WSL Linux
