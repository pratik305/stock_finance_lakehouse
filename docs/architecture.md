# Architecture Overview

This project implements an end-to-end **Lakehouse architecture** using Databricks and Delta Lake for stock market analytics.

The design follows the **Medallion Architecture** pattern to separate concerns, improve data reliability, and support incremental processing.

---

## High-Level Architecture

Alpha Vantage API (local extraction)
→ Raw CSV Files
→ Bronze Delta Table
→ Silver Delta Table
→ Gold Delta Table

---

## Architecture Layers

### Bronze Layer
- Purpose: Capture raw, immutable data exactly as received
- Storage format: Delta Lake
- Write strategy: Append-only
- Characteristics:
  - No schema enforcement
  - No deduplication
  - Full traceability via ingestion metadata

### Silver Layer
- Purpose: Create a clean, correct, trusted dataset
- Storage format: Delta Lake
- Write strategy: Incremental MERGE
- Characteristics:
  - Enforced schema and data types
  - Deduplicated on business keys
  - Handles late-arriving and corrected data

### Gold Layer
- Purpose: Provide analytics-ready data for consumption
- Storage format: Delta Lake
- Write strategy: Rebuild (INSERT OVERWRITE)
- Characteristics:
  - Business metrics and aggregations
  - SQL-first design
  - Stable schema for downstream analytics

---

## Design Principles

- Separation of ingestion and processing
- Idempotent and re-runnable pipelines
- Append-only raw data
- Incremental correctness using Delta MERGE
- SQL-based analytics for clarity and maintainability

---

## Why Databricks + Delta Lake

- ACID guarantees on data lakes
- Scalable Spark execution
- Native support for incremental MERGE
- Time travel and auditability
- Unified analytics and engineering workflows
