# Project Charter: Pokémon Card Data Pipeline

## Purpose
Build a production style data engineering pipeline that ingests Pokémon card data from an API, stores raw data, transforms it into clean tables, and produces analytics ready outputs.

This repo is designed to demonstrate:
- API ingestion
- Medallion architecture (Bronze, Silver, Gold)
- PostgreSQL data modeling
- Docker reproducibility
- Logging and error handling
- Clear documentation and repeatable runs

## Definition of Done
The project is complete when:
1. A single command can stand up required services (Postgres via Docker).
2. A single pipeline run can ingest data from the API and store raw JSON (Bronze).
3. The pipeline can create cleaned, typed tables (Silver).
4. The pipeline can create aggregated reporting tables (Gold).
5. The pipeline can be rerun safely without creating duplicates.
6. Documentation explains how to run, how data flows, and how to troubleshoot.

## Data Flow
API -> Bronze -> Silver -> Gold -> Postgres

## Scope
In scope:
- Pull Pokémon card data from Pokémon TCG API
- Store raw JSON payloads
- Create clean relational tables for cards and sets
- Create simple aggregated tables

Out of scope for v1:
- Streaming ingestion
- Full CI CD pipeline
- Airflow or other orchestrators
