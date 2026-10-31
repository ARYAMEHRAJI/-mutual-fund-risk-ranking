# Research notebook migration notes

The implementation preserves the latest agreed research decisions and makes them reproducible as Python modules.

| Notebook work | New implementation |
|---|---|
| Latest scheme metadata and eligibility filters | src/fundrank/data.py |
| Batched historical NAV download | src/fundrank/data.py |
| NAV quality checks and correction experiments | src/fundrank/cleaning.py |
| Period returns, volatility, drawdown, Sharpe, Sortino | src/fundrank/metrics.py |
| Category peer groups and percentile scores | src/fundrank/scoring.py |
| Four profile weight dictionaries and coverage | src/fundrank/config.py and scoring.py |
| Ten-answer risk score | src/fundrank/questionnaire.py |
| Composite rankings | src/fundrank/scoring.py |
| Model comparison and weight sensitivity | src/fundrank/evaluation.py |

## Important differences and audit decisions

1. The notebook has multiple NAV correction experiments and conflicting hard-coded correction dates. These dates were not copied as unquestioned truth. The new cleaner uses explicit time-series evidence and writes every correction to a reviewable audit file.
2. The final executed notebook reconstruction uses a zero risk-free rate for Sharpe. That remains the default and is configurable.
3. The final notebook Sortino attempt calculates standard deviation after clipping positive returns to zero. The new implementation instead uses target-zero downside RMS, the conventional downside-deviation denominator.
4. The notebook's interim questionnaire calculation divides the weighted sum by two. The new implementation normalises by the maximum possible weighted sum, producing a 0-100 score.
5. The four profile weights are preserved exactly from the latest model design. Each profile is expected to total 100.
6. The notebook's broad Equity and Debt peer pools can mix unlike strategies. The new implementation uses provider subcategories when at least five peers are present, otherwise falling back to the parent category group.

The original notebook should be attached to this folder before final submission so the exploratory work and production implementation remain traceable.
