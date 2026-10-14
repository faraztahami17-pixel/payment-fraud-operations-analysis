# Data Dictionary

Source: PaySim synthetic mobile-money, PS_20174392719_1491204439457_log.csv (~6,362,620 rows, 11 cols)
| Column | Meaning | Notes |
|---|---|---|
| step | Simulation hour | Not calendar date; use simulation_day = FLOOR((step-1)/24)+1 |
| type | CASH_IN/CASH_OUT/DEBIT/PAYMENT/TRANSFER | Documented 5 categories |
| amount | Local currency (unspecified) | Do not label INR/USD; fraud-labeled value ≠ realized loss |
| nameOrig/nameDest | Account IDs | Merchant IDs start with M; balance unavailable per Kaggle card |
| oldbalanceOrg/newbalanceOrig/oldbalanceDest/newbalanceDest | Balances | Exclude from screening (publisher warning: canceled fraud txs) |
| isFraud | Simulator label | Evaluation ground truth only |
| isFlaggedFraud | Existing control flag | Baseline to evaluate; documented as large-transfer related |

Derived: transaction_id (CSV row number), simulation_day, hour_in_simulated_day ((step-1)%24 relative position), destination_is_merchant, amount_band, evaluation_partition (by whole steps: ~60/20/20).
