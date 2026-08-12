/* USERS */
-- name: GetUser :one
SELECT * FROM users WHERE id = ?;

-- name: ListUsers :many
SELECT * FROM users ORDER BY id LIMIT ? OFFSET ?;

-- name: GetUserByUsername :one
SELECT * FROM users WHERE username = ?;

-- name: CreateUser :one
INSERT INTO users (username, password_hash) VALUES (?, ?)
RETURNING *;

-- name: UpdateUserLastLogin :one
UPDATE users SET last_login = CURRENT_TIMESTAMP, last_updated = CURRENT_TIMESTAMP WHERE id = ?
RETURNING *;

-- name: CountUsers :one
SELECT COUNT(*) FROM users;

-- name: UpdateUserPasswordHash :one
UPDATE users SET password_hash = ?, last_updated = CURRENT_TIMESTAMP WHERE id = ?
RETURNING *;

-- name: UpdateUserLastUpdated :one
UPDATE users SET last_updated = CURRENT_TIMESTAMP WHERE id = ?
RETURNING *;

/* USER_LOGINS */
-- name: CreateUserLogin :one
INSERT INTO user_logins (user_id, ip_address) VALUES (?, ?)
RETURNING *;

-- name: CreateUserLoginFailure :one
INSERT INTO user_login_failures (user_id, ip_address) VALUES (?, ?)
RETURNING *;

/* USER_LOCKOUTS */
-- name: CreateUserLockout :one
INSERT INTO user_lockouts (user_id, expiration) VALUES (?, ?)
RETURNING *;

-- name: GetUserLockoutsByUserId :many
SELECT * FROM user_lockouts WHERE user_id = ?;

-- name: DeleteUserLockoutByUserId :exec
DELETE FROM user_lockouts WHERE user_id = ?;
