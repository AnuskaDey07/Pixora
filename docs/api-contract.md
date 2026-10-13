# Pixora — API contract

Every REST endpoint the frontend consumes. Keep this current.

Base path: /api
Auth: JWT via Authorization: Bearer <token> except where noted.
Content type: application/json unless noted.

---

## Auth

### POST /api/auth/register
Create a user.

Request: { "email": "user@example.com", "password": "..." }
Response 201: { "id": "...", "email": "...", "role": "user" }
Errors: 400 invalid, 409 email taken.

### POST /api/auth/login
Request: { "email": "...", "password": "..." }
Response 200: { "access_token": "...", "refresh_token": "..." }
Errors: 401.

### POST /api/auth/refresh
Requires refresh token in Authorization.
Response 200: { "access_token": "..." }

### GET /api/auth/me
Requires access token.
Response 200: { "id": "...", "email": "...", "role": "..." }

---

## Images

### POST /api/images/upload
Multipart/form-data. Field: file.
Response 201: { "id": "...", "width": 1024, "height": 768, "mime": "image/png", "thumb_url": "...", "original_url": "..." }
Errors: 400 bad file, 413 too large, 415 unsupported type.

### GET /api/images
List current user's images. Query: limit, offset.

### GET /api/images/:id
Response 200: image metadata + presigned URLs.

### DELETE /api/images/:id

---

## Jobs

### POST /api/jobs
Request: { "type": "remove_bg", "image_id": "...", "params": { } }
Types: remove_bg, resize, convert, detect_nsfw, detect_ai, detect_objects, generate, img2img, inpaint, controlnet.
Response 202: { "job_id": "...", "status": "pending" }

### GET /api/jobs/:id
Response 200: { "id": "...", "type": "...", "status": "pending|running|done|failed|timeout", "result_url": "...", "meta": { }, "error": null }

### GET /api/jobs
List current user's jobs. Query: limit, offset, status, type.

---

## Search

### POST /api/search/semantic
Request: { "query": "sunset over mountains", "limit": 20 }
Response 200: { "results": [ { "image_id": "...", "score": 0.87, "thumb_url": "..." } ] }

### POST /api/search/similar
Request: { "image_id": "...", "limit": 20 }
Response 200: same shape.

---

## Admin

All require role == "admin".

- GET /api/admin/users
- PATCH /api/admin/users/:id — disable / enable
- GET /api/admin/jobs — all users' jobs
- GET /api/admin/nsfw-queue — flagged images pending review
- POST /api/admin/nsfw-queue/:id/approve
- POST /api/admin/nsfw-queue/:id/reject

---

## Health

### GET /api/health
Response 200: { "status": "ok", "service": "pixora-api" }

---

Skeleton — populated as endpoints are implemented.
