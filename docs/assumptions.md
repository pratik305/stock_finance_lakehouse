# Incremental Processing Logic

So this document explains how I handle incremental data processing in the lakehouse. The basic problem is that data comes in multiple times and you need to handle duplicates and updates correctly without breaking anything.

## Why incremental processing matters

The Alpha Vantage API can be called multiple times for the same ticker. Maybe I run the extraction script twice by accident. Maybe the API returns updated values for past dates. Maybe theres a correction.

Bronze layer is append only so everything just gets added. This means the same trading day for the same ticker can show up multiple times in bronze. Thats fine for bronze but downstream layers need to handle it.

Pipelines need to be safe to rerun. If a notebook fails halfway through I should be able to just run it again without corrupting data or creating duplicates.

Late arriving data is also a thing. Sometimes an API might return corrected values for past dates. The pipeline should handle that gracefully.

## How bronze works

Bronze is super simple. Just append everything. No deduplication. No updates. No deletes.

If the same record comes in five times it gets stored five times. Each copy has its own ingestion timestamp so I can tell them apart.

This might seem wasteful but it serves important purposes.

You can audit the full history. See exactly what data came in and when. Debug issues by looking at raw inputs. Reprocess silver if transformation logic changes.

The bronze layer is basically an immutable log of everything that happened. Never lose data. Never overwrite. Just keep appending.

## How silver handles duplicates

Silver is where deduplication happens. The business key for stock data is ticker symbol plus trade date. So AAPL on 2024-01-15 is one unique record.

But bronze might have multiple records for AAPL on 2024-01-15 because I ran the extraction twice or the API sent corrections. Silver needs to pick one.

The rule I use is simple. Keep the record with the latest ingestion timestamp. If theres five copies take the newest one. This handles both duplicates and corrections.

Implementation uses window functions. Partition by ticker and trade date. Order by ingestion timestamp descending. Rank each row. Filter to rank equals one. Now you have deduplicated data.

Then I read the current silver table and merge the new deduplicated data into it.

## MERGE operation explained

Delta MERGE is the key to incremental correctness. The operation looks at business keys and decides what to do.

If a record with that ticker and trade date already exists in silver it updates the existing row with new values. This handles corrections and late arriving data.

If the ticker and trade date combination is new it inserts a new row. This handles genuinely new data.

The beauty of MERGE is its idempotent. Run it once or ten times and you get the same result. If the same data comes in twice the second merge does nothing because the row already matches.

This makes the pipeline really robust. Job fails halfway through. Just rerun it. Same data accidentally processed twice. No problem. Late correction comes in. Gets merged correctly.

## Why silver uses MERGE not overwrite

I could just rebuild silver from bronze every time like I do with gold. Read all of bronze. deduplicate. write to silver. Done.

But that gets expensive as bronze grows. If bronze has millions of records you dont want to reprocess all of them every time.

MERGE lets me process just the new data. Read only the latest batch from bronze. Deduplicate that batch. Merge into silver. Much faster.

Also MERGE preserves existing data that hasnt changed. Only updates what needs updating. This is important if downstream processes are reading from silver while updates happen.

## Gold layer is different

Gold tables are fully derived from silver. They dont have their own incremental logic. Just read all of silver. compute metrics. write to gold.

I use INSERT OVERWRITE which means truncate and rebuild. This seems wasteful but it actually makes sense for analytics tables.

The metrics in gold depend on historical context. Daily returns need previous close prices. Moving averages need windows of past data. Volatility calculations need rolling windows.

Trying to incrementally update these metrics gets complicated fast. You need to track which records changed. Recalculate affected windows. Handle edge cases.

Easier to just rebuild from scratch. The silver table is not that big. Spark can compute all the metrics in seconds. Logic stays simple and correct.

## Business key design

Choosing the right business key is critical. For stock data its obvious. Ticker and trade date uniquely identify a record.

Some datasets have less obvious keys. You need to really understand the data to pick the right deduplication strategy.

Wrong business key means you either keep duplicates you should have removed or you deduplicate records that are actually different.

## Handling schema changes

If the API adds a new field the bronze layer just accepts it because schema enforcement is off. The new field gets stored.

Silver layer needs schema updates if I want to use the new field. Add the column to the schema. Update the merge logic. Reprocess from bronze if needed.

Gold layer only changes if the new field affects analytics. Otherwise it stays the same.

This is why bronze has no schema enforcement. Captures everything even if you dont know what to do with it yet.

## Idempotency in practice

Idempotent means you can run something multiple times and get the same result. This is super important for data pipelines.

Bronze is idempotent because its append only. Run it twice and you just get two copies. Doesnt break anything downstream because silver handles duplicates.

Silver is idempotent because of MERGE. Same data merged twice does nothing the second time.

Gold is idempotent because of INSERT OVERWRITE. Rebuild ten times and you get the same table.

This means I can run the entire pipeline multiple times without worrying. Job scheduling gets easier. Error recovery is simple. Just rerun.

## Late arriving data example

Say I pull data on January 15th. I get prices for January 14th. Process through bronze silver gold. All good.

Then on January 16th the API returns a correction for January 14th. Different close price. Maybe there was a stock split adjustment.

The corrected data lands in bronze with a new ingestion timestamp. Silver deduplication sees two records for the same ticker and date. Picks the one with newer timestamp. Merges the update into silver.

Gold rebuilds from silver and now has the corrected price in all calculations. The old incorrect value is gone from silver but still preserved in bronze for audit purposes.

This whole flow happens automatically because of how the layers are designed.

## What happens if things go wrong

If bronze ingestion fails partway through just rerun it. Append only means partial runs dont corrupt anything.

If silver merge fails check the error. Fix the bug. Rerun. MERGE operation is safe to retry.

If gold rebuild fails same thing. Fix the issue. Rerun INSERT OVERWRITE.

The architecture makes recovery easy because each layer can be rebuilt from the previous one.

## Summary of strategies

Bronze layer. Append everything. No deduplication. No updates. Preserve raw truth. Enable audit and reprocessing.

Silver layer. Incremental MERGE on business keys. Deduplicate using latest timestamp. Handle late data and corrections. Idempotent processing.

Gold layer. Rebuild from silver using INSERT OVERWRITE. Compute metrics with full historical context. Keep logic simple.

Each layer has a clear job. Each layer handles incremental data in the right way for its purpose.