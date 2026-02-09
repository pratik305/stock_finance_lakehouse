# End-to-End Stock Finance Analytics Lakehouse

An end-to-end **Lakehouse data engineering project** built using **Databricks Community Edition**, **Delta Lake**, **PySpark**, and **Spark SQL**.  
The project demonstrates production-style ingestion, incremental processing, and analytics-ready modeling using the **Medallion Architecture (Bronze → Silver → Gold)**.


---

## Project Overview

The goal of this project is to design and implement a **reliable, incremental analytics pipeline** for stock market data, focusing on:

- Correct lakehouse architecture
- Incremental data processing using Delta MERGE
- Schema enforcement and deduplication
- SQL-based analytical modeling
- Clear documentation of assumptions and trade-offs

---

## High-Level Architecture

```text
Alpha Vantage API (local extraction)
↓
Raw CSV Files
↓
Bronze Delta Table (raw, append-only)
↓
Silver Delta Table (clean, deduplicated, MERGE)
↓
Gold Delta Table (analytics-ready metrics)
```


---

## Technology Stack

- **Databricks Community Edition**
- **Apache Spark (PySpark)**
- **Delta Lake**
- **Spark SQL**
- **Python**
- **Unity Catalog Volumes**

---

## Data Source

- **Source:** Alpha Vantage (free tier)
- **Data:** Daily stock prices (OHLCV)
- **Granularity:** One record per ticker per trading day
- **Limitation:** Free tier provides ~100 recent trading days per ticker

API extraction is performed **locally** to avoid coupling Spark jobs with external rate limits.

---

## Project Structure

``` text
stock-finance-lakehouse/
│
├── ingestion/
│ └── alpha_vantage_extractor.py
│
├── databricks/
│ ├── 01_bronze_ingestion.py
│ ├── 02_silver_transformations.py
│ └── 03_gold_analytics.sql
│
├── docs/
│ ├── architecture.md
│ ├── data_model.md
│ ├── incremental_logic.md
│ └── assumptions.md
│
└── README.md
```

---

## Pipeline Layers

### Bronze Layer
- Stores raw data exactly as received
- Append-only Delta table
- No schema enforcement or deduplication
- Includes ingestion metadata for traceability

**Purpose:** Preserve raw truth and enable reprocessing.

---

### Silver Layer
- Reads from Bronze
- Enforces schema and data types
- Deduplicates records using window functions
- Uses **Delta MERGE** on `(ticker, trade_date)`
- Handles late-arriving and corrected data
- Idempotent and safe to re-run

**Purpose:** Produce clean, correct, trusted data.

---

### Gold Layer
- Reads only from Silver
- Built using **SQL window functions**
- Computes:
  - Daily returns
  - Moving averages (7-day, 30-day)
  - Rolling volatility (30-day)
- Rebuilt using `INSERT OVERWRITE`

**Purpose:** Provide analytics-ready tables for querying and BI.

---

## Key Engineering Concepts Demonstrated

- Medallion (Bronze / Silver / Gold) architecture
- Append-only raw ingestion
- Incremental processing with Delta MERGE
- Window-function-based deduplication
- SQL-first analytics modeling
- Unity Catalog–compatible file handling
- Clear separation of ingestion and processing

---

## Design Decisions & Assumptions

Key assumptions and trade-offs are explicitly documented in:

docs/assumptions.md

This includes:
- Free-tier API limitations
- Limited historical data
- No streaming or ML
- Rebuild strategy for Gold tables
- Databricks Community Edition constraints

---

## How to Run the Project

1. **Run API extraction locally**
python ingestion/alpha_vantage_extractor.py


2. **Upload generated CSV files** to Databricks Volumes:

3. **Run Databricks notebooks in order**
- `01_bronze_ingestion`
- `02_silver_transformations`
- `03_gold_analytics`

---

 

## Future Enhancements 

- Add partitioning and Z-ORDER optimizations
- Introduce streaming ingestion
- Integrate dbt for analytics transformations
- Expand to additional financial datasets

---

 
