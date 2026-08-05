# User Management API Documentation

All user administration endpoints are grouped under the `/admin/users` route prefix and require the `require_admin` dependency (user role `admin`).

---

## Data Schemas

### `UserCreate` (Request Body)
| Field | Type | Required | Default | Description / Validation |
| :--- | :--- | :--- | :--- | :--- |
| `name` | `string` | Yes | - | Full name of the user |
| `email` | `string (EmailStr)` | Yes | - | Valid email address |
| `password` | `string` | No | `null` | Optional plain text password |
| `role` | `string` | No | `"investor"` | Role string (`"admin"`, `"admin_dev"`, `"investor"`) |
| `provider` | `string` | Yes | - | Identity provider (e.g., `"local"`, `"google"`) |
| `age` | `integer` | No | `null` | Age of user |

### `UserUpdate` (Request Body)
| Field | Type | Required | Default | Description / Validation |
| :--- | :--- | :--- | :--- | :--- |
| `name` | `string` | No | `null` | Updated user full name |
| `age` | `integer` | No | `null` | Updated age |
| `role` | `string (UserRole)` | No | `null` | Updated user role (`"admin"`, `"admin_dev"`, `"investor"`) |

### `UserResponse` (Response Schema)
| Field | Type | Description |
| :--- | :--- | :--- |
| `uuid` | `string (UUID)` | Unique user UUID |
| `name` | `string` | Full name of user |
| `email` | `string` | Email address |
| `age` | `integer \| null` | User age |
| `role` | `string (UserRole)` | User role (`admin`, `admin_dev`, `investor`) |

---

## Endpoints

### 1. POST `/admin/users`
- **Role / Access**: Admin Only (`require_admin`)
- **Summary**: Create user
- **Description**: Allows administrators to create a new user account in the system.
- **Headers**: `Content-Type: application/json`
- **Cookies**: `access_token` (Required)
- **Request Body (`UserCreate`)**:
```json
{
  "name": "Jane Doe",
  "email": "jane.doe@example.com",
  "password": "secretpassword123",
  "role": "investor",
  "provider": "local",
  "age": 30
}
```
- **Response (`201 Created` / `200 OK - UserResponse`)**:
```json
{
  "uuid": "a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d",
  "name": "Jane Doe",
  "email": "jane.doe@example.com",
  "age": 30,
  "role": "investor"
}
```
- **Errors**:
  - `401 Unauthorized`: Missing or invalid `access_token` cookie.
  - `403 Forbidden`: User is not an admin.
  - `409 Conflict` / `400 Bad Request`: Email already exists.
  - `422 Unprocessable Entity`: Input validation failure.

---

### 2. GET `/admin/users/{user_id}`
- **Role / Access**: Admin Only (`require_admin`)
- **Summary**: Get user details
- **Description**: Retrieves detailed profile information for a specific user by their database integer ID (`user_id`).
- **Headers**: None
- **Cookies**: `access_token` (Required)
- **Path Parameters**:
  - `user_id` (`integer`, Required): Integer ID of the user.
- **Request Body**: None
- **Response (`200 OK - UserResponse`)**:
```json
{
  "uuid": "a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d",
  "name": "Jane Doe",
  "email": "jane.doe@example.com",
  "age": 30,
  "role": "investor"
}
```
- **Errors**:
  - `401 Unauthorized`: Not authenticated.
  - `403 Forbidden`: Admin role required.
  - `404 Not Found`: User with specified ID does not exist.

---

### 3. GET `/admin/users`
- **Role / Access**: Admin Only (`require_admin`)
- **Summary**: List all users
- **Description**: Retrieves a paginated list of user accounts with sorting options.
- **Headers**: None
- **Cookies**: `access_token` (Required)
- **Query Parameters**:
  - `limit` (`integer`, Optional, Default: `10`, Max: `100`): Maximum records to return.
  - `skip` (`integer`, Optional, Default: `0`, Min: `0`): Offset count.
  - `sort_by` (`string`, Optional, Default: `"id"`): Field name to sort by.
  - `order` (`string`, Optional, Default: `"asc"`): Order direction (`"asc"` or `"desc"`).
- **Request Body**: None
- **Response (`200 OK - List[UserResponse]`)**:
```json
[
  {
    "uuid": "a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d",
    "name": "Jane Doe",
    "email": "jane.doe@example.com",
    "age": 30,
    "role": "investor"
  }
]
```
- **Errors**:
  - `401 Unauthorized`: Not authenticated.
  - `403 Forbidden`: Admin role required.

---

### 4. PUT `/admin/users/{user_id}`
- **Role / Access**: Admin Only (`require_admin`)
- **Summary**: Update user details
- **Description**: Updates profile information for an existing user account identified by integer ID.
- **Headers**: `Content-Type: application/json`
- **Cookies**: `access_token` (Required)
- **Path Parameters**:
  - `user_id` (`integer`, Required): Integer ID of the user.
- **Request Body (`UserUpdate`)**:
```json
{
  "name": "Jane Updated",
  "age": 31,
  "role": "investor"
}
```
- **Response (`200 OK - UserResponse`)**:
```json
{
  "uuid": "a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d",
  "name": "Jane Updated",
  "email": "jane.doe@example.com",
  "age": 31,
  "role": "investor"
}
```
- **Errors**:
  - `401 Unauthorized`: Not authenticated.
  - `403 Forbidden`: Admin role required.
  - `404 Not Found`: User not found.

---

### 5. DELETE `/admin/users/{user_id}`
- **Role / Access**: Admin Only (`require_admin`)
- **Summary**: Delete user account
- **Description**: Deletes a user account from the system by integer ID.
- **Headers**: None
- **Cookies**: `access_token` (Required)
- **Path Parameters**:
  - `user_id` (`integer`, Required): Integer ID of the user.
- **Request Body**: None
- **Response (`200 OK`)**: Service output or deletion confirmation.
- **Errors**:
  - `401 Unauthorized`: Not authenticated.
  - `403 Forbidden`: Admin role required.
  - `404 Not Found`: User not found.
