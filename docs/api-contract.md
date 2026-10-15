# Pixora — API contract

Every REST endpoint the frontend consumes. Statuses:
- ✅ implemented and tested
- ⏳ planned

Base path: `/api`.
Auth: JWT via `Authorization: Bearer <token>` except where noted.
Content type: `application/json` unless noted.

---

## Auth

### ✅ `POST /api/auth/register`
**Request:** `{ "email": "...", "password": "..." }`
**Response 201:** `{ "id": "...", "email": "...", "role": "user" }`
**Errors:** 400 invalid, 409 email taken.

### ✅ `POST /api/auth/login`
**Request:** `{ "email": "...", "password": "..." }`
**Response 200:** `{ "access_token": "...", "refresh_token": "...", "user": { "id", "email", "role" } }`
**Errors:** 401 invalid, 403 disabled.

### ✅ `POST /api/auth/refresh`
**Request:** `{ "refresh_token": "..." }`
**Response 200:** `{ "access_token": "..." }`

### ✅ `GET /api/auth/me`
**Response 200:** `{ "id", "email", "role", "is_active", "created_at" }`

### ✅ `POST /api/auth/change-password`
**Request:** `{ "old_password": "...", "new_password": "..." }`
**Response 200:** `{ "ok": true }`
**Errors:** 400 too-short / same password / missing fields, 401 wrong old password.

---

## Images

### ✅ `POST /api/images/upload`
Multipart. Field: `file`.
**Response 201:** `{ "id", "filename", "width", "height", "mime", "size_bytes", "thumb_url", "original_url", "created_at" }`
**Side effects:** fires `detect_nsfw` and `embed` jobs automatically.
**Errors:** 400 no file, 413 too large, 415 invalid image.

### ✅ `GET /api/images`
**Query:** `limit` (default 40, max 100), `offset` (default 0).
**Response 200:** `{ "images": [...], "count": N }`

### ✅ `GET /api/images/:id`
**Response 200:** full metadata + presigned URLs.

### ✅ `DELETE /api/images/:id`
**Response 200:** `{ "deleted": true, "id": "..." }`

---

## Jobs

### ✅ `POST /api/jobs`
**Request:** `{ "type": "...", "image_id": "...", "params": {...} }`
**Types:** `resize`, `convert`, `remove_bg`, `detect_nsfw`, `detect_ai`, `detect_objects`, `embed`, `generate`, `img2img`, `inpaint`, `controlnet`.
**Response 202:** serialized job with status `pending`.
**Errors:** 400 unknown type / invalid id / params must be object, 404 image not found.

### ✅ `GET /api/jobs/:id`
**Response 200:** `{ "id", "type", "status", "image_id", "params", "meta", "result_url", "error", "created_at", "started_at", "finished_at" }`
**Statuses:** `pending` | `running` | `done` | `failed` | `timeout`

### ✅ `GET /api/jobs`
**Query:** `limit`, `offset`, `status`, `type`.
**Response 200:** `{ "jobs": [...], "count": N }`

---

## Search

### ✅ `POST /api/search/semantic`
**Request:** `{ "query": "sunset over mountains", "limit": 20 }`
**Response 200:** `{ "query", "results": [ { "image_id", "filename", "score", "thumb_url" } ], "count" }`

### ✅ `POST /api/search/similar`
**Request:** `{ "image_id": "...", "limit": 20 }`
**Response 200:** `{ "reference_id", "results": [...], "count" }`
**Errors:** 400 no embedding yet, 404 image not found.

---

## Admin

All require `role == "admin"`.

### ✅ `GET /api/admin/users`
### ✅ `PATCH /api/admin/users/:id` — change role or `is_active`
### ✅ `GET /api/admin/jobs` — all users' jobs
### ✅ `GET /api/admin/nsfw-queue` — flagged images with presigned URLs
### ✅ `POST /api/admin/nsfw-queue/:id/approve` — clears flag, keeps score
### ✅ `POST /api/admin/nsfw-queue/:id/reject` — deletes DB row + MinIO objects

---

## Health

### ✅ `GET /api/health`
**Response 200:** `{ "status": "ok", "service": "pixora-api" }`

---

## Rate limits

| Endpoint | Limit |
|---|---|
| `POST /api/auth/register` | 10/hour |
| `POST /api/auth/login` | 30/hour |
| `POST /api/auth/refresh` | 60/hour |
| `POST /api/auth/change-password` | 10/hour |
| `POST /api/images/upload` | 60/hour |

Limits are shared across all Gunicorn workers via Redis.
