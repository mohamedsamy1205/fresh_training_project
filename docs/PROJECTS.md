# Projects Administration API Documentation

All project management, analytics, approval, closing, and profit distribution endpoints are grouped under the `/admin/projects` route prefix and require the `require_admin` dependency (user role `admin`).

---

## Data Schemas

### `ProjectCreate` (Request Body)
| Field | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `name` | `string` | Yes | Project title / name |
| `start_date` | `string (datetime)` | Yes | ISO-8601 project start date |
| `end_date` | `string (datetime)` | Yes | ISO-8601 project end date |

### `ProjectCloseRequest` (Request Body)
| Field | Type | Required | Constraints | Description |
| :--- | :--- | :--- | :--- | :--- |
| `final_amount` | `decimal` | Yes | `> 0.00` | Final project evaluation amount |

### `DistributeProfitsRequest` (Request Body)
| Field | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `idempotency_key` | `string` | Yes | Unique request deduplication key |

### `ProjectResponse` (Response Schema)
| Field | Type | Description |
| :--- | :--- | :--- |
| `uuid` | `string (UUID)` | Project UUID |
| `name` | `string` | Project name |
| `start_date` | `string (datetime)` | Project start date |
| `end_date` | `string (datetime)` | Project end date |
| `initial_amount` | `decimal` | Total capital funded upon start |
| `final_amount` | `decimal \| null` | Final amount evaluation set when project closed |
| `status` | `string (ProjectStatus)` | Enum: `active`, `closed`, `distributed` |
| `created_at` | `string (datetime)` | ISO-8601 timestamp |
| `updated_at` | `string (datetime)` | ISO-8601 timestamp |

### `ProjectAnalyticsResponse` (Response Schema)
| Field | Type | Description |
| :--- | :--- | :--- |
| `project_id` | `string (UUID)` | Project UUID |
| `project_name` | `string` | Project name |
| `project_status` | `string (ProjectStatus)` | Enum: `active`, `closed`, `distributed` |
| `initial_amount` | `decimal` | Initial project target/capital |
| `total_invested_amount` | `decimal` | Total aggregated investment funds |
| `number_of_investments` | `integer` | Count of total investment records |
| `number_of_unique_investors` | `integer` | Count of unique investor users |
| `average_investment_amount` | `decimal` | Mean investment amount per investment |

---

## Endpoints

