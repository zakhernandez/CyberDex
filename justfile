# CyberDex justfile
# Run `just` with no arguments to see all recipes.

# Variable: the full docker compose invocation we'll reuse.
compose := "docker compose -f infra/docker-compose.yml"

# Default recipe: list all recipes. Runs when you type `just` with no args.
default:
    @just --list

# --- Database ---

# Start the Postgres container in the background.
db-up:
    {{compose}} up -d

# Stop the Postgres container (data is preserved in the volume).
db-down:
    {{compose}} down

# Tail Postgres logs. Ctrl-C to exit.
db-logs:
    {{compose}} logs -f postgres

# Open a psql shell inside the running Postgres container.
db-shell:
    {{compose}} exec postgres psql -U cyberdex

# Nuke the database completely (deletes the volume) and restart fresh.
# Use with care — destroys all data.
db-reset:
    {{compose}} down -v
    {{compose}} up -d

# Show the status of the database container.
db-status:
    {{compose}} ps


api_dir := "apps/api"

# --- API ---

# Run the FastAPI dev server with auto-reload
api:
    cd {{api_dir}} && uv run uvicorn main:app --reload --port 8000

# Install / Sync API dependencies.
api-install:
    cd{{api_dir}} && uv sync