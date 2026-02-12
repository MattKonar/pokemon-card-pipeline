# Repo Standards

## Documentation First Rule
Any new component must be documented before or alongside the code change.
If it is not documented, it does not exist.

## Folder Conventions
docs: Documentation and runbooks
docker: Docker Compose and container config
sql: DDL and SQL transformations
src: Python pipeline code
data: Local output data, not committed
logs: Logs, not committed

## Secrets
Secrets live in a .env file and are never committed.

## Git Commit Style
Use short, descriptive commits:
- Add project charter
- Add docker compose for postgres
- Create bronze ingestion script

## Run Philosophy
Every run should be reproducible:
- No manual clicking steps required
- Minimal setup
- Clear failure messages
