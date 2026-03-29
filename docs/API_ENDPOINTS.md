# API Endpoints Documentation

## Authentication Endpoints

### Web Authentication (Form-based)

#### `GET /signup`
- **Description**: Returns signup page HTML
- **Response**: HTML page for user registration

#### `POST /signup`
- **Description**: Register a new user via form submission
- **Parameters** (Form):
  - `username` (string, required): User's username
  - `email` (string, required): User's email address
  - `password` (string, required): User's password
  - `confirm_password` (string, required): Password confirmation
- **Response**: Redirects to `/login` on success or `/signup` with error on failure

#### `GET /login`
- **Description**: Returns login page HTML
- **Response**: HTML page for user login

#### `POST /login`
- **Description**: Authenticate user via form submission
- **Parameters** (Form):
  - `login` (string, required): Username or email
  - `password` (string, required): User's password
- **Response**: Redirects to `/dashboard` on success with authentication cookies set
- **Cookies Set**: `access_token`, `refresh_token`

#### `POST /logout`
- **Description**: Log out user and clear authentication cookies
- **Response**: Redirects to `/` (homepage)
- **Cookies Cleared**: `access_token`, `refresh_token`

---

### API Authentication (JSON-based)

#### `POST /api/v1/auth/signup`
- **Description**: Register a new user via API
- **Request Body** (JSON):
  ```json
  {
    "username": "string",
    "email": "string",
    "password": "string"
  }
  ```
- **Response** (JSON):
  ```json
  {
    "ok": true,
    "user": {
      "id": "number",
      "username": "string",
      "email": "string"
    }
  }
  ```
- **Status Codes**:
  - `200`: Success
  - `409`: User already exists
  - `500`: Registration failed
- **Cookies Set**: `access_token`, `refresh_token`

#### `POST /api/v1/auth/login`
- **Description**: Authenticate user via API
- **Request Body** (JSON):
  ```json
  {
    "login": "string",
    "password": "string"
  }
  ```
- **Response** (JSON):
  ```json
  {
    "ok": true,
    "user": {
      "id": "number",
      "username": "string",
      "email": "string"
    }
  }
  ```
- **Status Codes**:
  - `200`: Success
  - `401`: Invalid credentials
  - `404`: User not found
  - `500`: Cookie set failed
- **Cookies Set**: `access_token`, `refresh_token`

#### `POST /api/v1/auth/logout`
- **Description**: Log out user via API
- **Response** (JSON):
  ```json
  {
    "ok": true
  }
  ```
- **Status Codes**:
  - `200`: Success
  - `500`: Cookie delete failed
- **Cookies Cleared**: `access_token`, `refresh_token`

#### `GET /api/v1/auth/verify`
- **Description**: Verify if current authentication token is valid
- **Authentication**: Required (JWT token via cookie)
- **Response** (JSON):
  ```json
  {
    "ok": true
  }
  ```
- **Status Codes**:
  - `200`: Token is valid
  - `401`: Invalid token

---

## Token Management

#### `POST /auth/refresh`
- **Description**: Refresh access token using refresh token
- **Authentication**: Required (refresh token via cookie)
- **Response** (JSON):
  ```json
  {
    "message": "Token refreshed",
    "user_id": "string"
  }
  ```
- **Cookies Set**: New `access_token`

---

## Time Tracking Endpoints

#### `POST /api/v1/time-entries/start`
- **Description**: Start a new time tracking session
- **Authentication**: Required (JWT token)
- **Response** (JSON):
  ```json
  {
    "id": "number",
    "started_at": "datetime",
    "user_id": "number"
  }
  ```
- **Status Codes**:
  - `200`: Timer started successfully
  - `409`: Timer is already running
  - `500`: Internal server error

#### `POST /api/v1/time-entries/stop`
- **Description**: Stop the currently running time tracking session
- **Authentication**: Required (JWT token)
- **Response** (JSON):
  ```json
  {
    "id": "number",
    "started_at": "datetime",
    "ended_at": "datetime"
  }
  ```
- **Status Codes**:
  - `200`: Timer stopped successfully
  - `404`: No running timer found
  - `500`: Error stopping timer

#### `GET /api/v1/time-entries/current-running`
- **Description**: Get the currently running time tracking session
- **Authentication**: Required (JWT token)
- **Response** (JSON):
  ```json
  {
    "id": "number",
    "started_at": "datetime"
  }
  ```
- **Response**: Returns `null` if no timer is running

#### `POST /api/v1/time-entries/pause`
- **Description**: Pause the current timer (placeholder endpoint)
- **Authentication**: Required (JWT token)
- **Response**: Returns string "pause"

#### `GET /api/v1/time-entries`
- **Description**: Get all time tracking sessions for the authenticated user
- **Authentication**: Required (JWT token)
- **Response** (JSON): Array of time entry objects
  ```json
  [
    {
      "id": "number",
      "user_id": "number",
      "started_at": "datetime",
      "ended_at": "datetime|null"
    }
  ]
  ```
- **Response**: Returns empty array `[]` if no entries found

#### `GET /api/v1/timer/{entry_id}`
- **Description**: Get a specific time tracking session by ID
- **Authentication**: Required (JWT token)
- **Parameters**:
  - `entry_id` (path parameter, number): ID of the time entry
- **Response** (JSON):
  ```json
  {
    "id": "number",
    "user_id": "number",
    "started_at": "datetime",
    "ended_at": "datetime|null"
  }
  ```
- **Status Codes**:
  - `200`: Entry found
  - `404`: Entry not found
  - `500`: Error getting entry

---

## Page Endpoints

#### `GET /`
- **Description**: Landing page
- **Response**: HTML page

#### `GET /dashboard`
- **Description**: User dashboard (protected)
- **Authentication**: Required (JWT token)
- **Response**: HTML page

#### `GET /playground`
- **Description**: Development playground/testing endpoint
- **Response**: Decoded JWT token information

---

## Notes

- **Authentication**: Most API endpoints require JWT authentication via HTTP-only cookies
- **Cookie Names**: Configured via `settings.jwt_access_cookie_name` and `settings.jwt_refresh_cookie_name`
- **Cookie Settings**: 
  - `httponly=True`
  - `samesite="lax"` or `"none"`
  - `secure=True` (for production)
- **Error Handling**: All endpoints return appropriate HTTP status codes with error details
