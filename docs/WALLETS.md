# Wallets & Money Movements API Documentation

This document describes investor wallet management under `/wallet` and administrative treasury money movements under `/admin/money-movements`.

---

## Data Schemas

### `WalletCreate` (Request Body)
| Field | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `user_id` | `string (UUID)` | Yes | UUID of the wallet owner |
| `name` | `string` | Yes | Human-readable label for the wallet |

### `WalletUpdate` (Internal Model)
| Field | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `Wallet_id` | `string (UUID)` | Yes | UUID of target wallet |
| `new_balance` | `string (MoneyAmount)` | Yes | Updated balance |

### `WalletResponse` (Response Schema)
| Field | Type | Field Name in JSON | Description |
| :--- | :--- | :--- | :--- |
| `Wallet_id` | `string (UUID)` | `uuid` | Unique wallet UUID |
| `balance` | `string (MoneyAmount)` | `balance` | Formatted decimal string with 2 decimal places (e.g. `"1500.50"`) |
| `wallet_name` | `string` | `name` | Name label of the wallet |

### `DepositRequest` / `WithdrawRequest` (Request Body)
| Field | Type | Required | Constraints | Description |
| :--- | :--- | :--- | :--- | :--- |
| `user_id` | `string (UUID)` | Yes | - | Target user UUID |
| `amount` | `string (MoneyAmount)` | Yes | `> 0.00` | Transaction monetary amount |
| `idempotency_key` | `string` | No | Auto-generated UUID if omitted | Unique deduplication key |
| `description` | `string` | No | Max 500 characters | Optional transaction note |

### `MoneyMovementResponse` (Response Schema)
| Field | Type | Description |
| :--- | :--- | :--- |
| `success` | `boolean` | Indicates successful execution |
| `duplicate` | `boolean` | `true` if request was deduplicated via idempotency key |
| `transaction` | `TransactionResponse` | Created or retrieved transaction header |
| `ledger_entries` | `List[LedgerEntryResponse]` | Generated double-entry debit/credit audit records |

### `TransactionResponse` (Sub-schema)
| Field | Type | Description |
| :--- | :--- | :--- |
| `uuid` | `string (UUID)` | Unique transaction UUID |
| `idempotency_key` | `string` | Transaction deduplication key |
| `user_id` | `string (UUID) \| null` | Associated user UUID |
| `wallet_id` | `string (UUID)` | Associated wallet UUID |
| `amount` | `string (MoneyAmount)` | Formatted monetary amount |
| `currency` | `string` | Currency code (`"USD"`) |
| `type` | `string (TransactionType)` | Enum: `deposit`, `withdraw`, `transfer`, `investment`, `profit_payout`, `company_fee` |
| `status` | `string (TransactionStatus)` | Enum: `pending`, `success`, `failed` |
| `description` | `string \| null` | Transaction description note |
| `created_at` | `string (datetime)` | ISO-8601 creation timestamp |

### `LedgerEntryResponse` (Sub-schema)
| Field | Type | Description |
| :--- | :--- | :--- |
| `uuid` | `string (UUID)` | Unique ledger entry UUID |
| `transaction_id` | `string (UUID)` | Associated transaction UUID |
| `wallet_id` | `string (UUID)` | Affected wallet UUID |
| `entry_type` | `string (LedgerEntryType)` | Entry type: `debit` or `credit` |
| `amount` | `string (MoneyAmount)` | Delta monetary amount |
| `balance_after` | `string (MoneyAmount)` | Wallet balance immediately after the entry |
| `created_at` | `string (datetime)` | ISO-8601 creation timestamp |

---

## Investor & Admin Wallet Endpoints (`/wallet`)

### 1. GET `/wallet/admin/{user_id}`
- **Role / Access**: Admin OR Self (`authorize_user_or_admin`)
- **Rate Limit**: 5 requests / 60 seconds
- **Summary**: Get wallet by user ID
- **Description**: Retrieves all wallets belonging to the specified user UUID.
- **Path Parameters**:
  - `user_id` (`string (UUID)`, Required): UUID of the user.
- **Response (`200 OK - List[WalletResponse]`)**:
```json
[
  {
    "uuid": "b2c3d4e5-f6a7-8b9c-0d1e-2f3a4b5c6d7e",
    "balance": "1500.50",
    "name": "Main Investor Wallet"
  }
]
```
- **Errors**:
  - `401 Unauthorized`: Not authenticated.
  - `403 Forbidden`: Access restricted to admins or the matching user.
  - `429 Too Many Requests`: Rate limit exceeded.

---

### 2. POST `/wallet/admin`
- **Role / Access**: Admin Only (`require_admin`)
- **Rate Limit**: 3 requests / 86400 seconds (1 day)
- **Summary**: Create investor wallet
- **Description**: Creates a new financial wallet account for an investor user.
- **Headers**: `Content-Type: application/json`
- **Request Body (`WalletCreate`)**:
```json
{
  "user_id": "a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d",
  "name": "Growth Savings Wallet"
}
```
- **Response (`200 OK - WalletResponse`)**:
```json
{
  "uuid": "b2c3d4e5-f6a7-8b9c-0d1e-2f3a4b5c6d7e",
  "balance": "0.00",
  "name": "Growth Savings Wallet"
}
```
- **Errors**:
  - `401 Unauthorized`: Not authenticated.
  - `403 Forbidden`: Admin role required.
  - `429 Too Many Requests`: Rate limit exceeded.

