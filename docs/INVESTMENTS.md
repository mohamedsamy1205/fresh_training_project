# Investor Investments API Documentation

This document describes the investor-facing investment workflows, endpoints, and schemas for discovering projects and submitting funding requests under `/investor/projects` and `/projects`.

---

## Data Schemas

### `CreateInvestmentRequest` (Request Body)
| Field | Type | Required | Constraints | Description |
| :--- | :--- | :--- | :--- | :--- |
| `wallet_id` | `string (UUID)` | Yes | - | Investor's wallet UUID to deduct funds from upon approval |
| `amount` | `string (MoneyAmount)` | Yes | `> 0.00` | Requested investment amount formatted to 2 decimals (e.g. `"10000.00"`) |

### `InvestmentRequestResponse` (Response Schema)
| Field | Type | Description |
| :--- | :--- | :--- |
| `uuid` | `string (UUID)` | Unique investment request UUID |
| `user_id` | `string (UUID)` | Submitting investor user UUID |
| `project_id` | `string (UUID)` | Target project UUID |
| `wallet_id` | `string (UUID)` | Investor wallet UUID |
| `amount` | `string (MoneyAmount)` | Requested investment monetary amount |
| `status` | `string (InvestmentRequestStatus)` | Status enum: `pending`, `approved`, `rejected` |
| `created_at` | `string (datetime)` | ISO-8601 creation timestamp |
| `updated_at` | `string (datetime)` | ISO-8601 update timestamp |

### `InvestmentResponse` (Confirmed Investment DTO)
| Field | Type | Description |
| :--- | :--- | :--- |
| `uuid` | `string (UUID)` | Confirmed investment record UUID |
| `user_id` | `string (UUID)` | Investor user UUID |
| `project_id` | `string (UUID)` | Target project UUID |
| `wallet_id` | `string (UUID)` | Investor wallet UUID |
| `amount` | `string (MoneyAmount)` | Confirmed capital funded |
| `created_at` | `string (datetime)` | ISO-8601 creation timestamp |

---

## Endpoints

### 1. GET `/projects`
- **Role / Access**: Authenticated Users (`get_current_user`)
- **Summary**: Discover available projects & view application status
- **Description**: Retrieves all investment projects with Redis caching. For investors, each project entry includes a dynamic `user_request_status` field indicating if the user has a `pending`, `approved`, or `rejected` application for that project.
- **Response (`200 OK - List[ProjectResponse]`)**:
```json
[
  {
    "uuid": "d4e5f6a7-b8c9-0d1e-2f3a-4b5c6d7e8f9a",
    "name": "Solar Energy Plant Phase 1",
    "start_date": "2026-09-01T00:00:00Z",
    "end_date": "2027-09-01T00:00:00Z",
    "initial_amount": "50000.00",
    "final_amount": null,
    "status": "active",
    "user_request_status": "pending",
    "created_at": "2026-08-19T08:00:00Z",
    "updated_at": "2026-08-19T08:00:00Z"
  }
]
```

---

### 2. POST `/investor/projects/{project_id}/investment-requests`
- **Role / Access**: Investor Only (`require_investor`)
- **Status Code**: `201 Created`
- **Summary**: Submit investment request
- **Description**: Submits an investment funding request for a specific active project. The request is created in `pending` status awaiting administrator approval.
- **Headers**: `Content-Type: application/json`
- **Cookies / Bearer**: `access_token` (Required)
- **Path Parameters**:
  - `project_id` (`string (UUID)`, Required): UUID of the target project.
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
  - `400 Bad Request`: `INVALID_OPERATION` (Project is not active, project end date has passed, wallet does not belong to investor, or duplicate request already submitted).
  - `401 Unauthorized`: Not authenticated.
  - `403 Forbidden`: Investor role required.
  - `404 Not Found`: Project or wallet not found.

---

## Investment Lifecycle Walkthrough

```text
1. Discovery (GET /projects)
   Investor browses active projects. (user_request_status = null)
   ↓
2. Request Submission (POST /investor/projects/{project_id}/investment-requests)
   Investor selects wallet and enters funding amount. (status = pending)
   ↓
3. Admin Review & Processing (POST /admin/projects/requests/{request_id}/approve or reject)
   - If Approved:
     * Investor wallet is debited
     * Company treasury is credited
     * Double-entry ledger records created
     * Investment record created (status = approved)
   - If Rejected:
     * Request marked as rejected (status = rejected)
     * No funds debited
   ↓
4. Project Closure & Valuation (POST /admin/projects/{project_id}/close)
   Admin closes project upon maturity (enforcing >= 2 distinct investors) and deposits valuation.
   ↓
5. Profit Distribution (POST /admin/projects/{project_id}/distribute-profits)
   Profits/losses distributed pro-rata.
   * If profitable: 20% company fee collected; 80% net gain + principal returned to investor wallet.
```
