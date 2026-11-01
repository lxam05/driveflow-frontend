# CSO / RSA driving test statistics

Source exports used for DriveFlow centre stats (current: September 2026; July 2026 files kept for reference):

- `ROA30-pass-rates-<YYYY-MM>.csv` — Category B pass rate
- `ROA30-abandoned-<YYYY-MM>.csv` — tests not conducted / abandoned
- `ROA36-waiting-times-<YYYY-MM>.csv` — estimated weeks to invite at month end

New months come from the CSO PxStat API (tables ROA30 and ROA36), e.g.
`https://ws.cso.ie/public/api.restful/PxStat.Data.Cube_API.ReadDataset/ROA30/CSV/1.0/en`.
Filter to Category B and the month, keep the same columns, then set `PERIOD` in
`_agent/compile_cso_stats.py`.

Compile into site JSON:

```bash
python3 _agent/compile_cso_stats.py
```

Outputs:

- `data/cso-driving-test-stats-<YYYY-MM>.json`
- `data/centre-stats.json`
