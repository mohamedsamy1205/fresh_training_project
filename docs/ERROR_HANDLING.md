# Error Handling & Exceptions Specification

This document details the standardized exception hierarchy, error handling middleware, OpenTelemetry trace recording, HTTP status codes, and JSON response formats implemented across the application (`app/core/exceptions.py` and `app/core/exception_handlers.py`).

---

## 1. Standard Error Response Envelope

All application errors return a structured JSON response body:

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE_STRING",
    "message": "Human-readable explanation of the error",
    "details": null
  }
}
```

- **`success`** (`boolean`): Always `false` on errors.
- **`error.code`** (`string`): Machine-readable uppercase identifier for programmatic handling.
- **`error.message`** (`string`): Clear, human-readable description of what caused the error.
- **`error.details`** (`any | null`): Additional contextual metadata (such as schema validation errors, rate limit window info, or `null`).

---

## 2. Application Exception Hierarchy

All custom application exceptions inherit from `app.core.exceptions.AppException`:

```text
AppException (Base Exception)
├── ResourceNotFoundException       (404 Not Found)
├── InsufficientBalanceException     (400 Bad Request)
├── InvalidOperationException        (400 Bad Request)
├── UnauthorizedException            (401 Unauthorized)
├── ForbiddenException               (403 Forbidden)
├── DuplicateOperationException      (409 Conflict)
├── DatabaseException                (500 Internal Server Error)
└── RateLimitExceededException       (429 Too Many Requests)
```

### Exception Reference Table

| Exception Class | Error Code | HTTP Status Code | Default Message | Typical Use Case |
| :--- | :--- | :--- | :--- | :--- |
| `ResourceNotFoundException` | `RESOURCE_NOT_FOUND` | `404 NOT FOUND` | Resource not found | Entity (User, Wallet, Project, Request, Session) does not exist |
| `InsufficientBalanceException` | `WALLET_INSUFFICIENT_BALANCE`| `400 BAD REQUEST` | Insufficient wallet balance | Wallet balance is lower than withdrawal or investment amount |
| `InvalidOperationException` | `INVALID_OPERATION` | `400 BAD REQUEST` | Invalid operation | Business rule violation (e.g. project not active, $<2$ investors to close) |
| `UnauthorizedException` | `UNAUTHORIZED` | `401 UNAUTHORIZED`| Authentication credentials were missing or invalid | Missing/expired/invalid JWT, locked account, invalid session |
| `ForbiddenException` | `FORBIDDEN` | `403 FORBIDDEN` | Access forbidden | Role permission mismatch or attempting to access another user's entity |
| `DuplicateOperationException` | `DUPLICATE_OPERATION` | `409 CONFLICT` | Duplicate operation detected | Email duplicate, unique constraint violation |
| `DatabaseException` | `DATABASE_ERROR` | `500 INTERNAL SERVER ERROR` | Database operation failed | Database communication error or unexpected query failure |
| `RateLimitExceededException` | `RATE_LIMIT_EXCEEDED` | `429 TOO MANY REQUESTS` | Too many requests. Please try again later. | Request threshold exceeded for a specific endpoint window |

---

## 3. Global Exception Handlers & OpenTelemetry Instrumentation

Global exception handlers are registered in `app/core/exception_handlers.py`. Each handler automatically records the exception into the active OpenTelemetry span via `_record_span_exception`:

### 1. `AppException` Handler
Catches all subclasses of `AppException` and maps them directly to the corresponding HTTP status code:
```json
{
  "success": false,
  "error": {
    "code": "WALLET_INSUFFICIENT_BALANCE",
    "message": "Insufficient balance in investor wallet.",
    "details": null
  }
}
```

### 2. Pydantic `RequestValidationError` Handler
Catches schema validation failures on request bodies, query parameters, and headers:
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
        "type": "greater_than",
        "loc": ["body", "amount"],
        "msg": "Input should be greater than 0",
        "input": 0
      }
    ]
  }
}
```

### 3. Rate Limit Exceeded Handler (`RateLimitExceededException`)
Triggered when an authenticated user exceeds the Redis sliding-window limit for a protected endpoint:
- **HTTP Status**: `429 Too Many Requests`
- **Error Code**: `RATE_LIMIT_EXCEEDED`
- **Response Format**:
```json
{
  "success": false,
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Too many requests. Please try again later.",
    "details": {
      "limit": 5,
      "window": "60 sec"
    }
  }
}
```

### 4. SQLAlchemy `IntegrityError` Handler
Catches database-level unique constraint or foreign key violations:
- **HTTP Status**: `409 Conflict`
- **Error Code**: `DUPLICATE_OPERATION`
- **Message**: `"Database constraint violation or duplicate record"`

### 5. `SQLAlchemyError` Handler
Catches general database engine failures:
- **HTTP Status**: `500 Internal Server Error`
- **Error Code**: `DATABASE_ERROR`
- **Message**: `"A database error occurred while processing your request"`

### 6. Generic `Exception` Handler
Catches unhandled runtime exceptions:
- **HTTP Status**: `500 Internal Server Error`
- **Error Code**: `INTERNAL_SERVER_ERROR`
- **Message**: `"An unexpected error occurred"`
