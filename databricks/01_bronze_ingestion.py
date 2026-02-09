# Databricks notebook source
# MAGIC %md
# MAGIC # BRONZE INGESTION NOTEBOOK
# MAGIC ## Purpose:
# MAGIC #### - Read raw CSV files uploaded to Databricks Volumes
# MAGIC #### - Add ingestion metadata
# MAGIC #### - Write append-only Bronze Delta table

# COMMAND ----------

from pyspark.sql import functions as F

# COMMAND ----------

# files path
raw_path = "/Volumes/workspace/default/stock/*.csv"

# COMMAND ----------

df_raw = (
    spark.read
         .option("header", "true")
         .csv(raw_path)
)


# COMMAND ----------

# - input_file_name() is NOT supported in Unity Catalog
# - Use _metadata.file_path instead
# - Example file name: AAPL_daily.csv

df_with_ticker = (
    df_raw
    .withColumn(
        "ticker",
        F.regexp_extract(
            F.col("_metadata.file_path"),
            r"([^/]+)_daily.csv",
            1
        )
    )
)

# COMMAND ----------

# - ingestion_ts: when the record was ingested
# - source: data provider name
df_bronze = (
    df_with_ticker
    .withColumn("ingestion_ts", F.current_timestamp())
    .withColumn("source", F.lit("alpha_vantage"))
)

# COMMAND ----------

# - Logical container for Bronze/Silver/Gold tables
spark.sql("CREATE DATABASE IF NOT EXISTS stock_lakehouse")

# COMMAND ----------

# - Append-only (no overwrite)
# - Raw truth is preserved
# - Duplicates are allowed
(
    df_bronze
    .write
    .format("delta")
    .mode("append")
    .saveAsTable("stock_lakehouse.bronze_stock_prices")
)

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC   ticker,
# MAGIC   COUNT(*) AS rows_per_ticker
# MAGIC FROM stock_lakehouse.bronze_stock_prices
# MAGIC GROUP BY ticker;
# MAGIC

# COMMAND ----------

# MAGIC %md
# MAGIC This notebook ingests raw CSV stock data from Unity Catalog Volumes into an append-only Bronze Delta table, adds ingestion metadata, and preserves raw truth for downstream processing.

# COMMAND ----------

