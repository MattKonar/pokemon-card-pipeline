# Runbook

This document explains how to start infrastructure and run the pipeline locally.

## Local Development Overview

We use Docker to run PostgreSQL locally.

The pipeline runs from Python and connects to Postgres using environment variables.

## Local Setup Steps

1. Install Docker Desktop
2. Clone repository
3. Create a .env file with database credentials
4. Run docker compose up -d
5. Run python src/main.py

## Expected Services

Postgres container
- Exposes port 5432
- Creates database pokemon
- Uses credentials defined in .env

## First Run Expectations

On first run:
- Schemas are created
- Bronze table is created
- No data exists yet

## Rerun Expectations

Pipeline must:
- Not duplicate rows
- Use upsert or unique constraints
