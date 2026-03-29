# API Routes Documentation

Simple reference for all API endpoints with request/response examples.

**Base URL:** `/api/v1`

---

## Authentication

### POST /api/v1/auth/signup

Register a new user account.

**Request Body:**
```json
{
  "username": "john_doe",
  "email": "john@example.com",
  "password": "securePassword123"
}
```

**Response (200 OK):**
```json
{
  "ok": true,
  "user": {
    "id": 1,
    "username": "john_doe",
    "email": "john@example.com"
  }
}
```

**Cookies Set:**
- `access_token` - JWT access token (HttpOnly)
- `refresh_token` - JWT refresh token (HttpOnly)

**Errors:**
- `409 Conflict` - User already exists
- `500 Internal Server Error` - Registration failed

---

### POST /api/v1/auth/login

Authenticate user and receive session cookies.

**Request Body:**
```json
{
  "login": "john@example.com",
  "password": "securePassword123"
}
```

**Notes:**
- `login` can be either email or username

**Response (200 OK):**
```json
{
  "ok": true,
  "user": {
    "id": 1,
    "username": "john_doe",
    "email": "john@example.com"
  }
}
```

**Cookies Set:**
- `access_token` - JWT access token (HttpOnly)
- `refresh_token` - JWT refresh token (HttpOnly)

**Errors:**
- `404 Not Found` - No user found with this username or email
- `401 Unauthorized` - Invalid login or password
- `500 Internal Server Error` - Cookie set failed

---

### POST /api/v1/auth/logout

Clear authentication cookies and logout user.

**Request Body:** None

**Response (200 OK):**
```json
{
  "ok": true
}
```

**Cookies Deleted:**
- `access_token`
- `refresh_token`

**Errors:**
- `500 Internal Server Error` - Cookie delete failed

---

### GET /api/v1/auth/verify

Verify if current authentication token is valid.

**Authentication:** Required (cookie-based)

**Request Body:** None

**Response (200 OK):**
```json
{
  "ok": true
}
```

**Errors:**
- `401 Unauthorized` - Invalid token

---

### POST /api/v1/auth/refresh

Refresh access token using refresh token from cookies.

**Authentication:** Required (refresh token in cookie)

**Request Body:** None

**Response (200 OK):**
```json
{
  "message": "Token refreshed",
  "user_id": "1"
}
```

**Cookies Updated:**
- `access_token` - New JWT access token

---

## Time Entries

### POST /api/v1/time-entries/start

Start a new timer session for the authenticated user.

**Authentication:** Required

**Request Body:** None (empty object `{}`)

**Response (200 OK):**
```json
{
  "id": 42,
  "started_at": "2026-02-04T01:30:00.000Z",
  "user_id": 1
}
```

**Errors:**
- `409 Conflict` - Timer is already running
- `401 Unauthorized` - Not authenticated
- `500 Internal Server Error` - Internal server error

---

### PATCH /api/v1/time-entries/stop

Stop the currently running timer session.

**Authentication:** Required

**Request Body:** None (empty object `{}`)

**Note:** Automatically finds and stops the active timer for the authenticated user.

**Response (200 OK):**
```json
{
  "id": 42,
  "started_at": "2026-02-04T01:30:00.000Z",
  "ended_at": "2026-02-04T02:15:00.000Z"
}
```

**Errors:**
- `404 Not Found` - No running timer found
- `401 Unauthorized` - Not authenticated
- `500 Internal Server Error` - Error stopping timer

---

### GET /api/v1/time-entries/current-running

Get currently running timer session (if any).

**Authentication:** Required

**Request Body:** None

**Response (200 OK) - Timer running:**
```json
{
  "id": 42,
  "started_at": "2026-02-04T01:30:00.000Z"
}
```

**Response (200 OK) - No timer running:**
```json
null
```

**Errors:**
- `401 Unauthorized` - Not authenticated

---

### GET /api/v1/timer/

Get all timer sessions for the authenticated user.

**Authentication:** Required

**Request Body:** None

**Response (200 OK):**
```json
[
  {
    "id": 42,
    "user_id": 1,
    "started_at": "2026-02-04T01:30:00.000Z",
    "ended_at": "2026-02-04T02:15:00.000Z"
  },
  {
    "id": 41,
    "user_id": 1,
    "started_at": "2026-02-03T10:00:00.000Z",
    "ended_at": "2026-02-03T12:30:00.000Z"
  }
]
```

**Response (200 OK) - No entries:**
```json
[]
```

**Errors:**
- `401 Unauthorized` - Not authenticated
- `500 Internal Server Error` - Error getting entries

---

### GET /api/v1/timer/{entry_id}

Get a specific timer entry by ID.

**Authentication:** Required

**Path Parameters:**
- `entry_id` (integer) - ID of the timer entry

**Request Body:** None

**Response (200 OK):**
```json
{
  "id": 42,
  "user_id": 1,
  "started_at": "2026-02-04T01:30:00.000Z",
  "ended_at": "2026-02-04T02:15:00.000Z"
}
```

**Errors:**
- `404 Not Found` - Entry not found
- `401 Unauthorized` - Not authenticated
- `500 Internal Server Error` - Error getting entry

---

### POST /api/v1/timer/pause

Pause a running timer session (not implemented).

**Authentication:** Required

**Request Body:** None

**Response (200 OK):**
```json
"pause"
```

**Note:** This endpoint is a placeholder and not fully implemented yet.

---

## Authentication Flow

All authenticated endpoints require valid JWT tokens stored in HttpOnly cookies:

1. **Signup/Login** → Receive `access_token` and `refresh_token` cookies
2. **Make API calls** → Browser automatically sends cookies
3. **Token expires** → Use `/auth/refresh` to get new access token
4. **Logout** → Call `/auth/logout` to clear cookies

**Cookie Names:**
- Access Token: `access_token`
- Refresh Token: `refresh_token`

**Cookie Settings:**
- HttpOnly: `true`
- SameSite: `lax`
- Secure: `false` (development), `true` (production)
- Path: `/`

---

## Common Error Responses

**401 Unauthorized:**
```json
{
  "detail": "Invalid token"
}
```

**404 Not Found:**
```json
{
  "detail": "No running timer found"
}
```

**409 Conflict:**
```json
{
  "detail": "Timer is already running"
}
```

**500 Internal Server Error:**
```json
{
  "detail": "Internal server error"
}
```

---

## Data Types

### DateTime Format
All datetime fields use ISO 8601 format with timezone:
```
"2026-02-04T01:30:00.000Z"
```

### User Object
```json
{
  "id": 1,
  "username": "john_doe",
  "email": "john@example.com"
}
```

### Timer Entry Object
```json
{
  "id": 42,
  "user_id": 1,
  "started_at": "2026-02-04T01:30:00.000Z",
  "ended_at": "2026-02-04T02:15:00.000Z"  // null if still running
}
```

---

## Notes

- All endpoints use JSON for request/response bodies
- Authentication uses HttpOnly cookies (automatic in browser)
- Timestamps are in UTC timezone
- User can only access their own timer entries
- Only one timer can run at a time per user
