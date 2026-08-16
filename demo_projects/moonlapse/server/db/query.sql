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

/* USER_LOGIN_FAILURES */
-- name: CreateUserLoginFailure :one
INSERT INTO user_login_failures (user_id, ip_address) VALUES (?, ?)
RETURNING *;

-- name: CountUserLoginFailuresByUserIdSince :one
SELECT COUNT(*) FROM user_login_failures WHERE user_id = ? AND added >= ?;

/* USER_LOCKOUTS */
-- name: CreateUserLockout :one
INSERT INTO user_lockouts (user_id, expiration) VALUES (?, ?)
RETURNING *;

-- name: GetActiveUserLockoutsByUserId :many
SELECT * FROM user_lockouts WHERE user_id = ? AND (expiration IS NULL OR expiration > CURRENT_TIMESTAMP);

-- name: DeleteUserLockoutByUserId :exec
DELETE FROM user_lockouts WHERE user_id = ?;

/* ENTITIES */
-- name: CreateEntity :one
INSERT INTO entities (
  entity_type,
  entity_name,
  x_position,
  y_position
) VALUES (?, ?, ?, ?)
RETURNING *;

-- name: UpdateEntityPosition :one
UPDATE entities
SET
    x_position = ?,
    y_position = ?,
    last_updated = CURRENT_TIMESTAMP
WHERE id = ?
RETURNING *;

/* ACTORS */
-- name: GetActorByUserId :one
SELECT
  a.entity_id,
  a.user_id,
  e.entity_type,
  e.entity_name,
  a.sprite_image_index, 
  e.x_position,
  e.y_position,
  e.added,
  e.last_updated
FROM actors AS a
JOIN entities AS e ON e.id = a.entity_id
WHERE a.user_id = ?;

-- name: CreateActor :one
INSERT INTO actors (
  entity_id,
  user_id,
  sprite_image_index
) VALUES (?, ?, ?)
RETURNING *;