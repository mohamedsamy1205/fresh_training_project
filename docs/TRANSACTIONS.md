# Transactions API Documentation

This document describes the financial transaction history and audit query endpoints grouped under `/investor/transactions`.

---

## Data Schemas

### `TransactionResponse` (Response DTO)
| Field | Type | Description |
| :--- | :--- | :--- |
| `uuid` | `string (UUID)` | Unique transaction header UUID |
| `user_id` | `string (UUID) \| null` | Initiator or affected user UUID |
| `wallet_id` | `string (UUID)` | Associated investor or treasury wallet UUID |
| `amount` | `string (MoneyAmount)` | Monetary value formatted with 2 decimal places (e.g. `"250.00"`) |
| `currency` | `string` | Currency string (default: `"USD"`) |
| `type` | `string (TransactionType)` | Transaction classification enum |
| `status` | `string (TransactionStatus)` | Transaction state enum |
| `description` | `string \| null` | Optional note or audit description |
| `created_at` | `string (datetime)` | ISO-8601 creation timestamp |

### `TransactionType` Enum
- `deposit`: Treasury-to-user deposit
- `withdraw`: User-to-treasury withdrawal
- `transfer`: Peer-to-peer or inter-wallet transfer
- `investment`: Approved project investment transfer
- `profit_payout`: Project maturity payout to investor
- `company_fee`: 20% platform profit-sharing commission

### `TransactionStatus` Enum
- `pending`: Awaiting background settlement or approval
- `success`: Fully committed and balanced in ledger
- `failed`: Aborted or rolled back

### `PagePaginationMeta`
| Field | Type | Description |
| :--- | :--- | :--- |
| `page` | `integer` | Current 1-based page number |
| `limit` | `integer` | Requested items per page |
| `total` | `integer` | Total matching record count |
| `total_pages` | `integer` | Total number of available pages |
| `has_next` | `boolean` | `true` if next page exists |
| `has_prev` | `boolean` | `true` if previous page exists |

### `PaginatedTransactionResponse`
| Field | Type | Description |
| :--- | :--- | :--- |
| `data` | `List[TransactionResponse]` | Array of transaction records |
| `pagination` | `PagePaginationMeta` | Standard pagination metadata |

---

## Endpoints

### 1. GET `/investor/transactions/user/{user_id}`
- **Role / Access**: Authenticated Users (`get_current_user`)
- **Rate Limit**: 5 requests / 60 seconds
- **Summary**: Get paginated transactions by sender ID
- **Description**: Retrieves a paginated history of financial transactions initiated by or associated with a specific sender user UUID.
- **Headers**: None
- **Cookies / Bearer**: `access_token` (Required)
- **Path Parameters**:
  - `user_id` (`string (UUID)`, Required): UUID of the sender/user.
- **Query Parameters**:
  - `page` (`integer`, Optional, Default: `1`, Min: `1`): Target page number.
  - `limit` (`integer`, Optional, Default: `20`, Min: `1`, Max: `100`): Maximum items per page.
- **Response (`200 OK - PaginatedTransactionResponse`)**:
```json
{
  "data": [
    {
      "uuid": "c3d4e5f6-a7b8-9c0d-1e2f-3a4b5c6d7e8f",
      "user_id": "a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d",
      "wallet_id": "b2c3d4e5-f6a7-8b9c-0d1e-2f3a4b5c6d7e",
      "amount": "250.00",
      "currency": "USD",
      "type": "deposit",
      "status": "success",
      "description": "Initial funding",
      "created_at": "2026-08-19T08:15:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 1,
    "total_pages": 1,
    "has_next": false,
    "has_prev": false
  }
}
```
- **Errors**:
  - `401 Unauthorized`: Not authenticated.
  - `422 Unprocessable Entity`: Invalid UUID or query parameter validation failure.
  - `429 Too Many Requests`: Rate limit exceeded.

---

## Database Index Optimization

The transactions table is optimized with a composite B-Tree index:

```sql
CREATE INDEX idx_transactions_user_created_id 
ON transactions (user_id, created_at, id);
```

This ensures that queries filtered by `user_id` and ordered by `created_at DESC, id DESC` execute with direct index seeks, eliminating costly table scans and temporary sorting steps.
