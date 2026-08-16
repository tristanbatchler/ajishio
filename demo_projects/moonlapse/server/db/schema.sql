CREATE TABLE IF NOT EXISTS users
(
  id INTEGER PRIMARY KEY NOT NULL,
  username TEXT NOT NULL UNIQUE,
  password_hash TEXT NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  last_login TIMESTAMP,
  last_updated TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS user_logins
(
  id INTEGER PRIMARY KEY NOT NULL,
  user_id INTEGER NOT NULL,
  login_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  ip_address TEXT NOT NULL,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS user_login_failures
(
  id INTEGER PRIMARY KEY NOT NULL,
  user_id INTEGER NOT NULL,
  added TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  ip_address TEXT NOT NULL,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS user_lockouts
(
  id INTEGER PRIMARY KEY NOT NULL,
  user_id INTEGER NOT NULL,
  added TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  expiration TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS entities
(
  id INTEGER PRIMARY KEY NOT NULL,
  entity_type INTEGER NOT NULL,
  added TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  last_updated TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  x_position INTEGER NOT NULL,
  y_position INTEGER NOT NULL,
  entity_name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS entities_resources
(
  entity_id INTEGER PRIMARY KEY NOT NULL,
  level_required INTEGER NOT NULL, 
  FOREIGN KEY (entity_id) REFERENCES entities(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS actors
(
  entity_id INTEGER PRIMARY KEY NOT NULL,
  user_id INTEGER NOT NULL UNIQUE, -- Only one actor per user 
  FOREIGN KEY (entity_id) REFERENCES entities(id) ON DELETE CASCADE,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Indexes for Foreign Keys to optimize joins and ON DELETE performance
CREATE INDEX IF NOT EXISTS idx_user_logins_user_id ON user_logins(user_id);
CREATE INDEX IF NOT EXISTS idx_user_login_failures_user_id ON user_login_failures(user_id);
CREATE INDEX IF NOT EXISTS idx_user_lockouts_user_id ON user_lockouts(user_id);
CREATE INDEX IF NOT EXISTS idx_actors_user_id ON actors(user_id);
-- Note: Separate indexes for entity_id on entities_resources and actors are omitted 
-- because those columns are already defined as PRIMARY KEYs, which automatically create indexes.
