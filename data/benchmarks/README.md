# India benchmark history input

Place a CSV named `index_levels.csv` in this folder with exactly these columns:

```csv
date,benchmark_id,index_value
2024-01-01,NIFTY_500_TRI,12345.67
2024-01-01,NIFTY_BANK_TRI,23456.78
```

Use daily official NSE Indices Total Return Index (TRI) closing levels. Do not paste price-only index closes into a TRI series. Dates must be ISO `YYYY-MM-DD`; values must be positive numeric index levels.

## Benchmark IDs

- `NIFTY_50_TRI`
- `NIFTY_NEXT_50_TRI`
- `NIFTY_MIDCAP_150_TRI`
- `NIFTY_SMALLCAP_250_TRI`
- `NIFTY_500_TRI`
- `NIFTY_BANK_TRI`
- `NIFTY_IT_TRI`
- `NIFTY_PHARMA_TRI`
- `NIFTY_AUTO_TRI`
- `NIFTY_METAL_TRI`
- `NIFTY_FINANCIAL_SERVICES_TRI`
- `NIFTY_REALTY_TRI`
- `NIFTY_FMCG_TRI`
- `NIFTY_MEDIA_TRI`
- `NIFTY_ENERGY_TRI`
- `NIFTY_HEALTHCARE_TRI`

The pipeline computes alpha and beta only when at least 60 fund/benchmark daily return pairs exist. Other categories remain unmapped until a suitable benchmark is added. The scheme's disclosed benchmark should override category inference when available.

Official historical reports: https://www.niftyindices.com/reports
