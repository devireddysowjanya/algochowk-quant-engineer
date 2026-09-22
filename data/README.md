# Data

## Primary source
The assignment asks for a credible, documented NIFTY historical source. NSE states that NIFTY 50 historical data is available through its Indices/Statistics historical data service.

Official source:
https://www.nseindia.com/all-reports
https://www.nseindia.com/static/products-services/indices-faqs

## Reproducible mirror used for this run
For computation, the annual OHLC files were retrieved from the public `Hareeshkesavan/Stock-Market-Dataset` GitHub repository, covering 2015–2025. The repository exposes one NIFTY 50 CSV per calendar year with Date/Open/High/Low/Close and additional volume/turnover fields.

Mirror:
https://github.com/Hareeshkesavan/Stock-Market-Dataset

Run:

    python data/download_data.py

The research engine uses only Date, Open, High, Low and Close.

## Coverage
2015-01-01 through 2025-12-31; 2,725 trading-day observations after parsing and de-duplication.

## Cleaning
- Trimmed column names/BOM.
- Parsed dates with day-first format.
- Converted OHLC fields to numeric.
- Removed rows missing required fields.
- Sorted chronologically.
- Removed duplicate dates.
- Validated OHLC relationships.
- No imputation of OHLC values was performed.
- Weekends/market holidays are naturally absent from the trading-day series.

## Important limitation
The annual files are a public mirror, not an official NSE download artifact. The methodology and source hierarchy therefore distinguish the authoritative NSE historical-data service from the mirror used for this reproducible computation. For a production submission, retain the downloaded raw files or replace the downloader with archived NSE files and re-run the same engine.
