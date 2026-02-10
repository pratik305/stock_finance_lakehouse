# Architecture Overview

So this project uses the lakehouse architecture pattern with Databricks and Delta Lake. The whole idea is to process stock market data through different layers where each layer has a specific job.

I followed the medallion architecture because it makes sense for separating raw data from cleaned data from analytics ready data. Also makes debugging easier when you know which layer has issues.

## How data flows

```
Alpha Vantage API
    ↓
Extract locally and save as CSV
    ↓
Bronze Delta Table (raw everything)
    ↓
Silver Delta Table (cleaned and deduplicated)
    ↓
Gold Delta Table (analytics metrics)
```

Pretty simple flow. Data comes in at the top and gets refined as it moves down through the layers.

## Bronze Layer

This is where I dump all the raw data. Think of it as the source of truth. Whatever comes from the API goes straight into bronze with no changes.

I made it append only which means nothing ever gets deleted or updated here. Just keep adding new data. This is really important because if I mess up transformations in silver or gold I can always reprocess from bronze.

No schema enforcement at this layer. No deduplication. Just raw data plus some metadata like when it was ingested and where it came from.

The whole point is to preserve everything exactly as received. Even if the data has issues or duplicates. Deal with that stuff later in silver.

## Silver Layer

This is the cleaning layer. Read from bronze. apply schema. remove duplicates. fix data types. All that stuff.

The key design decision here was using Delta MERGE instead of simple inserts. So if the same record comes in twice the merge operation handles it correctly based on business keys. For stock data thats ticker symbol and trade date.

Window functions handle the deduplication. If theres multiple records for the same ticker and date I keep the one with the latest ingestion timestamp. This handles late arriving data and corrections from the API.

The silver layer is idempotent. Run it ten times and you get the same result. This makes the pipeline really reliable. No weird bugs from accidentally running jobs twice.

Schema is enforced here. Dates are actual date types. Prices are decimals. Volume is integer. Everything has the right type.

## Gold Layer

Analytics ready tables live here. This layer is built entirely with SQL because analytical queries are way easier to read in SQL than pyspark code.

I compute business metrics like daily returns. moving averages. volatility measures. All using window functions and aggregations.

The write strategy is different from silver. Instead of incremental merge I just rebuild the whole table each time using INSERT OVERWRITE. This works because.
- The calculations need historical context anyway
- Silver table is not that huge
- Query performance is fast enough
- Simpler logic than tracking incremental changes

Gold tables have stable schemas because downstream users depend on them. BI tools. analysts. maybe ML models later. So I dont change gold schemas without good reason.

## Why I built it this way

Separation of concerns is the big one. Ingestion happens outside databricks. Bronze just stores. Silver cleans. Gold analyzes. Each layer does one thing.

Making pipelines idempotent and rerunnable saves so much debugging time. You can run jobs multiple times without worrying about corrupting data.

Append only raw data means I never lose information. Even bad data gets preserved in bronze. Then I can figure out what went wrong and fix the transformations.

Delta MERGE gives me incremental correctness. New data gets added. Updated data gets merged. Late data gets handled. All automatically.

SQL for analytics makes the code readable. Anyone who knows SQL can understand what the gold layer is doing. No need to decode complex pyspark transformations.

## Why Databricks and Delta Lake

I picked Databricks because its basically the standard for lakehouse architectures. The community edition is free which is perfect for learning.

Delta Lake gives me ACID transactions on top of object storage. So I get database guarantees without running an actual database. Updates and deletes work correctly. No corrupt files from failed jobs.

The MERGE operation is native in delta which makes incremental processing really clean. In regular parquet you would have to read everything. deduplicate in memory. write back. Delta handles it efficiently.

Time travel is built in. If I accidentally corrupt a table I can just roll back to a previous version. Super useful during development.

Spark scales horizontally. Right now the data is small but if I wanted to process millions of tickers the same code would work. Just add more nodes.

Unity Catalog integration makes file management easier. Volumes give me a clean way to handle CSV uploads without messing with cloud storage permissions.

## Trade offs I made

Local extraction instead of databricks based extraction. This adds a manual step but avoids dealing with API rate limits in spark jobs. For a portfolio project thats fine.

Rebuilding gold tables instead of incremental updates. Simpler logic. Faster development. Performance is acceptable for current data size. If gold tables get huge I might change this.

No partitioning yet. Delta tables work fine without partitioning at small scale. Adding partitions later is easy if query performance becomes an issue.

Community edition means no job scheduling. Have to run notebooks manually. But for demonstrating the architecture patterns thats okay.

## What this architecture enables

Reliable incremental processing. New data gets merged correctly without reprocessing everything.

Data quality at each layer. Bronze has raw truth. Silver has clean data. Gold has trusted metrics.

Easy debugging. If something looks wrong in gold check silver. If silver looks wrong check bronze. If bronze looks wrong check the extraction.

Audit trail. Every record has ingestion metadata. Delta has version history. Can trace any data point back to source.

Flexibility to reprocess. Change transformation logic. Truncate silver. Rerun from bronze. Done.

SQL based analytics. Analysts can write queries against gold tables without learning pyspark.

Foundation for future work. Streaming. ML. More complex transformations. The architecture supports all that.