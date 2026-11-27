# پایگاه داده ساده پروژه با SQLite
# SQLite نیاز به نصب سرور جداگانه ندارد.

import sqlite3
import pandas as pd

مسیر_پایگاه = "funds_database.db"


def اتصال():
    return sqlite3.connect(مسیر_پایگاه)


def آماده_سازی():
    with اتصال() as پایگاه:
        پایگاه.execute("""
            CREATE TABLE IF NOT EXISTS funds (
                scheme_code TEXT PRIMARY KEY,
                scheme_name TEXT NOT NULL,
                fund_group TEXT NOT NULL
            )
        """)
        پایگاه.execute("""
            CREATE TABLE IF NOT EXISTS fund_metrics (
                metric_id INTEGER PRIMARY KEY AUTOINCREMENT,
                scheme_code TEXT NOT NULL,
                metrics_as_of TEXT NOT NULL,
                return_1w REAL,
                return_1m REAL,
                return_3m REAL,
                return_6m REAL,
                return_1y REAL,
                return_3y REAL,
                volatility REAL,
                max_drawdown REAL,
                sharpe REAL,
                sortino REAL,
                alpha REAL,
                beta REAL,
                UNIQUE (scheme_code, metrics_as_of),
                FOREIGN KEY (scheme_code) REFERENCES funds(scheme_code)
            )
        """)


def ذخیره_نتایج(جدول):
    آماده_سازی()
    with اتصال() as پایگاه:
        for _, ردیف in جدول.iterrows():
            کد = str(ردیف["scheme_code"])
            پایگاه.execute(
                "INSERT OR REPLACE INTO funds (scheme_code, scheme_name, fund_group) VALUES (?, ?, ?)",
                (کد, str(ردیف.get("scheme_name", "")), str(ردیف.get("fund_group", "نامشخص")))
            )
            مقادیر = []
            for ستون in [
                "metrics_as_of", "return_1w", "return_1m", "return_3m",
                "return_6m", "return_1y", "return_3y", "volatility",
                "max_drawdown", "sharpe", "sortino", "alpha", "beta"
            ]:
                مقدار = ردیف.get(ستون)
                if pd.isna(مقدار):
                    مقدار = None
                elif ستون == "metrics_as_of":
                    مقدار = str(مقدار)
                else:
                    مقدار = float(مقدار)
                مقادیر.append(مقدار)
            پایگاه.execute("""
                INSERT OR REPLACE INTO fund_metrics (
                    scheme_code, metrics_as_of, return_1w, return_1m, return_3m,
                    return_6m, return_1y, return_3y, volatility, max_drawdown,
                    sharpe, sortino, alpha, beta
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (کد, *مقادیر))


def آمار_پایگاه_داده():
    آماده_سازی()
    with اتصال() as پایگاه:
        تعداد_صندوق = پایگاه.execute("SELECT COUNT(*) FROM funds").fetchone()[0]
        تعداد_شاخص = پایگاه.execute("SELECT COUNT(*) FROM fund_metrics").fetchone()[0]
    return {"funds": تعداد_صندوق, "metrics": تعداد_شاخص}
