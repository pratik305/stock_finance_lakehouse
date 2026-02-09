# Incremental Processing Logic

This document explains how incremental data processing is handled in the Lakehouse.

---

## Why Incremental Logic Is Required

- Source data can be re-fetched multiple times
- Bronze layer is append-only
- Duplicate and late-arriving records are expected
- Pipelines must be safe to re-run

---

## Bronze Layer Strategy

- Append-only ingestion
- No deduplication
- Raw truth is preserved
- Multiple records for the same business key are allowed

This enables:
- Auditing
- Reprocessing
- Debugging data issues

---

## Silver Layer Strategy (Core Logic)

### Business Key
(ticker, trade_date)

### Deduplication Rule
For the same business key, keep the record with the **latest ingestion timestamp**.

### Implementation
1. Read from Bronze
2. Cast data types
3. Use window functions to rank duplicates
4. Keep the latest record per key
5. MERGE into Silver Delta table

### MERGE Behavior
- WHEN MATCHED → UPDATE existing row
- WHEN NOT MATCHED → INSERT new row

This ensures:
- Idempotency
- Correct handling of late data
- No duplicate business keys

---

## Gold Layer Strategy

- Gold tables are fully derived
- No incremental MERGE
- Tables are rebuilt using INSERT OVERWRITE

This simplifies logic and ensures consistency.

---

## Summary

- Bronze: append-only, no corrections
- Silver: incremental MERGE, correctness enforced
- Gold: deterministic rebuilds for analytics