### 1. POST `/admin/projects`
- **Role / Access**: Admin Only (`require_admin`)
- **Summary**: Create investment project
- **Description**: Allows administrators to launch a new investment project with start and end dates.
- **Headers**: `Content-Type: application/json`
- **Cookies**: `access_token` (Required)
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
  "initial_amount": 0.00,
  "final_amount": null,
  "status": "active",
  "created_at": "2026-08-05T11:50:00Z",
  "updated_at": "2026-08-05T11:50:00Z"
}
```
- **Errors**:
  - `401 Unauthorized`: Not authenticated.
  - `403 Forbidden`: Admin role required.

---

### 2. GET `/admin/projects/{project_id}/analytics`
- **Role / Access**: Admin Only (`require_admin`)
- **Summary**: Get project investment analytics
- **Description**: Retrieves aggregated investment analytics, totals, unique investor counts, and average metrics for a specified project UUID.
- **Headers**: None
- **Cookies**: `access_token` (Required)
- **Path Parameters**:
  - `project_id` (`string (UUID)`, Required): Target project UUID.
- **Response (`200 OK - ProjectAnalyticsResponse`)**:
```json
{
  "project_id": "d4e5f6a7-b8c9-0d1e-2f3a-4b5c6d7e8f9a",
  "project_name": "Solar Energy Plant Phase 1",
  "project_status": "active",
  "initial_amount": 100000.00,
  "total_invested_amount": 150000.00,
  "number_of_investments": 12,
  "number_of_unique_investors": 8,
  "average_investment_amount": 12500.00
}
```
- **Errors**:
  - `401 Unauthorized`: Authentication required.
  - `403 Forbidden`: Admin role required.
  - `404 Not Found`: Project not found.

---

### 3. POST `/admin/projects/requests/{request_id}/approve`
- **Role / Access**: Admin Only (`require_admin`)
- **Summary**: Approve investment request
- **Description**: Approves a pending investor investment request using an idempotency key, transferring funds from investor wallet into the project.
- **Headers**: None
- **Cookies**: `access_token` (Required)
- **Path Parameters**:
  - `request_id` (`string (UUID)`, Required): Investment request UUID.
- **Query Parameters**:
  - `idempotency_key` (`string`, Required): Unique string key to prevent duplicate approval processing.
- **Response (`200 OK`)**: Service approval output / investment request confirmation.
- **Errors**:
  - `400 Bad Request`: Request is not pending or investor has insufficient wallet balance.
  - `401 Unauthorized`: Not authenticated.
  - `403 Forbidden`: Admin role required.
  - `404 Not Found`: Request or wallet not found.

---

### 4. POST `/admin/projects/requests/{request_id}/reject`
- **Role / Access**: Admin Only (`require_admin`)
- **Summary**: Reject investment request
- **Description**: Rejects a pending investor investment request and updates request status to `rejected`.
- **Headers**: None
- **Cookies**: `access_token` (Required)
- **Path Parameters**:
  - `request_id` (`string (UUID)`, Required): Target investment request UUID.
- **Response (`200 OK - InvestmentRequestResponse`)**:
```json
{
  "uuid": "e5f6a7b8-c9d0-1e2f-3a4b-5c6d7e8f9a0b",
  "user_id": "a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d",
  "project_id": "d4e5f6a7-b8c9-0d1e-2f3a-4b5c6d7e8f9a",
  "wallet_id": "b2c3d4e5-f6a7-8b9c-0d1e-2f3a4b5c6d7e",
  "amount": 5000.00,
  "status": "rejected",
  "created_at": "2026-08-05T10:00:00Z",
  "updated_at": "2026-08-05T11:52:00Z"
}
```
- **Errors**:
  - `400 Bad Request`: Request is not pending.
  - `401 Unauthorized`: Not authenticated.
  - `403 Forbidden`: Admin role required.
  - `404 Not Found`: Investment request not found.

---

### 5. POST `/admin/projects/{project_id}/close`
- **Role / Access**: Admin Only (`require_admin`)
- **Summary**: Close active project
- **Description**: Closes an active investment project and sets the final valuation amount (`final_amount`). Enforces a strict business rule: project must have a **minimum of 2 active investors**.
- **Headers**: `Content-Type: application/json`
- **Cookies**: `access_token` (Required)
- **Path Parameters**:
  - `project_id` (`string (UUID)`, Required): Target project UUID.
- **Request Body (`ProjectCloseRequest`)**:
```json
{
  "final_amount": 125000.00
}
```
- **Response (`200 OK - ProjectResponse`)**:
```json
{
  "uuid": "d4e5f6a7-b8c9-0d1e-2f3a-4b5c6d7e8f9a",
  "name": "Solar Energy Plant Phase 1",
  "start_date": "2026-09-01T00:00:00Z",
  "end_date": "2027-09-01T00:00:00Z",
  "initial_amount": 100000.00,
  "final_amount": 125000.00,
  "status": "closed",
  "created_at": "2026-08-05T11:50:00Z",
  "updated_at": "2026-08-05T11:53:00Z"
}
```
- **Errors**:
  - `400 Bad Request`: `INVALID_OPERATION` (Project is not active or has fewer than 2 investors).
  - `401 Unauthorized`: Not authenticated.
  - `403 Forbidden`: Admin role required.
  - `404 Not Found`: Project not found.

---

### 6. POST `/admin/projects/{project_id}/distribute-profits`
- **Role / Access**: Admin Only (`require_admin`)
- **Summary**: Distribute project profits/losses
- **Description**: Calculates financial profits or losses (`final_amount - initial_amount`) and distributes returns to project investors proportionally according to their investment percentage using double-entry treasury ledgers and idempotency keys.
- **Headers**: `Content-Type: application/json`
- **Cookies**: `access_token` (Required)
- **Path Parameters**:
  - `project_id` (`string (UUID)`, Required): Target closed project UUID.
- **Request Body (`DistributeProfitsRequest`)**:
```json
{
  "idempotency_key": "DIST-SOLAR-2026-001"
}
```
- **Response (`200 OK`)**: Profit distribution execution output / transaction summary.
- **Errors**:
  - `400 Bad Request`: `INVALID_OPERATION` (Project is not closed or already distributed).
  - `401 Unauthorized`: Not authenticated.
  - `403 Forbidden`: Admin role required.
  - `404 Not Found`: Project not found.
