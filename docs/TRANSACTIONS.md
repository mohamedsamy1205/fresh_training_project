# Transactions API Documentation

All transaction history and creation endpoints are grouped under the `/investor/transactions` route prefix and require the `require_investor` dependency (user role `investor`).

---

## Data Schemas

### `TransactionCreate` (Request Body)
| Field | Type | Required | Default | Description / Constraints |
| :--- | :--- | :--- | :--- | :--- |
| `wallet_id` | `string (UUID)` | Yes | - | UUID of target wallet |
| `amount` | `decimal` | Yes | - | Transaction amount |
| `type` | `string (TransactionType)` | Yes | - | Enum: `deposit`, `withdraw`, `transfer`, `investment`, `profit_payout`, `company_fee` |
| `status` | `string (TransactionStatus)` | No | `"pending"` | Enum: `pending`, `success`, `failed` |
| `user_id` | `string (UUID)` | No | `null` | Optional user UUID |
| `description` | `string` | No | `null` | Optional transaction description |

### `TransactionResponse` (Response Schema)
| Field | Type | Description |
| :--- | :--- | :--- |
| `uuid` | `string (UUID)` | Transaction header UUID |
| `user_id` | `string (UUID)` | User UUID |
| `wallet_id` | `string (UUID)` | Wallet UUID |
| `amount` | `float` | Transaction amount |
| `type` | `string (TransactionType)` | Enum: `deposit`, `withdraw`, `transfer`, `investment`, `profit_payout`, `company_fee` |
| `status` | `string (TransactionStatus)` | Enum: `pending`, `success`, `failed` |
| `description` | `string \| null` | Optional description |
| `created_at` | `string (datetime)` | ISO-8601 timestamp |

---

## Endpoints

### 1. POST `/investor/transactions`
- **Role / Access**: Investor Only (`require_investor`)
- **Summary**: Create transaction
- **Description**: Creates a new financial transaction header record between investor wallets.
- **Headers**: `Content-Type: application/json`
- **Cookies**: `access_token` (Required)
- **Request Body (`TransactionCreate`)**:
```json
{
  "wallet_id": "b2c3d4e5-f6a7-8b9c-0d1e-2f3a4b5c6d7e",
  "amount": 250.00,
  "type": "transfer",
  "status": "pending",
  "user_id": "a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d",
  "description": "Peer-to-peer wallet transfer"
}
```
- **Response (`200 OK - TransactionResponse`)**:
```json
{
  "uuid": "c3d4e5f6-a7b8-9c0d-1e2f-3a4b5c6d7e8f",
  "user_id": "a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d",
  "wallet_id": "b2c3d4e5-f6a7-8b9c-0d1e-2f3a4b5c6d7e",
  "amount": 250.00,
  "type": "transfer",
  "status": "pending",
  "description": "Peer-to-peer wallet transfer",
  "created_at": "2026-08-05T11:45:00Z"
}
```
- **Errors**:
  - `401 Unauthorized`: Authentication required.
  - `403 Forbidden`: Investor role required.
  - `422 Unprocessable Entity`: Field validation failure.

---

### 2. GET `/investor/transactions/sender/{user_id}`
- **Role / Access**: Investor Only (`require_investor`)
- **Summary**: Get transactions by sender ID
- **Description**: Retrieves all financial transactions initiated by a specific sender user UUID.
- **Headers**: None
- **Cookies**: `access_token` (Required)
- **Path Parameters**:
  - `user_id` (`string (UUID)`, Required): UUID of the sender user.
- **Response (`200 OK - List[TransactionResponse]`)**:
```json
[
  {
    "uuid": "c3d4e5f6-a7b8-9c0d-1e2f-3a4b5c6d7e8f",
    "user_id": "a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d",
    "wallet_id": "b2c3d4e5-f6a7-8b9c-0d1e-2f3a4b5c6d7e",
    "amount": 250.00,
    "type": "transfer",
    "status": "pending",
    "description": "Peer-to-peer wallet transfer",
    "created_at": "2026-08-05T11:45:00Z"
  }
]
```
- **Errors**:
  - `401 Unauthorized`: Not authenticated.
  - `403 Forbidden`: Investor role required.

---

### 3. GET `/investor/transactions/wallet/{wallet_id}`
- **Role / Access**: Investor Only (`require_investor`)
- **Summary**: Get transactions by wallet ID
- **Description**: Retrieves all financial transaction logs recorded for a specific wallet UUID.
- **Headers**: None
- **Cookies**: `access_token` (Required)
- **Path Parameters**:
  - `wallet_id` (`string (UUID)`, Required): Target wallet UUID.
- **Response (`200 OK - List[TransactionResponse]`)**:
```json
[
  {
    "uuid": "c3d4e5f6-a7b8-9c0d-1e2f-3a4b5c6d7e8f",
    "user_id": "a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d",
    "wallet_id": "b2c3d4e5-f6a7-8b9c-0d1e-2f3a4b5c6d7e",
    "amount": 250.00,
    "type": "transfer",
    "status": "pending",
    "description": "Peer-to-peer wallet transfer",
    "created_at": "2026-08-05T11:45:00Z"
  }
]
```
- **Errors**:
  - `401 Unauthorized`: Not authenticated.
  - `403 Forbidden`: Investor role required.
