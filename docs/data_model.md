# Data Model

This document describes the schema, grain, and purpose of each table in the Lakehouse.

---

## Bronze Table

### Table Name
stock_lakehouse.bronze_stock_prices

### Grain
One raw record per ticker per trading day as ingested.

### Schema
- ticker (STRING)
- trade_date (STRING)
- open (STRING)
- high (STRING)
- low (STRING)
- close (STRING)
- volume (STRING)
- ingestion_ts (TIMESTAMP)
- source (STRING)

### Notes
- Data types are intentionally left as STRING
- Duplicates are allowed
- No business rules are applied

---

## Silver Table

### Table Name
stock_lakehouse.silver_stock_prices

### Grain
One row per (ticker, trade_date)

### Schema
- ticker (STRING)
- trade_date (DATE)
- open_price (DECIMAL(18,4))
- high_price (DECIMAL(18,4))
- low_price (DECIMAL(18,4))
- close_price (DECIMAL(18,4))
- volume (BIGINT)

### Notes
- Schema is enforced
- Data is deduplicated
- Late-arriving data is handled via MERGE

---

## Gold Table

### Table Name
stock_lakehouse.gold_stock_daily_metrics

### Grain
One row per (ticker, trade_date)

### Schema
- ticker (STRING)
- trade_date (DATE)
- daily_return_pct (DECIMAL(10,4))
- ma_7 (DECIMAL(18,4))
- ma_30 (DECIMAL(18,4))
- volatility_30d (DECIMAL(18,6))

### Notes
- Derived entirely from Silver
- Optimized for analytics and querying
