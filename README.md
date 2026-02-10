# Stock Finance Analytics Lakehouse

So this is basically a data engineering project I built to practice working with stock market data using Databricks and Delta Lake. The whole thing follows the medallion architecture pattern with bronze silver and gold layers.

## Tools I Used

![Databricks](https://img.shields.io/badge/Databricks-FF3621?style=for-the-badge&logo=databricks&logoColor=white)
![Apache Spark](https://img.shields.io/badge/Apache_Spark-E25A1C?style=for-the-badge&logo=apachespark&logoColor=white)
![Delta Lake](https://img.shields.io/badge/Delta_Lake-00ADD8?style=for-the-badge&logo=delta&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![PySpark](https://img.shields.io/badge/PySpark-E25A1C?style=for-the-badge&logo=apachespark&logoColor=white)
 

## What it does

The project pulls daily stock prices from Alpha Vantage API and processes them through different layers. Each layer has a specific job. Bronze just stores raw data. Silver cleans it up and removes duplicates. Gold layer creates analytics ready metrics like moving averages and volatility.

I wanted to show how incremental processing works in a real lakehouse setup. So the pipeline can handle new data coming in without reprocessing everything from scratch.

## How it works

```
Alpha Vantage API
    ↓
CSV files saved locally
    ↓
Bronze Delta Table
    ↓  
Silver Delta Table 
    ↓
Gold Delta Table
```

Pretty straightforward flow. Extract data locally then load it into databricks and process through the layers.

## Project folders

```
stock-finance-lakehouse/
│
├── ingestion/
│   └── alpha_vantage_extractor.py
│
├── databricks/
│   ├── 01_bronze_ingestion.py
│   ├── 02_silver_transformations.py
│   └── 03_gold_analytics.sql
│
├── docs/
│   ├── architecture.md
│   ├── data_model.md
│   └── assumptions.md
│
└── README.md
```

## Data source stuff

Using Alpha Vantage free tier which gives you daily OHLCV data. Open high low close volume for each trading day. The free tier only provides around 100 days of recent data per ticker but thats enough for this project.

I extract the data locally first because the API has rate limits and I didnt want to deal with that inside Spark jobs. Just run the python script. save CSVs. then upload to databricks.

## Bronze layer

This is where raw data lives. Its append only so I never delete anything. Just keep adding new data as it comes in. No transformations here. No deduplication. Just pure raw data exactly as received.

The table includes some metadata like ingestion timestamp so I can track when data was loaded. This layer is basically the source of truth. If anything goes wrong downstream I can always reprocess from bronze.

Schema enforcement is disabled here intentionally. I want to capture whatever comes from the API.

## Silver layer  

This is where the cleaning happens. Read from bronze. enforce proper schema. deduplicate records. The deduplication uses window functions to keep only the latest record for each ticker and date combination.

The key thing here is using Delta MERGE instead of just insert. So if the same data comes in twice it handles it correctly. If theres a late arriving correction it updates the existing record. The merge happens on ticker and trade date.

This layer is idempotent which means you can run it multiple times and get the same result. Really important for data quality.

## Gold layer

Analytics ready tables. Built entirely with SQL because analytical queries are easier to read in SQL than PySpark.

I compute things like.
- Daily returns
- 7 day moving average  
- 30 day moving average
- 30 day rolling volatility

All using window functions. The gold tables get rebuilt using INSERT OVERWRITE each time. Not incremental here because the calculations depend on historical data and its simpler to just rebuild.

## Running the pipeline

First run the API extractor locally.

```bash
python ingestion/alpha_vantage_extractor.py
```

This generates CSV files in your local directory.

Then upload those CSVs to Databricks Volumes. I put them in /Volumes/main/default/stock_data/landing.

After that run the notebooks in order.
1. 01_bronze_ingestion
2. 02_silver_transformations  
3. 03_gold_analytics

Each notebook is self contained and has comments explaining what its doing.

## Some limitations

Im using Databricks Community Edition which is free but has some restrictions. No jobs scheduling. No clusters running 24/7. But its perfect for learning and building portfolio projects.

The Alpha Vantage free tier only gives 100 days of data. If you want more historical data you need a paid plan. For this demo 100 days is fine.

No real time streaming here. Everything is batch processing. I might add streaming later but wanted to get the basics solid first.

## Design decisions I made

I chose to do API extraction locally instead of in databricks because.
- Rate limits are easier to handle outside spark
- Can retry failed requests manually
- Dont waste cluster time waiting for API responses

Bronze layer is append only because.
- Preserves raw history
- Enables reprocessing if transformations change
- Acts as audit trail

Silver uses MERGE not INSERT because.
- Handles duplicates gracefully  
- Supports late arriving data
- Provides idempotency

Gold uses INSERT OVERWRITE because.
- Metrics depend on full history
- Simpler than tracking incremental changes
- Queries are fast enough to rebuild

## What I learned

Delta Lake MERGE operations are really powerful for incremental processing. Window functions in Spark SQL work great for deduplication and analytics. The medallion architecture makes sense once you actually build it.

Also learned that data quality issues show up fast. Missing dates. duplicate records. schema changes. All that stuff needs handling.

## Future ideas

Maybe add.
- Partitioning by year and month
- Z-ORDER optimization  
- More tickers
- Streaming ingestion with Auto Loader
- dbt for transformations
- Some basic ML models

But for now keeping it simple and focused on core lakehouse patterns.

## Notes

The docs folder has more detailed explanations of the architecture and data model. Check [assumptions.md](docs/assumptions.md) for all the trade offs and decisions.

 