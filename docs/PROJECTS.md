# Projects & Investment Management API Documentation

This document covers all project management, analytics, investment requests, project closures, and profit distributions across `/admin/projects`, `/investor/projects`, and `/projects`.

---

## Data Schemas

### `ProjectCreate` (Request Body)
| Field | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `name` | `string` | Yes | Project title |
| `start_date` | `string (datetime)` | Yes | ISO-8601 project start date |
| `end_date` | `string (datetime)` | Yes | ISO-8601 project end date (must be after start_date) |

### `ProjectCloseRequest` (Request Body)
| Field | Type | Required | Constraints | Description |
| :--- | :--- | :--- | :--- | :--- |
| `final_amount` | `string (MoneyAmount)` | Yes | `> 0.00` | Final project evaluation amount |

### `DistributeProfitsRequest` (Request Body)
| Field | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `idempotency_key` | `string` | Yes | Unique deduplication key |

### `CreateInvestmentRequest` (Request Body)
| Field | Type | Required | Constraints | Description |
| :--- | :--- | :--- | :--- | :--- |
| `wallet_id` | `string (UUID)` | Yes | - | Investor's wallet UUID |
| `amount` | `string (MoneyAmount)` | Yes | `> 0.00` | Requested investment funding amount |

### `ProjectResponse` (Response Schema)
| Field | Type | Description |
| :--- | :--- | :--- |
| `uuid` | `string (UUID)` | Unique project UUID |
| `name` | `string` | Project name |
| `start_date` | `string (datetime)` | ISO-8601 project start date |
| `end_date` | `string (datetime)` | ISO-8601 project end date |
| `initial_amount` | `string (MoneyAmount)` | Aggregated approved capital invested |
| `final_amount` | `string (MoneyAmount) \| null` | Final evaluation set upon project closure |
| `status` | `string (ProjectStatus)` | Enum: `active`, `closed`, `distributed` |
| `user_request_status` | `string (InvestmentRequestStatus) \| null` | Authenticated investor's latest request status (`pending`, `approved`, `rejected`, or `null`) |
| `created_at` | `string (datetime)` | ISO-8601 creation timestamp |
| `updated_at` | `string (datetime)` | ISO-8601 update timestamp |

### `ProjectAnalyticsResponse` (Response Schema)
| Field | Type | Description |
| :--- | :--- | :--- |
| `project_id` | `string (UUID)` | Project UUID |
| `project_name` | `string` | Project name |
| `project_status` | `string (ProjectStatus)` | Enum: `active`, `closed`, `distributed` |
| `initial_amount` | `string (MoneyAmount)` | Current total initial capital funded |
| `total_invested_amount` | `string (MoneyAmount)` | Aggregated investment sum from `investments` table |
| `number_of_investments` | `integer` | Count of confirmed investment records |
| `number_of_unique_investors` | `integer` | Count of distinct investor users |
| `average_investment_amount` | `string (MoneyAmount)` | Mean investment amount per investment |

### `InvestmentRequestResponse` (Response Schema)
| Field | Type | Description |
| :--- | :--- | :--- |
| `uuid` | `string (UUID)` | Unique investment request UUID |
| `user_id` | `string (UUID)` | Submitting investor user UUID |
| `project_id` | `string (UUID)` | Target project UUID |
| `wallet_id` | `string (UUID)` | Selected investor wallet UUID |
| `amount` | `string (MoneyAmount)` | Requested investment amount |
| `status` | `string (InvestmentRequestStatus)` | Enum: `pending`, `approved`, `rejected` |
| `created_at` | `string (datetime)` | ISO-8601 creation timestamp |
| `updated_at` | `string (datetime)` | ISO-8601 update timestamp |

---

## Global & Discovery Endpoints

### 1. GET `/projects`
- **Role / Access**: Authenticated Users (`get_current_user`)
- **Summary**: List all projects
- **Description**: Returns all projects with 300s Redis caching. For investors, each project is enriched with their current `user_request_status` (`pending`, `approved`, `rejected`, or `null`).
- **Response (`200 OK - List[ProjectResponse]`)**:
```json
[
  {
    "uuid": "d4e5f6a7-b8c9-0d1e-2f3a-4b5c6d7e8f9a",
    "name": "Solar Energy Plant Phase 1",
    "start_date": "2026-09-01T00:00:00Z",
    "end_date": "2027-09-01T00:00:00Z",
    "initial_amount": "100000.00",
    "final_amount": null,
    "status": "active",
    "user_request_status": "approved",
    "created_at": "2026-08-19T08:00:00Z",
    "updated_at": "2026-08-19T08:00:00Z"
  }
]
```

