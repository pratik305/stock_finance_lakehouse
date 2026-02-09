# Databricks notebook source
from pyspark.sql import functions as F
from pyspark.sql.window import Window

# COMMAND ----------

df_bronze = spark.table("stock_lakehouse.bronze_stock_prices") # Loads Bronze Delta table into Spark DataFrame

# COMMAND ----------

# MAGIC %md
# MAGIC Converts raw strings into correct business types
# MAGIC
# MAGIC Renames columns to analytics-friendly names

# COMMAND ----------

df_casted = (
    df_bronze
    .withColumn("trade_date", F.to_date("trade_date"))
    .withColumn("open_price", F.col("open").cast("decimal(18,4)"))
    .withColumn("high_price", F.col("high").cast("decimal(18,4)"))
    .withColumn("low_price", F.col("low").cast("decimal(18,4)"))
    .withColumn("close_price", F.col("close").cast("decimal(18,4)"))
    .withColumn("volume", F.col("volume").cast("bigint"))
    .select(
        "ticker",
        "trade_date",
        "open_price",
        "high_price",
        "low_price",
        "close_price",
        "volume",
        "ingestion_ts"
    )
)


# COMMAND ----------

# MAGIC %md
# MAGIC Groups rows by business key (ticker, trade_date)
# MAGIC
# MAGIC Orders duplicates so latest ingested record comes first

# COMMAND ----------

window_spec = Window.partitionBy(
    "ticker","trade_date"
).orderBy(
    F.col("ingestion_ts").desc()
)

# COMMAND ----------

# MAGIC %md
# MAGIC Assigns row numbers within each group
# MAGIC
# MAGIC Keeps only the latest record
# MAGIC
# MAGIC Removes helper columns

# COMMAND ----------

df_deduped = (
    df_casted
    .withColumn("row_num", F.row_number().over(window_spec))
    .filter(F.col("row_num") == 1)
    .drop("row_num", "ingestion_ts")
)


# COMMAND ----------

# MAGIC %md
# MAGIC Defines Silver Delta table schema explicitly

# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE TABLE IF NOT EXISTS stock_lakehouse.silver_stock_prices (
# MAGIC   ticker STRING,
# MAGIC   trade_date DATE,
# MAGIC   open_price DECIMAL(18,4),
# MAGIC   high_price DECIMAL(18,4),
# MAGIC   low_price DECIMAL(18,4),
# MAGIC   close_price DECIMAL(18,4),
# MAGIC   volume BIGINT
# MAGIC )
# MAGIC USING DELTA;
# MAGIC

# COMMAND ----------

# MAGIC %md
# MAGIC Makes Spark DataFrame accessible in SQL
# MAGIC
# MAGIC Required for SQL-based MERGE

# COMMAND ----------

df_deduped.createOrReplaceTempView("silver_updates")


# COMMAND ----------

# MAGIC %md
# MAGIC Merge With business logic to if new entry identify we insert if not we update existing rows with latest values this will 
# MAGIC handle late arriving data or correcte data.
# MAGIC This prevent dupication of data 

# COMMAND ----------

# MAGIC %sql
# MAGIC MERGE INTO stock_lakehouse.silver_stock_prices AS target
# MAGIC USING silver_updates AS source
# MAGIC ON target.ticker = source.ticker
# MAGIC AND target.trade_date = source.trade_date
# MAGIC
# MAGIC WHEN MATCHED THEN UPDATE SET
# MAGIC   target.open_price  = source.open_price,
# MAGIC   target.high_price  = source.high_price,
# MAGIC   target.low_price   = source.low_price,
# MAGIC   target.close_price = source.close_price,
# MAGIC   target.volume      = source.volume
# MAGIC
# MAGIC WHEN NOT MATCHED THEN INSERT (
# MAGIC   ticker,
# MAGIC   trade_date,
# MAGIC   open_price,
# MAGIC   high_price,
# MAGIC   low_price,
# MAGIC   close_price,
# MAGIC   volume
# MAGIC )
# MAGIC VALUES (
# MAGIC   source.ticker,
# MAGIC   source.trade_date,
# MAGIC   source.open_price,
# MAGIC   source.high_price,
# MAGIC   source.low_price,
# MAGIC   source.close_price,
# MAGIC   source.volume
# MAGIC );
# MAGIC

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC   ticker,
# MAGIC   COUNT(*) AS rows_per_ticker,
# MAGIC   MIN(trade_date) AS start_date,
# MAGIC   MAX(trade_date) AS end_date
# MAGIC FROM stock_lakehouse.silver_stock_prices
# MAGIC GROUP BY ticker;
# MAGIC

# COMMAND ----------

# MAGIC %md
# MAGIC The Silver layer reads from Bronze, enforces schema, deduplicates using window functions based on ingestion timestamps, and incrementally merges clean records into a Delta table using (ticker, trade_date) as the business key. This design is idempotent, handles late-arriving data, and produces analytics-ready data.

# COMMAND ----------

