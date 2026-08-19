# Financial & Investment Management Backend

Welcome to the official technical documentation for the FastAPI Financial & Investment Management Backend. This documentation serves as the authoritative reference for frontend engineers, system integration teams, and backend developers.

---

## 1. Project Purpose

The system provides a secure, production-grade financial platform designed for managing investment projects, investor wallets, transactional ledgers, treasury money movements, and platform user administration.

---

## 2. Main Business Idea

The platform enables investors to fund investment projects while enforcing strict financial, architectural, and operational guarantees:
- **Wallet & Treasury Management**: Every investor owns dedicated wallets. A central Company Treasury Vault facilitates deposits, withdrawals, and capital consolidation.
- **Double-Entry Ledger Accounting**: All money movements produce balanced debit and credit ledger entries (`ledger_entries`) alongside immutable transaction headers (`transactions`).
- **Project Lifecycle & Investment Flow**:
  1. Admins launch investment projects (`active`).
  2. Investors browse projects with real-time status and submit investment requests (`pending`).
  3. Admins approve (triggering atomic wallet-to-treasury debit/credit transfers) or reject requests.
  4. Active projects are closed upon reaching maturity (enforcing a strict minimum of **2 distinct active investors**) and valuation is deposited into the treasury.
  5. Profits/losses are distributed proportionally to investors, with a **20% company fee** automatically collected on net gains.
- **Financial & Concurrency Guarantees**:
  - Idempotency key tracking prevents double-spending and duplicate execution.
  - Deterministic row-level database locking (`SELECT ... FOR UPDATE` sorted by wallet UUID) prevents race conditions and deadlocks.
  - High-precision monetary utilities (`MoneyAmount`) ensure decimal precision and sanitize input representations.

---

## 3. Backend Architecture Overview

The codebase is organized into a modular layered architecture with clean separation of concerns:

```
app/
├── business/               # Business domain modules
│   ├── mony_movements/     # Treasury deposit & withdrawal engine, double-entry ledgers
│   ├── projects/           # Projects lifecycle, investments, requests, closures & analytics
│   ├── transaction/        # Transaction history and paginated audit queries
│   └── wallet/             # Investor & admin wallet management and balance tracking
├── common/                 # Common enums, pagination helpers, rate limiting & money utils
│   ├── enums.py            # Platform-wide enums (Roles, Statuses, Movement Types)
│   ├── pagination.py       # Reusable Page/Limit pagination schemas and query helpers
│   ├── rate_limit.py       # Redis-backed sliding window rate limiter dependency
│   └── utils/money.py      # Custom MoneyAmount type, validators & serializers
├── core/                   # Application core (config, DB, exceptions, security, telemetry)
│   ├── config.py           # Environment and pydantic settings
│   ├── database.py         # SQLAlchemy engine and session factory
│   ├── exception_handlers.py# Global exception handlers with OpenTelemetry tracing
│   ├── exceptions.py       # Standardized AppException hierarchy
│   ├── jwt_key_manager.py  # Asymmetric RSA key pair rotation & Redis JWKS manager
│   ├── redis.py            # Async Redis connection pool
│   ├── security.py         # RS256 token creation, claims & password hashing
│   ├── store.py            # Auth & permission dependencies (Bearer / Cookie)
│   └── telemetry.py        # OpenTelemetry instrumentation (FastAPI, SQLAlchemy, Redis)
├── platform/               # Platform infrastructural modules
│   ├── auth/               # Google OAuth2, local auth, JWKS & multi-session management
│   └── users/              # User administration, CRUD operations & role assignment
└── main.py                 # FastAPI application entrypoint, middleware & routing
```

---

## 4. Main Business Modules

