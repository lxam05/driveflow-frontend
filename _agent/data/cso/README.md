# CSO / RSA driving test statistics

Source exports used for DriveFlow centre stats (July 2026):

- `ROA30-pass-rates-2026-07.csv` — Category B pass rate
- `ROA30-abandoned-2026-07.csv` — tests not conducted / abandoned
- `ROA36-waiting-times-2026-07.csv` — estimated weeks to invite at month end

Compile into site JSON:

```bash
python3 _agent/compile_cso_stats.py
```

Outputs:

- `data/cso-driving-test-stats-2026-07.json`
- `data/centre-stats.json`
