# Power BI — how to open without error

1. Open Power BI Desktop.
2. Get Data -> Text/CSV -> select `data/processed/FactMonitoring.csv` (or Parquet via Python connector).
3. Paste DAX from `measures.dax` into Model -> New Measure.
4. Follow `dashboard_build_guide.md` for 3 pages (screenshots already in `reports/screenshots/`).

The .pbix is not auto-generated here; building it in Desktop is the correct portfolio step. Export your built file to `powerbi/FraudOps.pbix`.

Pre-generated files ready: `FactMonitoring.csv` (83M), `FactMonitoring.parquet` (34M), `review_queue.csv`, `rule_performance.csv`.