| Module | Location | Description |
| :--- | :--- | :--- |
| **Auth** | `app/platform/auth` | Google OAuth2 login, local token refresh, JWKS public keys, and multi-session lifecycle management. |
| **Users** | `app/platform/users` | Admin user CRUD operations, UUID lookups, and role assignments. |
| **Wallets** | `app/business/wallet` | Investor and admin wallet management, rate-limited balance queries, and wallet creation. |
| **Transactions** | `app/business/transaction` | Paginated transaction audit trail queries with Page/Limit metadata. |
| **Money Movements** | `app/business/mony_movements` | Idempotent treasury deposits/withdrawals, deterministic wallet locking, and double-entry accounting. |
| **Projects** | `app/business/projects` | Project creation, investor discovery with personalized statuses, approval/rejection, closure valuation, and profit distribution. |
| **Pagination** | `app/common/pagination` | Standardized Page/Limit pagination utility (`PaginationParams`, `PagePaginationMeta`, `PaginatedResponse`). |
| **Rate Limiting** | `app/common/rate_limit` | Redis-backed rate limiting per user and endpoint (`RateLimitExceededException`). |
| **Telemetry** | `app/core/telemetry` | OpenTelemetry distributed tracing and structured logging for FastAPI, SQLAlchemy, and Redis. |

---

## 5. Authentication & Role-Based Access Control

The platform enforces Role-Based Access Control (RBAC) across three access tiers:
- **Public Endpoints**: Unauthenticated access (e.g., Google OAuth login/callback, token refresh, JWKS).
- **Admin Endpoints (`/admin/*`, `/projects`)**: Requires `require_admin` dependency (user role `admin`).
- **Investor Endpoints (`/investor/*`)**: Requires `require_investor` dependency (user role `investor`).
- **User-or-Admin Endpoints**: Requires `authorize_user_or_admin` or `get_current_user`.

Authentication credentials can be provided via **HTTP-only Cookies** (`access_token`, `refresh_token`) or the **Authorization Header** (`Bearer <token>`).

---

## 6. Financial Flow & Concurrency Overview

1. **Idempotency Deduplication**: All financial requests enforce idempotency keys. Repeated calls return existing transaction records without mutating wallet state.
2. **Deterministic Locking**: Inter-wallet transfers lock wallets ordered by UUID ascending (`lock_wallets`), preventing deadlocks under high concurrency.
3. **Double-Entry Balance Updates**: Every balance modification produces matching `DEBIT` and `CREDIT` records in `ledger_entries` linked to an immutable `transactions` header.
4. **Monetary Precision**: Amounts are validated against negative values, non-numeric formats, and large thresholds using the `MoneyAmount` custom Pydantic type (stored with 4 decimal places in PostgreSQL, serialized with 2 decimal places in JSON).

---

## 7. Database & Persistence Layer

The database layer utilizes **PostgreSQL** with **SQLAlchemy ORM** and **Alembic** migrations. Key tables include:
- `users`: User profiles, email credentials, provider (`google`, `local`), roles (`admin`, `admin_dev`, `investor`).
- `user_sessions`: Active and revoked authentication sessions with IP, user-agent, device name, and expiration.
- `wallets`: User and treasury financial balances with non-negative constraints.
- `transactions`: Immutable header records for financial events (`deposit`, `withdraw`, `transfer`, `investment`, `profit_payout`, `company_fee`).
- `ledger_entries`: Double-entry accounting records (`debit`, `credit`) with post-transaction balances.
- `projects`: Investment projects (`active`, `closed`, `distributed`).
- `investment_requests`: Investor investment applications (`pending`, `approved`, `rejected`).
- `investments`: Confirmed investment holdings linked to projects and user wallets.

---

## 8. Technology Stack

- **Framework**: FastAPI (Python 3.10+)
- **Validation**: Pydantic v2 & `pydantic-settings`
- **ORM & DB**: SQLAlchemy, PostgreSQL
- **Caching & Rate Limiting**: Redis (Async redis-py)
- **Migrations**: Alembic
- **Auth & Cryptography**: Authlib, PyJWT / python-jose, Cryptography (RSA/RS256), Passlib (bcrypt)
- **Observability**: OpenTelemetry SDK (FastAPI, SQLAlchemy, Redis instrumentation) with OTLP exporter (SigNoz / Jaeger)
- **Containerization**: Docker, Docker Compose
