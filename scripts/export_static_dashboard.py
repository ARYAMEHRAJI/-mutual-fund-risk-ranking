"""Export processed pipeline outputs for the static HTML dashboard."""
from pathlib import Path
import json
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
OUT = ROOT / "site" / "data"
NAV_DIR = OUT / "nav"
NAV_DIR.mkdir(parents=True, exist_ok=True)

rank_path = PROCESSED / "fund_rankings.parquet"
nav_path = PROCESSED / "nav_clean.parquet"
if not rank_path.exists() or not nav_path.exists():
    raise FileNotFoundError("Run scripts/run_pipeline.py before exporting the dashboard.")

df = pd.read_parquet(rank_path)
vol = pd.to_numeric(df["volatility"], errors="coerce").rank(pct=True) * 100
dd = pd.to_numeric(df["max_drawdown"], errors="coerce").abs().rank(pct=True) * 100
df["risk_score"] = pd.concat([vol, dd], axis=1).mean(axis=1)
df["scheme_code"] = df["scheme_code"].astype(str)
df = df.replace({float("inf"): None, float("-inf"): None})
(OUT / "fund_rankings.json").write_text(
    df.to_json(orient="records", force_ascii=False), encoding="utf-8"
)

for filename in ["ranking_evaluation.csv", "out_of_sample_evaluation.csv", "weight_sensitivity.csv"]:
    source = PROCESSED / filename
    if source.exists():
        table = pd.read_csv(source)
        table = table.replace({float("inf"): None, float("-inf"): None})
        target = OUT / filename.replace(".csv", ".json")
        target.write_text(table.to_json(orient="records", force_ascii=False), encoding="utf-8")

nav = pd.read_parquet(nav_path)
nav["scheme_code"] = nav["scheme_code"].astype(str)
nav["date"] = pd.to_datetime(nav["date"], errors="coerce").dt.strftime("%Y-%m-%d")
nav["nav_clean"] = pd.to_numeric(nav["nav_clean"], errors="coerce")
nav = nav.dropna(subset=["date", "nav_clean"])
for code, group in nav.groupby("scheme_code", sort=False):
    records = group.sort_values("date")[["date", "nav_clean"]].to_dict(orient="records")
    (NAV_DIR / f"{code}.json").write_text(
        json.dumps(records, separators=(",", ":"), ensure_ascii=False), encoding="utf-8"
    )

info = {
    "fund_count": int(len(df)),
    "last_nav_date": str(pd.to_datetime(df["last_date"]).max().date()),
    "generated_at_utc": pd.Timestamp.now(tz="UTC").isoformat(),
    "nav_funds": int(nav["scheme_code"].nunique()),
}
(OUT / "meta.json").write_text(json.dumps(info, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"Static dashboard data exported: {len(df):,} funds; {info['nav_funds']:,} NAV histories.")
