# Findings -- Payment Fraud and Operational Anomaly Analysis

Partitions dev [1, 446] val [447, 594] test [595, 744]. Total 636,262 transactions, fraud 820 (0.13%), fraud-labeled value 210,714,642 local units (not realized loss). Fraud only in TRANSFER / CASH_OUT -- synthetic limitation.

Existing flag (isFlaggedFraud): near-zero recall in test -- narrow legacy control.

Test, thresholds frozen on dev:
- R1 large-for-type (p99.5): 639 alerts, precision 0.78%, recall 2.82%
- R2 TRANSFER over 200k: 2,279 alerts, precision 2.19%, recall 28.25%
- R3 recipient activity, end-of-hour: 674 alerts, precision 1.93%, recall 7.34%
- Combined OR: 2,954 alerts, precision 1.93%, recall 32.20%, fraud-value recall 52%

Capacity 100/250/500 per simulated day: alerts fit within budget in this sample -- demonstrates daily prioritization (score, amount, id).

Invariants hold: TP+FP+FN+TN = total. Leakage guard: balances excluded per publisher warning.


```
  partition                      rule  alerts  tp   fp    fn       tn  precision   recall      fpr  alert_rate  reviews_per_fraud  fraud_value_recall
development         rule_large_amount    1911  11 1900 452.0 379137.0   0.005756 0.023758 0.004986    0.005009         173.727273            0.090242
development   rule_transfer_threshold    6693 127 6566 336.0 374471.0   0.018975 0.274298 0.017232    0.017544          52.700787            0.409524
development rule_destination_activity    1908  32 1876 431.0 379161.0   0.016771 0.069114 0.004923    0.005001          59.625000            0.208232
development                alert_flag    8696 143 8553 320.0 372484.0   0.016444 0.308855 0.022447    0.022794          60.811189            0.514163
development             existing_flag       3   3    0 460.0 381037.0   1.000000 0.006479 0.000000    0.000008           1.000000            0.009127
 validation         rule_large_amount     628   7  621 173.0 125723.0   0.011146 0.038889 0.004915    0.004963          89.714286            0.171272
 validation   rule_transfer_threshold    2218  53 2165 127.0 124179.0   0.023895 0.294444 0.017136    0.017530          41.849057            0.485268
 validation rule_destination_activity     648  14  634 166.0 125710.0   0.021605 0.077778 0.005018    0.005122          46.285714            0.262120
 validation                alert_flag    2868  57 2811 123.0 123533.0   0.019874 0.316667 0.022249    0.022668          50.315789            0.557559
 validation             existing_flag       0   0    0 180.0 126344.0        NaN 0.000000 0.000000    0.000000                NaN            0.000000
 validation      capacity_100_per_day    2868  57 2811   NaN      NaN   0.019874 0.316667      NaN         NaN                NaN                 NaN
 validation      capacity_250_per_day    2868  57 2811   NaN      NaN   0.019874 0.316667      NaN         NaN                NaN                 NaN
 validation      capacity_500_per_day    2868  57 2811   NaN      NaN   0.019874 0.316667      NaN         NaN                NaN                 NaN
       test         rule_large_amount     639   5  634 172.0 127427.0   0.007825 0.028249 0.004951    0.004983         127.800000            0.118937
       test   rule_transfer_threshold    2279  50 2229 127.0 125832.0   0.021939 0.282486 0.017406    0.017772          45.580000            0.409457
       test rule_destination_activity     674  13  661 164.0 127400.0   0.019288 0.073446 0.005162    0.005256          51.846154            0.229376
       test                alert_flag    2954  57 2897 120.0 125164.0   0.019296 0.322034 0.022622    0.023035          51.824561            0.521301
       test             existing_flag       0   0    0 177.0 128061.0        NaN 0.000000 0.000000    0.000000                NaN            0.000000
       test      capacity_100_per_day    2954  57 2897   NaN      NaN   0.019296 0.322034      NaN         NaN                NaN                 NaN
       test      capacity_250_per_day    2954  57 2897   NaN      NaN   0.019296 0.322034      NaN         NaN                NaN                 NaN
       test      capacity_500_per_day    2954  57 2897   NaN      NaN   0.019296 0.322034      NaN         NaN                NaN                 NaN
```