---

### 3. GET `/wallet/me`
- **Role / Access**: Authenticated Users (`get_current_user`)
- **Rate Limit**: 5 requests / 60 seconds
- **Summary**: Get current user wallet info
- **Description**: Retrieves wallets owned by the currently authenticated session user.
- **Response (`200 OK - List[WalletResponse]`)**:
```json
[
  {
    "uuid": "b2c3d4e5-f6a7-8b9c-0d1e-2f3a4b5c6d7e",
    "balance": "1500.50",
    "name": "Primary Investment Wallet"
  }
]
```
- **Errors**:
  - `401 Unauthorized`: Not authenticated.
  - `429 Too Many Requests`: Rate limit exceeded.

---

## Treasury Money Movements Endpoints (`/admin/money-movements`)

### 4. POST `/admin/money-movements/deposit`
- **Role / Access**: Admin Only (`require_admin`)
- **Status Code**: `201 Created`
- **Summary**: Deposit funds into user wallet & treasury
- **Description**: Executes a double-entry deposit into a user's wallet and company treasury vault with deterministic row locking and idempotency deduplication.
- **Headers**: `Content-Type: application/json`
- **Request Body (`DepositRequest`)**:
```json
{
  "user_id": "a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d",
  "amount": "5000.00",
  "idempotency_key": "DEP-2026-0819-001",
  "description": "Wire transfer deposit"
}
```
- **Response (`201 Created - MoneyMovementResponse`)**:
```json
{
  "success": true,
  "duplicate": false,
  "transaction": {
    "uuid": "c3d4e5f6-a7b8-9c0d-1e2f-3a4b5c6d7e8f",
    "idempotency_key": "DEP-2026-0819-001",
    "user_id": "a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d",
    "wallet_id": "b2c3d4e5-f6a7-8b9c-0d1e-2f3a4b5c6d7e",
    "amount": "5000.00",
    "currency": "USD",
    "type": "deposit",
    "status": "success",
    "description": "Wire transfer deposit",
    "created_at": "2026-08-19T08:30:00Z"
  },
  "ledger_entries": [
    {
      "uuid": "e5f6a7b8-c9d0-1e2f-3a4b-5c6d7e8f9a0b",
      "transaction_id": "c3d4e5f6-a7b8-9c0d-1e2f-3a4b5c6d7e8f",
      "wallet_id": "b2c3d4e5-f6a7-8b9c-0d1e-2f3a4b5c6d7e",
      "entry_type": "credit",
      "amount": "5000.00",
      "balance_after": "5000.00",
      "created_at": "2026-08-19T08:30:00Z"
    },
    {
      "uuid": "f6a7b8c9-d0e1-2f3a-4b5c-6d7e8f9a0b1c",
      "transaction_id": "c3d4e5f6-a7b8-9c0d-1e2f-3a4b5c6d7e8f",
      "wallet_id": "00000000-0000-0000-0000-000000000001",
      "entry_type": "credit",
      "amount": "5000.00",
      "balance_after": "105000.00",
      "created_at": "2026-08-19T08:30:00Z"
    }
  ]
}
```
- **Errors**:
  - `400 Bad Request`: Invalid amount (`INVALID_OPERATION`).
  - `401 Unauthorized`: Not authenticated.
  - `403 Forbidden`: Admin role required.
  - `404 Not Found`: User wallet or treasury wallet not found.

---

### 5. POST `/admin/money-movements/withdraw`
- **Role / Access**: Admin Only (`require_admin`)
- **Status Code**: `200 OK`
- **Summary**: Withdraw funds from user wallet & treasury
- **Description**: Withdraws funds from a user's wallet and treasury vault, verifying sufficient balance and recording double-entry debit audit entries.
- **Headers**: `Content-Type: application/json`
- **Request Body (`WithdrawRequest`)**:
```json
{
  "user_id": "a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d",
  "amount": "1000.00",
  "idempotency_key": "WTH-2026-0819-002",
  "description": "Investor withdrawal payout"
}
```
- **Response (`200 OK - MoneyMovementResponse`)**: Same schema as deposit, with `entry_type: "debit"`.
- **Errors**:
  - `400 Bad Request`: `WALLET_INSUFFICIENT_BALANCE` (User wallet balance < withdrawal amount).
  - `401 Unauthorized`: Not authenticated.
  - `403 Forbidden`: Admin role required.
  - `404 Not Found`: User wallet or treasury wallet not found.

---

## Concurrency & Financial Accounting Mechanics

1. **Deterministic Locking Order**:
   To prevent deadlocks between concurrent transfers involving multiple wallets, `lock_wallets` sorts all target wallet UUIDs ascending before executing `SELECT ... FOR UPDATE`.
2. **Idempotency Deduplication**:
   If an existing transaction with the same `idempotency_key` is detected, the operation short-circuits and returns the existing transaction and its ledger entries with `duplicate: true`.
3. **Double-Entry Balance Updates**:
   - `DEPOSIT`: Increases user wallet balance and increases treasury wallet balance.
   - `WITHDRAW`: Decreases user wallet balance and decreases treasury wallet balance.
   - `INVESTMENT`: Decreases investor wallet balance and increases treasury wallet balance.
   - `PROFIT_PAYOUT`: Decreases treasury wallet balance and increases investor wallet balance.
