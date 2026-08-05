# Error Handling Specification

This document details the standardized exception hierarchy, error handlers, HTTP status codes, and error response formats implemented across the application (`app/core/exceptions.py` and `app/core/exception_handlers.py`).

---

## 1. Standard Error Response Structure

All application errors return a consistent JSON response body:

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE_STRING",
    "message": "Human-readable description of the error",
    "details": null
  }
}
```

- **`success`** (`boolean`): Always `false` on error.
- **`error.code`** (`string`): Machine-readable uppercase error identifier.
- **`error.message`** (`string`): Concise human-readable explanation.
- **`error.details`** (`any | null`): Additional contextual payload (such as validation error lists or null).

---

## 2. Application Exception Hierarchy

Defined in `app.core.exceptions.AppException`:

```
AppException (Base Exception)
├── ResourceNotFoundException (404 Not Found)
├── InsufficientBalanceException (400 Bad Request)
├── InvalidOperationException (400 Bad Request)
├── UnauthorizedException (401 Unauthorized)
├── ForbiddenException (403 Forbidden)
├── DuplicateOperationException (409 Conflict)
└── DatabaseException (500 Internal Server Error)
```

| Exception Class | Error Code | HTTP Status Code | Default Message |
| :--- | :--- | :--- | :--- |
| `ResourceNotFoundException` | `RESOURCE_NOT_FOUND` | `404 NOT FOUND` | Resource not found |
| `InsufficientBalanceException` | `WALLET_INSUFFICIENT_BALANCE` | `400 BAD REQUEST` | Insufficient wallet balance |
| `InvalidOperationException` | `INVALID_OPERATION` | `400 BAD REQUEST` | Invalid operation |
| `UnauthorizedException` | `UNAUTHORIZED` | `401 UNAUTHORIZED` | Authentication credentials were missing or invalid |
| `ForbiddenException` | `FORBIDDEN` | `403 FORBIDDEN` | Access forbidden |
| `DuplicateOperationException` | `DUPLICATE_OPERATION` | `409 CONFLICT` | Duplicate operation detected |
| `DatabaseException` | `DATABASE_ERROR` | `500 INTERNAL SERVER ERROR` | Database operation failed |

---

## 3. Global Exception Handlers

Registered globally on the FastAPI application instance in `app/core/exception_handlers.py`:

### 1. `AppException` Handler
Catches all subclasses of `AppException` and returns the structured JSON response matching the exception's `status_code`, `code`, `message`, and `details`.

### 2. Pydantic `RequestValidationError` Handler
Catches request payload schema or parameter validation failures.
- **HTTP Status**: `422 Unprocessable Entity`
- **Error Code**: `VALIDATION_ERROR`
- **Response Format**:
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Input validation failed",
    "details": [
      {
        "loc": ["body", "amount"],
        "msg": "Input should be greater than 0",
        "type": "greater_than"
      }
    ]
  }
}
```

### 3. SQLAlchemy `IntegrityError` Handler
Catches database unique constraint or foreign key violations.
- **HTTP Status**: `409 Conflict`
- **Error Code**: `DUPLICATE_OPERATION`
- **Message**: `"Database constraint violation or duplicate record"`

### 4. `SQLAlchemyError` Handler
Catches unexpected database engine errors.
- **HTTP Status**: `500 Internal Server Error`
- **Error Code**: `DATABASE_ERROR`
- **Message**: `"A database error occurred while processing your request"`

### 5. Generic `Exception` Handler
Catches unhandled runtime exceptions.
- **HTTP Status**: `500 Internal Server Error`
- **Error Code**: `INTERNAL_SERVER_ERROR`
- **Message**: `"An unexpected error occurred"`

---

## 4. HTTP Status Code Reference

| Status Code | Description | Typical Triggers |
| :--- | :--- | :--- |
| **`400 Bad Request`** | Invalid operation or insufficient wallet balance | Withdrawal exceeding balance; project close with <2 investors; invalid transaction amount |
| **`401 Unauthorized`** | Authentication failure | Missing, expired, or corrupted `access_token` cookie |
| **`403 Forbidden`** | Authorization role failure | Investor attempting to access `/admin/*` routes, or admin accessing `/investor/*` routes |
| **`404 Not Found`** | Missing entity | Requested user ID, wallet UUID, project UUID, or request UUID does not exist |
| **`409 Conflict`** | Duplicate operation | Idempotency key collision or database unique constraint violation |
| **`422 Unprocessable Entity`** | Schema validation error | Invalid email format, missing required body field, or invalid enum value |
| **`500 Internal Server Error`** | Unhandled server error | Database connection breakdown or unhandled exception |