### 2. POST `/projects`
- **Role / Access**: Admin Only (`require_admin`)
- **Status Code**: `201 Created`
- **Summary**: Create project generic
- **Request Body (`dict`)**:
```json
{
  "name": "Wind Turbine Farm",
  "start_date": "2026-10-01T00:00:00Z",
  "end_date": "2027-10-01T00:00:00Z"
}
```
- **Response (`201 Created - ProjectResponse`)**: Created project object.

---

## Admin Endpoints (`/admin/projects`)

### 3. POST `/admin/projects`
- **Role / Access**: Admin Only (`require_admin`)
- **Status Code**: `201 Created`
- **Summary**: Create investment project
- **Request Body (`ProjectCreate`)**:
```json
{
  "name": "Solar Energy Plant Phase 1",
  "start_date": "2026-09-01T00:00:00Z",
  "end_date": "2027-09-01T00:00:00Z"
}
```
- **Response (`201 Created - ProjectResponse`)**:
```json
{
  "uuid": "d4e5f6a7-b8c9-0d1e-2f3a-4b5c6d7e8f9a",
  "name": "Solar Energy Plant Phase 1",
  "start_date": "2026-09-01T00:00:00Z",
  "end_date": "2027-09-01T00:00:00Z",
  "initial_amount": "0.00",
  "final_amount": null,
  "status": "active",
  "user_request_status": null,
  "created_at": "2026-08-19T08:00:00Z",
  "updated_at": "2026-08-19T08:00:00Z"
}
```

---

### 4. GET `/admin/projects/{project_id}/analytics`
- **Role / Access**: Admin Only (`require_admin`)
- **Summary**: Get project investment analytics
- **Path Parameters**:
  - `project_id` (`string (UUID)`, Required): Target project UUID.
- **Response (`200 OK - ProjectAnalyticsResponse`)**:
```json
{
  "project_id": "d4e5f6a7-b8c9-0d1e-2f3a-4b5c6d7e8f9a",
  "project_name": "Solar Energy Plant Phase 1",
  "project_status": "active",
  "initial_amount": "100000.00",
  "total_invested_amount": "100000.00",
  "number_of_investments": 4,
  "number_of_unique_investors": 3,
  "average_investment_amount": "25000.00"
}
```

---

### 5. GET `/admin/projects/{project_id}/investment-requests`
- **Role / Access**: Admin Only (`require_admin`)
- **Summary**: List investment requests for a project
- **Path Parameters**:
  - `project_id` (`string (UUID)`, Required): Target project UUID.
- **Response (`200 OK - List[InvestmentRequestResponse]`)**: Array of investment requests.

---

### 6. DELETE `/admin/projects/{project_id}`
- **Role / Access**: Admin Only (`require_admin`)
- **Summary**: Delete investment project
- **Description**: Transactionally deletes the project and all associated investment requests and investment records.
- **Path Parameters**:
  - `project_id` (`string (UUID)`, Required): Target project UUID.
- **Response (`200 OK`)**:
```json
{
  "success": true,
  "message": "Project 'd4e5f6a7-b8c9-0d1e-2f3a-4b5c6d7e8f9a' and all associated relations deleted successfully."
}
```

---

### 7. POST `/admin/projects/requests/{request_id}/approve`
- **Role / Access**: Admin Only (`require_admin`)
- **Summary**: Approve investment request
- **Description**: Atomically debits the investor's wallet, credits treasury, records double-entry ledgers, creates an `Investment` record, and increments project `initial_amount`.
- **Path Parameters**:
  - `request_id` (`string (UUID)`, Required): Investment request UUID.
- **Query Parameters**:
  - `idempotency_key` (`string`, Required): Unique deduplication key.
- **Response (`200 OK`)**:
```json
{
  "success": true,
  "is_duplicate": false,
  "request_id": "e5f6a7b8-c9d0-1e2f-3a4b-5c6d7e8f9a0b",
  "status": "approved",
  "investment_id": "a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d",
  "transaction_id": "c3d4e5f6-a7b8-9c0d-1e2f-3a4b5c6d7e8f",
  "amount": "10000.00",
  "project_initial_amount": "100000.00"
}
```

