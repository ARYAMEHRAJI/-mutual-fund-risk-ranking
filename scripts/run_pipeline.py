"""Run the complete data and ranking pipeline."""
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from fundrank.pipeline import run_pipeline

if __name__ == "__main__":
    result = run_pipeline()
    print(f"Pipeline complete: {len(result):,} funds")
    print(f"Latest NAV date: {result['last_date'].max()}")
