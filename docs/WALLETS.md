# Wallets & Money Movements API Documentation

This document covers investor wallet operations under `/investor/wallet` and administrative treasury money movements under `/admin/money-movements`.

---

## Data Schemas

### `WalletCreate`
| Field | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `user_id` | `string (UUID)` | Yes | UUID of the user owner |
| `name` | `string` | Yes | Wallet name label |

### `WalletUpdate`
| Field | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `Wallet_id` | `string (UUID)` | Yes | UUID of target wallet |
| `new_balance` | `decimal` | Yes | New balance value |

### `WalletResponse`
| Field | Type | Alias | Description |
| :--- | :--- | :--- | :--- |
| `Wallet_id` | `string (UUID)` | `uuid` | Wallet UUID |
| `balance` | `decimal` | - | Current wallet balance |
| `wallet_name` | `string` | `name` | Name of wallet |

### `DepositRequest` / `WithdrawRequest`
| Field | Type | Required | Constraints | Description |
| :--- | :--- | :--- | :--- | :--- |
| `user_id` | `string (UUID)` | Yes | - | User UUID |
| `amount` | `decimal` | Yes | `> 0.00` | Positive transaction amount |
| `idempotency_key` | `string` | Yes | Length: 8-255 | Unique deduplication key |
| `description` | `string` | No | Max 500 chars | Optional description |

### `MoneyMovementResponse`
| Field | Type | Description |
| :--- | :--- | :--- |
| `success` | `boolean` | Indicates execution success |
| `duplicate` | `boolean` | `true` if request was deduplicated via idempotency key |
| `transaction_ids` | `array[string (UUID)]` | Created transaction UUIDs |
| `amount` | `decimal` | Transaction amount |
| `currency` | `string` | Currency code (`"USD"`) |
| `description` | `string \| null` | Transaction description |
| `transactions` | `array[object]` | Generated transaction objects |
| `ledger_entries` | `array[object]` | Double-entry credit/debit audit logs |

---

## Investor Wallet Endpoints

### 1. GET `/investor/wallet/{user_id}`
- **Role / Access**: Investor Only (`require_investor`)
- **Summary**: Get wallet by user ID
- **Description**: Retrieves wallet details and current balance for a specified investor user UUID.
- **Headers**: None
- **Cookies**: `access_token` (Required)
- **Path Parameters**:
  - `user_id` (`string (UUID)`, Required): UUID of the user.
- **Response (`200 OK - List[WalletResponse]`)**:
```json
[
  {
    "uuid": "b2c3d4e5-f6a7-8b9c-0d1e-2f3a4b5c6d7e",
    "balance": 1500.50,
    "name": "Main Investor Wallet"
  }
]
```
- **Errors**:
  - `401 Unauthorized`: Authentication required.
  - `403 Forbidden`: Investor role required.
  - `404 Not Found`: Wallet not found.

---

