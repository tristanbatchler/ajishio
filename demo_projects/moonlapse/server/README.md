# Moonlapse Server

A MUD demo that includes a well-architected server featuring a state machine and database connection.

## Run

```bash
cd demo_projects/moonlapse
uv run -m demo_projects.moonlapse.server.server.main
```

## Architecture

- `state.py` - interface for server state
- `hub.py` - interface for server hub
- `connection.py` - implementation of the server hub
- `client.py` - basic data structure for a connected client
- `db/`
    - `schema.sql` - database schema (do edit)
    - `query.sql` - database queries (do edit)
    - `sqlc.yaml` - sqlc config (only edit if you know what you're doing)
    - everything else is generated code (do NOT edit)

## Regenerating DB code

```bash
cd demo_projects/moonlapse/server/db
uv tool run sqlc generate
```

Changes to `schema.sql` or `query.sql` require re-running this.
