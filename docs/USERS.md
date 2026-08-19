# User Management API Documentation

All user administration endpoints are grouped under the `/admin/users` route prefix and require the `require_admin` dependency (user role `admin`).

---

## Data Schemas

### `UserCreate` (Request Body)
| Field | Type | Required | Default | Description / Validation |
| :--- | :--- | :--- | :--- | :--- |
| `name` | `string` | Yes | - | Full name of the user |
| `email` | `string (EmailStr)` | Yes | - | Unique valid email address |
| `password` | `string` | No | `null` | Optional plain text password (hashed via bcrypt if provided) |
| `role` | `string` | No | `"investor"` | Requested user role (`"investor"`, `"admin"`, `"admin_dev"`) |
| `provider` | `string` | Yes | - | Identity provider label (e.g. `"local"`, `"google"`) |
| `age` | `integer` | No | `null` | Optional user age |

### `UserUpdate` (Request Body)
| Field | Type | Required | Default | Description / Validation |
| :--- | :--- | :--- | :--- | :--- |
| `name` | `string` | No | `null` | Updated user full name |
| `age` | `integer` | No | `null` | Updated age |
| `role` | `string (UserRole)` | No | `null` | Updated user role (`"admin"`, `"admin_dev"`, `"investor"`) |

### `UserResponse` (Response Schema)
| Field | Type | Description |
| :--- | :--- | :--- |
| `uuid` | `string (UUID)` | Unique User UUID identifier |
| `name` | `string` | User full name |
| `email` | `string (EmailStr)` | Email address |
| `age` | `integer \| null` | User age |
| `role` | `string (UserRole)` | Current assigned role enum: `admin`, `admin_dev`, `investor` |

---

## Endpoints Catalog

### 1. POST `/admin/users`
- **Role / Access**: Admin Only (`require_admin`)
- **Summary**: Create user account
- **Description**: Creates a new user profile with local credentials or provider registration.
- **Headers**: `Content-Type: application/json`
- **Cookies / Bearer**: `access_token` (Required)
- **Request Body (`UserCreate`)**:
```json
{
  "name": "Jane Doe",
  "email": "jane.doe@example.com",
  "password": "SecurePassword123!",
  "role": "investor",
  "provider": "local",
  "age": 29
}
```
- **Response (`200 OK - UserResponse`)**:
```json
{
  "uuid": "a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d",
  "name": "Jane Doe",
  "email": "jane.doe@example.com",
  "age": 29,
  "role": "investor"
}
```
- **Errors**:
  - `401 Unauthorized`: Missing or invalid authentication token.
  - `403 Forbidden`: Admin privileges required.
  - `409 Conflict`: Email address already registered (`DUPLICATE_OPERATION`).
  - `422 Unprocessable Entity`: Input validation failure.

---

### 2. GET `/admin/users/get/{user_id}`
- **Role / Access**: Admin Only (`require_admin`)
- **Summary**: Get user details
- **Description**: Retrieves full profile information for a specific user by their unique UUID.
- **Path Parameters**:
  - `user_id` (`string (UUID)`, Required): UUID of the user.
- **Response (`200 OK - UserResponse`)**:
```json
{
  "uuid": "a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d",
  "name": "Jane Doe",
  "email": "jane.doe@example.com",
  "age": 29,
  "role": "investor"
}
```
- **Errors**:
  - `401 Unauthorized`: Not authenticated.
  - `403 Forbidden`: Admin role required.
  - `404 Not Found`: User with specified UUID does not exist.

---

### 3. GET `/admin/users`
- **Role / Access**: Admin Only (`require_admin`)
- **Summary**: List all users
- **Description**: Retrieves a paginated list of user profiles with sorting and offset controls.
- **Query Parameters**:
  - `limit` (`integer`, Optional, Default: `10`, Max: `100`): Maximum records per query.
  - `skip` (`integer`, Optional, Default: `0`, Min: `0`): Offset record count.
  - `sort_by` (`string`, Optional, Default: `"id"`): Column name to sort by.
  - `order` (`string`, Optional, Default: `"asc"`): Sort direction (`"asc"` or `"desc"`).
- **Response (`200 OK - List[UserResponse]`)**:
```json
[
  {
    "uuid": "a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d",
    "name": "Jane Doe",
    "email": "jane.doe@example.com",
    "age": 29,
    "role": "investor"
  }
]
```
- **Errors**:
  - `401 Unauthorized`: Not authenticated.
  - `403 Forbidden`: Admin role required.

---

### 4. GET `/admin/users/users`
- **Role / Access**: Admin Only (`require_admin`)
- **Summary**: Get all users alias
- **Description**: Convenient administrative alias returning up to 100 users ordered by ID ascending.
- **Response (`200 OK - List[UserResponse]`)**: Array of `UserResponse` objects.

---

### 5. PUT `/admin/users/{user_id}`
- **Role / Access**: Admin Only (`require_admin`)
- **Summary**: Update user details
- **Description**: Updates profile details (name, age, role) for an existing user identified by UUID.
- **Path Parameters**:
  - `user_id` (`string (UUID)`, Required): UUID of the user to update.
- **Request Body (`UserUpdate`)**:
```json
{
  "name": "Jane Doe Updated",
  "age": 30,
  "role": "admin"
}
```
- **Response (`200 OK - UserResponse`)**: Updated user profile.
- **Errors**:
  - `401 Unauthorized`: Not authenticated.
  - `403 Forbidden`: Admin role required.
  - `404 Not Found`: User not found.

---

### 6. DELETE `/admin/users/{user_id}`
- **Role / Access**: Admin Only (`require_admin`)
- **Summary**: Delete user account
- **Description**: Deletes a user profile from the database by UUID.
- **Path Parameters**:
  - `user_id` (`string (UUID)`, Required): UUID of the user to delete.
- **Response (`200 OK`)**:
```json
{
  "message": "User deleted"
}
```
- **Errors**:
  - `401 Unauthorized`: Not authenticated.
  - `403 Forbidden`: Admin role required.
  - `404 Not Found`: User not found.
