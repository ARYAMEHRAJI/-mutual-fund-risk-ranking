# پایگاه داده ساده پروژه با SQLite

import sqlite3
from contextlib import contextmanager
import pandas as pd

مسیر_پایگاه = "funds_database.db"


@contextmanager
def اتصال():
    پایگاه = sqlite3.connect(مسیر_پایگاه, timeout=30)
    پایگاه.execute("PRAGMA foreign_keys = ON")
    try:
        yield پایگاه
        پایگاه.commit()
    except Exception:
        پایگاه.rollback()
        raise
    finally:
        پایگاه.close()


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
                return_score REAL,
                risk_score REAL,
                quality_score REAL,
                conservative_score REAL,
                moderate_score REAL,
                growth_score REAL,
                aggressive_score REAL,
                data_coverage REAL,
                UNIQUE (scheme_code, metrics_as_of),
                FOREIGN KEY (scheme_code) REFERENCES funds(scheme_code)
            )
        """)

        # اگر پایگاه قدیمی باشد، ستون‌های جدید را بدون پاک کردن اطلاعات اضافه می‌کنیم.
        ستون_ها = {
            "return_score": "REAL",
            "risk_score": "REAL",
            "quality_score": "REAL",
            "conservative_score": "REAL",
            "moderate_score": "REAL",
            "growth_score": "REAL",
            "aggressive_score": "REAL",
            "data_coverage": "REAL"
        }
        ستون_های_فعلی = {
            ردیف[1] for ردیف in پایگاه.execute("PRAGMA table_info(fund_metrics)").fetchall()
        }

        for نام, نوع in ستون_ها.items():
            if نام not in ستون_های_فعلی:
                پایگاه.execute(
                    "ALTER TABLE fund_metrics ADD COLUMN " + نام + " " + نوع
                )


def ذخیره_نتایج(جدول):
    آماده_سازی()
    if جدول.empty:
        return

    ستون_های_شاخص = [
        "metrics_as_of", "return_1w", "return_1m", "return_3m",
        "return_6m", "return_1y", "return_3y", "volatility",
        "max_drawdown", "sharpe", "sortino", "alpha", "beta",
        "return_score", "risk_score", "quality_score",
        "Conservative_score", "Moderate_score", "Growth_score",
        "Aggressive_score", "data_coverage"
    ]

    with اتصال() as پایگاه:
        for _, ردیف in جدول.iterrows():
            کد = str(ردیف["scheme_code"]).strip().removesuffix(".0")
            نام = str(ردیف.get("scheme_name", "نامشخص"))
            گروه = str(ردیف.get("fund_group", "نامشخص"))

            پایگاه.execute("""
                INSERT INTO funds (scheme_code, scheme_name, fund_group)
                VALUES (?, ?, ?)
                ON CONFLICT(scheme_code) DO UPDATE SET
                    scheme_name = excluded.scheme_name,
                    fund_group = excluded.fund_group
            """, (کد, نام, گروه))

            مقادیر = []
            for ستون in ستون_های_شاخص:
                مقدار = ردیف.get(ستون)
                if pd.isna(مقدار):
                    مقدار = None
                elif ستون == "metrics_as_of":
                    مقدار = str(مقدار)
                else:
                    مقدار = float(مقدار)
                مقادیر.append(مقدار)

            پایگاه.execute("""
                INSERT INTO fund_metrics (
                    scheme_code, metrics_as_of, return_1w, return_1m, return_3m,
                    return_6m, return_1y, return_3y, volatility, max_drawdown,
                    sharpe, sortino, alpha, beta, return_score, risk_score,
                    quality_score, conservative_score, moderate_score,
                    growth_score, aggressive_score, data_coverage
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(scheme_code, metrics_as_of) DO UPDATE SET
                    return_1w=excluded.return_1w,
                    return_1m=excluded.return_1m,
                    return_3m=excluded.return_3m,
                    return_6m=excluded.return_6m,
                    return_1y=excluded.return_1y,
                    return_3y=excluded.return_3y,
                    volatility=excluded.volatility,
                    max_drawdown=excluded.max_drawdown,
                    sharpe=excluded.sharpe,
                    sortino=excluded.sortino,
                    alpha=COALESCE(excluded.alpha, fund_metrics.alpha),
                    beta=COALESCE(excluded.beta, fund_metrics.beta),
                    return_score=excluded.return_score,
                    risk_score=excluded.risk_score,
                    quality_score=excluded.quality_score,
                    conservative_score=excluded.conservative_score,
                    moderate_score=excluded.moderate_score,
                    growth_score=excluded.growth_score,
                    aggressive_score=excluded.aggressive_score,
                    data_coverage=excluded.data_coverage
            """, (کد, *مقادیر))


def آمار_پایگاه_داده():
    آماده_سازی()
    with اتصال() as پایگاه:
        تعداد_صندوق = پایگاه.execute("SELECT COUNT(*) FROM funds").fetchone()[0]
        تعداد_شاخص = پایگاه.execute("SELECT COUNT(*) FROM fund_metrics").fetchone()[0]
    return {"funds": تعداد_صندوق, "metrics": تعداد_شاخص}