---

### 8. POST `/admin/projects/requests/{request_id}/reject`
- **Role / Access**: Admin Only (`require_admin`)
- **Summary**: Reject investment request
- **Path Parameters**:
  - `request_id` (`string (UUID)`, Required): Target request UUID.
- **Response (`200 OK - InvestmentRequestResponse`)**: Updated request with `status: "rejected"`.

---

### 9. POST `/admin/projects/{project_id}/close`
- **Role / Access**: Admin Only (`require_admin`)
- **Summary**: Close active project
- **Description**: Closes active project and sets `final_amount`. **Enforces minimum 2 distinct investors requirement**. Deposits final valuation into the treasury wallet.
- **Path Parameters**:
  - `project_id` (`string (UUID)`, Required): Project UUID.
- **Request Body (`ProjectCloseRequest`)**:
```json
{
  "final_amount": "125000.00"
}
```
- **Response (`200 OK - ProjectResponse`)**: Project with `status: "closed"` and `final_amount: "125000.00"`.
- **Errors**:
  - `400 Bad Request`: `INVALID_OPERATION` (Fewer than 2 distinct investors or project not active).

---

### 10. POST `/admin/projects/{project_id}/distribute-profits`
- **Role / Access**: Admin Only (`require_admin`)
- **Summary**: Distribute project profits/losses
- **Description**: Computes pro-rata profit/loss share for each investor. If net profit is positive, deducts a **20% platform commission** (`company_fee`), returns 80% net gain + initial principal to investor wallets (`profit_payout`), and updates project status to `distributed`.
- **Path Parameters**:
  - `project_id` (`string (UUID)`, Required): Project UUID.
- **Request Body (`DistributeProfitsRequest`)**:
```json
{
  "idempotency_key": "DIST-SOLAR-2026-001"
}
```
- **Response (`200 OK`)**:
```json
{
  "success": true,
  "is_duplicate": false,
  "project_id": "d4e5f6a7-b8c9-0d1e-2f3a-4b5c6d7e8f9a",
  "total_initial_amount": "100000.00",
  "total_final_amount": "125000.00",
  "total_profit": "25000.00",
  "total_company_fee_collected": "5000.00",
  "total_returned_to_investors": "120000.00",
  "distributions": [
    {
      "investment_id": "a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d",
      "user_id": "user-uuid-1",
      "wallet_id": "wallet-uuid-1",
      "investment_amount": "50000.00",
      "gross_profit": "12500.00",
      "company_fee": "2500.00",
      "net_profit": "10000.00",
      "total_payout": "60000.00"
    }
  ]
}
```

---

## Investor Endpoints (`/investor/projects`)

### 11. POST `/investor/projects/{project_id}/investment-requests`
- **Role / Access**: Investor Only (`require_investor`)
- **Status Code**: `201 Created`
- **Summary**: Submit investment request
- **Description**: Allows an investor to submit an investment request for an active project. Validates wallet ownership, active status, and investment window.
- **Path Parameters**:
  - `project_id` (`string (UUID)`, Required): Target project UUID.
- **Request Body (`CreateInvestmentRequest`)**:
```json
{
  "wallet_id": "b2c3d4e5-f6a7-8b9c-0d1e-2f3a4b5c6d7e",
  "amount": "10000.00"
}
```
- **Response (`201 Created - InvestmentRequestResponse`)**:
```json
{
  "uuid": "e5f6a7b8-c9d0-1e2f-3a4b-5c6d7e8f9a0b",
  "user_id": "a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d",
  "project_id": "d4e5f6a7-b8c9-0d1e-2f3a-4b5c6d7e8f9a",
  "wallet_id": "b2c3d4e5-f6a7-8b9c-0d1e-2f3a4b5c6d7e",
  "amount": "10000.00",
  "status": "pending",
  "created_at": "2026-08-19T08:20:00Z",
  "updated_at": "2026-08-19T08:20:00Z"
}
```
- **Errors**:
  - `400 Bad Request`: Project not active, end date passed, or user already submitted a request.
  - `401 Unauthorized`: Not authenticated.
  - `403 Forbidden`: Investor role required.
  - `404 Not Found`: Project or wallet not found.