### 2. POST `/investor/wallet`
- **Role / Access**: Investor Only (`require_investor`)
- **Summary**: Create investor wallet
- **Description**: Creates a new wallet account for an investor user.
- **Headers**: `Content-Type: application/json`
- **Cookies**: `access_token` (Required)
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
  "balance": 0.00,
  "name": "Growth Savings Wallet"
}
```
- **Errors**:
  - `401 Unauthorized`: Not authenticated.
  - `403 Forbidden`: Investor role required.

---

### 3. POST `/investor/wallet/update_blance`
- **Role / Access**: Investor Only (`require_investor`)
- **Summary**: Update wallet balance
- **Description**: Directly updates the financial balance of an investor's wallet.
- **Headers**: `Content-Type: application/json`
- **Cookies**: `access_token` (Required)
- **Request Body (`WalletUpdate`)**:
```json
{
  "Wallet_id": "b2c3d4e5-f6a7-8b9c-0d1e-2f3a4b5c6d7e",
  "new_balance": 2500.00
}
```
- **Response (`200 OK - WalletResponse`)**:
```json
{
  "uuid": "b2c3d4e5-f6a7-8b9c-0d1e-2f3a4b5c6d7e",
  "balance": 2500.00,
  "name": "Growth Savings Wallet"
}
```
- **Errors**:
  - `401 Unauthorized`: Not authenticated.
  - `403 Forbidden`: Investor role required.

---

## Treasury Money Movements Endpoints (Admin)

### 4. POST `/admin/money-movements/deposit`
- **Role / Access**: Admin Only (`require_admin`)
- **Summary**: Deposit funds into user wallet
- **Description**: Executes a treasury-backed deposit into a user's wallet using atomic double-entry accounting and idempotency deduplication.
- **Headers**: `Content-Type: application/json`
- **Cookies**: `access_token` (Required)
- **Request Body (`DepositRequest`)**:
```json
{
  "user_id": "a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d",
  "amount": 5000.00,
  "idempotency_key": "DEP-2026-0805-0019283",
  "description": "Wire transfer deposit"
}
```
- **Response (`201 Created - MoneyMovementResponse`)**:
```json
{
  "success": true,
  "duplicate": false,
  "transaction_ids": [
    "c3d4e5f6-a7b8-9c0d-1e2f-3a4b5c6d7e8f",
    "d4e5f6a7-b8c9-0d1e-2f3a-4b5c6d7e8f9a"
  ],
  "amount": 5000.00,
  "currency": "USD",
  "description": "Wire transfer deposit",
  "transactions": [
    {
      "uuid": "c3d4e5f6-a7b8-9c0d-1e2f-3a4b5c6d7e8f",
      "idempotency_key": "DEP-2026-0805-0019283_user",
      "user_id": "a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d",
      "wallet_id": "b2c3d4e5-f6a7-8b9c-0d1e-2f3a4b5c6d7e",
      "amount": 5000.00,
      "currency": "USD",
      "type": "deposit",
      "status": "success",
      "description": "Wire transfer deposit",
      "created_at": "2026-08-05T11:40:00Z"
    }
  ],
  "ledger_entries": [
    {
      "uuid": "e5f6a7b8-c9d0-1e2f-3a4b-5c6d7e8f9a0b",
      "transaction_id": "c3d4e5f6-a7b8-9c0d-1e2f-3a4b5c6d7e8f",
      "wallet_id": "b2c3d4e5-f6a7-8b9c-0d1e-2f3a4b5c6d7e",
      "entry_type": "credit",
      "amount": 5000.00,
      "balance_after": 5000.00,
      "created_at": "2026-08-05T11:40:00Z"
    }
  ]
}
```
- **Errors**:
  - `400 Bad Request`: Invalid amount (`WALLET_INSUFFICIENT_BALANCE` / `INVALID_OPERATION`).
  - `401 Unauthorized`: Not authenticated.
  - `403 Forbidden`: Admin role required.
  - `404 Not Found`: User wallet not found.
  - `409 Conflict`: Duplicate transaction idempotency key collision.

---

### 5. POST `/admin/money-movements/withdraw`
- **Role / Access**: Admin Only (`require_admin`)
- **Summary**: Withdraw funds from user wallet
- **Description**: Withdraws funds from a user's wallet, verifying sufficient balance and updating double-entry ledger entries.
- **Headers**: `Content-Type: application/json`
- **Cookies**: `access_token` (Required)
- **Request Body (`WithdrawRequest`)**:
```json
{
  "user_id": "a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d",
  "amount": 1000.00,
  "idempotency_key": "WTH-2026-0805-0099182",
  "description": "Investor withdrawal payout"
}
```
- **Response (`200 OK - MoneyMovementResponse`)**:
```json
{
  "success": true,
  "duplicate": false,
  "transaction_ids": [
    "f6a7b8c9-d0e1-2f3a-4b5c-6d7e8f9a0b1c"
  ],
  "amount": 1000.00,
  "currency": "USD",
  "description": "Investor withdrawal payout",
  "transactions": [],
  "ledger_entries": []
}
```
- **Errors**:
  - `400 Bad Request`: `WALLET_INSUFFICIENT_BALANCE` (User balance < requested amount).
  - `401 Unauthorized`: Not authenticated.
  - `403 Forbidden`: Admin role required.
  - `404 Not Found`: User wallet not found.
