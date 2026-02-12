# Architecture

## System overview
This project ingests Pokémon card data from an external API and organizes it into three layers:

1. Bronze: raw payloads
2. Silver: cleaned structured tables
3. Gold: aggregated reporting tables

The pipeline is batch based and rerunnable.

## Data Flow

External API
-> Bronze
-> Silver
-> Gold
-> PostgreSQL

## Design Principles

Reproducibility
The project must run from scratch with minimal setup.

Idempotency
Rerunning the pipeline must not create duplicates.

Observability
Logs must clearly show pipeline steps and failures.

