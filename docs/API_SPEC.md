# REST API Specification

Base URL local qua Nginx: `http://localhost:8080/api`

## Auth

### POST /auth/register

Request:

```json
{
  "email": "test@example.com",
  "password": "Password123",
  "full_name": "Test User"
}
```

### POST /auth/login

Response trả `access_token` và `refresh_token`.

### POST /auth/refresh-token

Request:

```json
{"refresh_token":"..."}
```

### POST /auth/logout

Cần Bearer token và refresh token trong body.

### GET /me

Lấy thông tin user hiện tại.

## Upload

### POST /uploads

`multipart/form-data`:

- `job_id`: UUID
- `file_type`: `cv` hoặc `jd`
- `file`: PDF/DOCX

## Jobs

### POST /jobs

Tạo analysis job.

### GET /jobs

Danh sách job của user hiện tại.

### GET /jobs/{job_id}

Chi tiết job.

### POST /jobs/{job_id}/enqueue

Đưa job vào queue sau khi có đủ CV và JD.

### GET /jobs/{job_id}/result

Lấy kết quả khi job đã completed.

## Admin

Cần user role `admin`.

- `GET /admin/users`
- `GET /admin/jobs`
- `GET /admin/jobs/{job_id}/events`
