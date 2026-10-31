"""Central configuration for the ranking model."""
import os
TRADING_DAYS = int(os.getenv("TRADING_DAYS", "252"))
RISK_FREE_RATE = float(os.getenv("RISK_FREE_RATE", "0.0"))
MIN_HISTORY_YEARS = int(os.getenv("MIN_HISTORY_YEARS", "3"))
API_BASE_URL = os.getenv("TIGZIG_BASE_URL", "https://api.tigzig.com/mf/v1")
API_TIMEOUT = int(os.getenv("TIGZIG_TIMEOUT", "60"))
API_BATCH_SIZE = min(50, max(1, int(os.getenv("TIGZIG_BATCH_SIZE", "50"))))
API_REQUEST_DELAY = float(os.getenv("TIGZIG_REQUEST_DELAY", "21"))
METRICS = ["return_1m", "return_3m", "return_6m", "return_12m", "volatility", "max_drawdown", "sharpe_ratio", "sortino_ratio"]
PROFILE_WEIGHTS = {
 "Conservative": {"return_1m":5,"return_3m":5,"return_6m":10,"return_12m":10,"volatility":20,"max_drawdown":25,"sharpe_ratio":10,"sortino_ratio":15},
 "Moderate": {"return_1m":5,"return_3m":10,"return_6m":15,"return_12m":20,"volatility":15,"max_drawdown":15,"sharpe_ratio":10,"sortino_ratio":10},
 "Growth": {"return_1m":7.5,"return_3m":12.5,"return_6m":17.5,"return_12m":22.5,"volatility":12.5,"max_drawdown":10,"sharpe_ratio":8.5,"sortino_ratio":9},
 "Aggressive": {"return_1m":10,"return_3m":15,"return_6m":20,"return_12m":25,"volatility":10,"max_drawdown":5,"sharpe_ratio":7.5,"sortino_ratio":7.5}}
METRIC_HIGHER_IS_BETTER = {"return_1m":True,"return_3m":True,"return_6m":True,"return_12m":True,"volatility":False,"max_drawdown":True,"sharpe_ratio":True,"sortino_ratio":True}
RISK_QUESTION_WEIGHTS = [3,3,2,1,2,2,1,1,2,2]
RISK_PROFILE_BANDS = [(0,30,"Conservative"),(30,60,"Moderate"),(60,80,"Growth"),(80,100,"Aggressive")]
