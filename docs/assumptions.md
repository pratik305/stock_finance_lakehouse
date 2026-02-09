# Assumptions & Design Decisions

This document lists the explicit assumptions made while building the project.

---

## Data Source Assumptions

- Data is sourced from Alpha Vantage (free tier)
- Only ~100 recent trading days are available per ticker
- Adjusted prices are not used
- API extraction is performed locally

---

## Scope Assumptions

- Project focuses on Data Engineer / Analytics Engineer roles
- No real-time streaming is implemented
- No machine learning models are included
- No dashboards are built

---

## Technical Assumptions

- Databricks Community Edition is used
- Unity Catalog Volumes are used for raw file storage
- input_file_name() is not available; _metadata.file_path is used
- Small number of tickers (5–10)

---

## Design Trade-offs

- Full history ingestion is skipped due to API limits
- Gold tables are rebuilt instead of incrementally merged
- Performance optimizations are minimal and intentional

---

## Why These Assumptions Are Acceptable

- Architecture scales independently of data volume
- Incremental logic remains valid with larger datasets
- Design mirrors real-world lakehouse patterns
- Focus remains on correctness and clarity
