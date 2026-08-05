# Investor Investments API Documentation

This document describes the investor-facing endpoints for submitting project investment requests under `/investor/projects`.

---

## Data Schemas

### `CreateInvestmentRequest` (Request Body)
| Field | Type | Required | Constraints | Description |
| :--- | :--- | :--- | :--- | :--- |
| `wallet_id` | `string (UUID)` | Yes | - | Investor's wallet UUID to deduct investment from |
| `amount` | `decimal` | Yes | `> 0.00` | Requested investment funding amount |

### `InvestmentRequestResponse` (Response Schema)
| Field | Type | Description |
| :--- | :--- | :--- |
| `uuid` | `string (UUID)` | Investment request UUID |
| `user_id` | `string (UUID)` | Submitting investor user UUID |
| `project_id` | `string (UUID)` | Target project UUID |
| `wallet_id` | `string (UUID)` | Investor wallet UUID |
| `amount` | `decimal` | Investment amount |
| `status` | `string (InvestmentRequestStatus)` | Status enum: `pending`, `approved`, `rejected` |
| `created_at` | `string (datetime)` | ISO-8601 creation timestamp |
| `updated_at` | `string (datetime)` | ISO-8601 update timestamp |

### `InvestmentResponse` (Response Schema)
| Field | Type | Description |
| :--- | :--- | :--- |
| `uuid` | `string (UUID)` | Confirmed investment UUID |
| `user_id` | `string (UUID)` | Investor user UUID |
| `project_id` | `string (UUID)` | Project UUID |
| `wallet_id` | `string (UUID)` | Wallet UUID |
| `amount` | `decimal` | Investment amount |
| `created_at` | `string (datetime)` | ISO-8601 creation timestamp |

---

## Endpoints

### 1. POST `/investor/projects/{project_id}/investment-requests`
- **Role / Access**: Investor Only (`require_investor`)
- **Summary**: Submit investment request
- **Description**: Allows registered investors to submit an investment request for a specific active project. The request is created in `pending` status awaiting administrator approval.
- **Headers**: `Content-Type: application/json`
- **Cookies**: `access_token` (Required)
- **Path Parameters**:
  - `project_id` (`string (UUID)`, Required): UUID of the target project.
- **Request Body (`CreateInvestmentRequest`)**:
```json
{
  "wallet_id": "b2c3d4e5-f6a7-8b9c-0d1e-2f3a4b5c6d7e",
  "amount": 10000.00
}
```
- **Response (`201 Created - InvestmentRequestResponse`)**:
```json
{
  "uuid": "e5f6a7b8-c9d0-1e2f-3a4b-5c6d7e8f9a0b",
  "user_id": "a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d",
  "project_id": "d4e5f6a7-b8c9-0d1e-2f3a-4b5c6d7e8f9a",
  "wallet_id": "b2c3d4e5-f6a7-8b9c-0d1e-2f3a4b5c6d7e",
  "amount": 10000.00,
  "status": "pending",
  "created_at": "2026-08-05T11:55:00Z",
  "updated_at": "2026-08-05T11:55:00Z"
}
```
- **Errors**:
  - `400 Bad Request`: `INVALID_OPERATION` (Project is not active or wallet does not belong to investor).
  - `401 Unauthorized`: Not authenticated.
  - `403 Forbidden`: Investor role required.
  - `404 Not Found`: Project or wallet not found.
