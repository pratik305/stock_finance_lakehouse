-- Databricks notebook source
CREATE TABLE IF NOT EXISTS stock_lakehouse.gold_stock_daily_metrics (
  ticker STRING,
  trade_date DATE,
  daily_return_pct DECIMAL(10,4),
  ma_7 DECIMAL(18,4),
  ma_30 DECIMAL(18,4),
  volatility_30d DECIMAL(18,6)
)
USING DELTA;


-- COMMAND ----------

INSERT OVERWRITE TABLE stock_lakehouse.gold_stock_daily_metrics
WITH base_prices AS (
  SELECT
    ticker,
    trade_date,
    close_price,
    LAG(close_price) OVER (
      PARTITION BY ticker
      ORDER BY trade_date
    ) AS prev_close
  FROM stock_lakehouse.silver_stock_prices
), 
metrics AS (
  SELECT
    ticker,
    trade_date,
    -- Daily return % logic: ((Current - Previous) / Previous) * 100
    ((close_price - prev_close) / prev_close) * 100 AS daily_return_pct,

    -- 7-day moving average
    AVG(close_price) OVER (
      PARTITION BY ticker
      ORDER BY trade_date
      ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ) AS ma_7,

    -- 30-day moving average
    AVG(close_price) OVER (
      PARTITION BY ticker
      ORDER BY trade_date
      ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
    ) AS ma_30,

    -- 30-day rolling volatility (Standard Deviation)
    STDDEV(close_price) OVER (
      PARTITION BY ticker
      ORDER BY trade_date
      ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
    ) AS volatility_30d
  FROM base_prices
)
SELECT
  ticker,
  trade_date,
  daily_return_pct,
  ma_7,
  ma_30,
  volatility_30d
FROM metrics;

-- COMMAND ----------

SELECT *
FROM stock_lakehouse.gold_stock_daily_metrics
ORDER BY ticker, trade_date
LIMIT 20;


-- COMMAND ----------

-- MAGIC %md
-- MAGIC Gold tables are built using SQL window functions on Silver data, producing analytics-ready metrics like returns, moving averages, and volatility. These tables are rebuilt deterministically and optimized for consumption

-- COMMAND ----------

