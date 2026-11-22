# این فایل شاخص های بازدهی و ریسک را حساب می کند.

import json
import requests
import numpy as np
import pandas as pd


def بازدهی_در_بازه(جدول, تعداد_روز):
    # آخرین NAV و NAV مربوط به ابتدای بازه را پیدا می کنیم
    تاریخ_آخر = جدول["date"].max()
    تاریخ_شروع = تاریخ_آخر - pd.Timedelta(days=تعداد_روز)

    nav_آخر = جدول.iloc[-1]["nav"]
    داده_قدیمی = جدول[جدول["date"] <= تاریخ_شروع]

    if داده_قدیمی.empty:
        return np.nan

    nav_شروع = داده_قدیمی.iloc[-1]["nav"]
    return nav_آخر / nav_شروع - 1


def محاسبه_شاخص_ها(اطلاعات_nav):
    # داده ها را بر اساس کد صندوق جدا می کنیم
    نتیجه = []

    for کد, صندوق in اطلاعات_nav.groupby("scheme_code"):
        صندوق = صندوق.sort_values("date").reset_index(drop=True)

        # بازدهی های روزانه را حساب می کنیم
        بازدهی_روزانه = صندوق["nav"].pct_change().dropna()

        if len(صندوق) < 2:
            continue

        nav = صندوق["nav"]
        بازدهی_سه_ساله = بازدهی_در_بازه(صندوق, 365 * 3)

        # نوسان سالانه از انحراف معیار بازدهی روزانه به دست می آید
        نوسان = بازدهی_روزانه.std() * np.sqrt(252)

        # بیشترین افت سرمایه را حساب می کنیم
        سقف_قبلی = nav.cummax()
        افت = nav / سقف_قبلی - 1
        بیشترین_افت = افت.min()

        # نسبت شارپ با فرض نرخ بدون ریسک صفر
        if نوسان > 0:
            شارپ = (بازدهی_روزانه.mean() * 252) / نوسان
        else:
            شارپ = np.nan

        # نسبت سورتینو فقط نوسان روزهای منفی را در نظر می گیرد
        روزهای_منفی = بازدهی_روزانه[بازدهی_روزانه < 0]
        if len(روزهای_منفی) > 0:
            ریسک_نزولی = np.sqrt((روزهای_منفی ** 2).mean()) * np.sqrt(252)
            سورتینو = (بازدهی_روزانه.mean() * 252) / ریسک_نزولی
        else:
            سورتینو = np.nan

        نتیجه.append({
            "scheme_code": کد,
            "scheme_name": صندوق.iloc[-1]["scheme_name"],
            "return_1w": بازدهی_در_بازه(صندوق, 7),
            "return_1m": بازدهی_در_بازه(صندوق, 30),
            "return_3m": بازدهی_در_بازه(صندوق, 90),
            "return_6m": بازدهی_در_بازه(صندوق, 180),
            "return_1y": بازدهی_در_بازه(صندوق, 365),
            "return_3y": بازدهی_سه_ساله,
            "volatility": نوسان,
            "max_drawdown": بیشترین_افت,
            "sharpe": شارپ,
            "sortino": سورتینو
        })

    return pd.DataFrame(نتیجه, columns=["scheme_code", "scheme_name", "return_1w", "return_1m", "return_3m", "return_6m", "return_1y", "return_3y", "volatility", "max_drawdown", "sharpe", "sortino"])


def دریافت_شاخص_بازار(نام_شاخص, تاریخ_شروع, تاریخ_پایان):
    # ابتدا منبع رسمی Nifty TRI را امتحان می کنیم.
    خطای_منبع_رسمی = None
    try:
        return _دریافت_شاخص_رسمی(نام_شاخص, تاریخ_شروع, تاریخ_پایان)
    except Exception as خطا:
        خطای_منبع_رسمی = str(خطا)

    # اگر سرور ابری به Nifty دسترسی نداشت، از سری تاریخی Yahoo Finance
    # از طریق API عمومی Tigzig استفاده می کنیم.
    نمادها = {
        "NIFTY 50": "^NSEI",
        "NIFTY MIDCAP 150": "^NSMIDCP",
        "NIFTY SMALLCAP 250": "^CRSLDX",
        "NIFTY 500": "^CRSLDX"
    }
    نماد = نمادها.get(نام_شاخص)
    if not نماد:
        raise RuntimeError(
            "برای شاخص " + نام_شاخص + " نماد جایگزین تعریف نشده است. "
            + "خطای منبع رسمی: " + str(خطای_منبع_رسمی)[:250]
        )

    آدرس = "https://yfin-h.tigzig.com/v1/get-adj-close/"
    پارامترها = {
        "tickers": نماد,
        "start_date": pd.Timestamp(تاریخ_شروع).strftime("%Y-%m-%d"),
        "end_date": pd.Timestamp(تاریخ_پایان).strftime("%Y-%m-%d")
    }
    پاسخ = requests.get(
        آدرس,
        params=پارامترها,
        headers={"User-Agent": "Mozilla/5.0"},
        timeout=45
    )
    پاسخ.raise_for_status()

    try:
        داده = پاسخ.json()
    except ValueError:
        raise ValueError(
            "منبع جایگزین به جای JSON پاسخ نامعتبر فرستاد: "
            + پاسخ.text[:180]
        )

    # پاسخ این API به شکل دیکشنری تاریخ -> نماد -> قیمت برمی گردد.
    if isinstance(داده, dict) and "error" in داده:
        raise ValueError("خطای منبع جایگزین: " + str(داده["error"]))

    if isinstance(داده, dict) and "data" in داده:
        داده = داده["data"]

    ردیف_ها = []
    if isinstance(داده, dict):
        for تاریخ, قیمت_ها in داده.items():
            if isinstance(قیمت_ها, dict):
                قیمت = قیمت_ها.get(نماد)
                if قیمت is not None:
                    ردیف_ها.append({"date": تاریخ, "adj_close": قیمت})
            elif isinstance(قیمت_ها, (int, float, str)):
                ردیف_ها.append({"date": تاریخ, "adj_close": قیمت_ها})
    elif isinstance(داده, list):
        ردیف_ها = داده

    if not ردیف_ها:
        raise ValueError(
            "منبع جایگزین برای نماد " + نماد + " داده ای برنگرداند. "
            + "خطای Nifty: " + str(خطای_منبع_رسمی)[:180]
        )

    شاخص = pd.DataFrame(ردیف_ها)
    ستون_تاریخ = next(
        (ستون for ستون in ["date", "Date", "datetime", "timestamp"] if ستون in شاخص.columns),
        None
    )
    ستون_قیمت = next(
        (ستون for ستون in ["adj_close", "Adj Close", "adjclose", "close", "Close"] if ستون in شاخص.columns),
        None
    )
    if ستون_تاریخ is None or ستون_قیمت is None:
        raise ValueError(
            "ساختار داده منبع جایگزین قابل شناسایی نیست. ستون ها: "
            + ", ".join(map(str, شاخص.columns))
        )

    شاخص = شاخص[[ستون_تاریخ, ستون_قیمت]].copy()
    شاخص.columns = ["date", "close"]
    شاخص["date"] = pd.to_datetime(شاخص["date"], errors="coerce", utc=True)
    شاخص["date"] = شاخص["date"].dt.tz_convert(None).dt.normalize()
    شاخص["close"] = pd.to_numeric(شاخص["close"], errors="coerce")
    شاخص = شاخص.dropna().sort_values("date").drop_duplicates("date", keep="last")

    if شاخص.empty:
        raise ValueError("داده های منبع جایگزین پس از پاک سازی خالی شدند.")

    # این داده شاخص قیمتِ بازار است، نه TRI رسمی؛ در داشبورد شفاف اعلام می شود.
    شاخص["source"] = "Tigzig / Yahoo Finance - adjusted close"
    شاخص["benchmark_type"] = "Price Index Proxy (نه TRI رسمی)"
    شاخص["ticker"] = نماد
    return شاخص


def _دریافت_شاخص_رسمی(نام_شاخص, تاریخ_شروع, تاریخ_پایان):
    # اطلاعات رسمی Total Return Index از سایت Nifty
    آدرس = "https://www.niftyindices.com/Backpage.aspx/getTotalReturnIndexString"
    شروع = pd.Timestamp(تاریخ_شروع).strftime("%d-%b-%Y")
    پایان = pd.Timestamp(تاریخ_پایان).strftime("%d-%b-%Y")
    اطلاعات_درخواست = {
        "cinfo": "{'name':'" + نام_شاخص + "','startDate':'" + شروع
        + "','endDate':'" + پایان + "','indexName':'" + نام_شاخص + "'}"
    }
    سربرگ = {
        "Content-Type": "application/json; charset=UTF-8",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": "https://www.niftyindices.com/reports/historical-data",
        "Origin": "https://www.niftyindices.com",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/131.0 Safari/537.36"
    }

    پاسخ = None
    خطاها = []
    try:
        import cloudscraper
        مرورگر = cloudscraper.create_scraper()
        پاسخ = مرورگر.post(
            آدرس, headers=سربرگ, json=اطلاعات_درخواست, timeout=35
        )
        پاسخ.raise_for_status()
    except Exception as خطا:
        خطاها.append(str(خطا))
        try:
            پاسخ = requests.post(
                آدرس, headers=سربرگ, json=اطلاعات_درخواست, timeout=35
            )
            پاسخ.raise_for_status()
        except Exception as خطای_دوم:
            خطاها.append(str(خطای_دوم))
            raise RuntimeError("دریافت TRI رسمی ناموفق بود: " + " | ".join(خطاها))

    try:
        محتوای_پاسخ = پاسخ.json()
        ردیف_ها = محتوای_پاسخ["d"]
        if isinstance(ردیف_ها, str):
            ردیف_ها = json.loads(ردیف_ها)
    except Exception as خطا:
        raise ValueError("پاسخ TRI رسمی قابل خواندن نیست: " + str(خطا))

    شاخص = pd.DataFrame(ردیف_ها)
    ستون_تاریخ = "Date" if "Date" in شاخص.columns else "HistoricalDate"
    if شاخص.empty or ستون_تاریخ not in شاخص.columns or "TotalReturnsIndex" not in شاخص.columns:
        raise ValueError("داده TRI رسمی ساختار مورد انتظار را ندارد.")

    شاخص = شاخص[[ستون_تاریخ, "TotalReturnsIndex"]].copy()
    شاخص.columns = ["date", "close"]
    شاخص["date"] = pd.to_datetime(شاخص["date"], errors="coerce", utc=True)
    شاخص["date"] = شاخص["date"].dt.tz_convert(None).dt.normalize()
    شاخص["close"] = pd.to_numeric(شاخص["close"], errors="coerce")
    شاخص = شاخص.dropna().sort_values("date").drop_duplicates("date", keep="last")
    if شاخص.empty:
        raise ValueError("داده TRI رسمی خالی است.")
    شاخص["source"] = "Nifty Indices - Official TRI"
    شاخص["benchmark_type"] = "Official TRI"
    شاخص["ticker"] = نام_شاخص
    return شاخص

def محاسبه_آلفا_بتا(اطلاعات_nav, اطلاعات_شاخص):
    # تاریخ های صندوق و شاخص را یک شکل می کنیم تا اختلاف ساعت باعث حذف روزهای مشترک نشود
    شاخص = اطلاعات_شاخص[["date", "close"]].copy()
    شاخص["date"] = pd.to_datetime(
        شاخص["date"], errors="coerce"
    ).dt.tz_localize(None).dt.normalize()
    شاخص["close"] = pd.to_numeric(شاخص["close"], errors="coerce")
    شاخص = شاخص.dropna().sort_values("date")
    شاخص = شاخص.drop_duplicates(subset=["date"], keep="last")

    # بازدهی روزانه شاخص بازار
    شاخص["بازدهی_شاخص"] = شاخص["close"].pct_change()

    نتیجه = []
    for کد, صندوق in اطلاعات_nav.groupby("scheme_code"):
        صندوق = صندوق[["date", "nav"]].copy()
        صندوق["date"] = pd.to_datetime(
            صندوق["date"], errors="coerce"
        ).dt.tz_localize(None).dt.normalize()
        صندوق["nav"] = pd.to_numeric(صندوق["nav"], errors="coerce")
        صندوق = صندوق.dropna().sort_values("date")
        صندوق = صندوق.drop_duplicates(subset=["date"], keep="last")
        صندوق["بازدهی_صندوق"] = صندوق["nav"].pct_change()

        # فقط تاریخ هایی را مقایسه می کنیم که هر دو منبع داده دارند
        مشترک = pd.merge(
            صندوق[["date", "بازدهی_صندوق"]],
            شاخص[["date", "بازدهی_شاخص"]],
            on="date",
            how="inner"
        ).dropna()

        آلفا = np.nan
        بتا = np.nan

        # برای محاسبه قابل اتکا حداقل ۳۰ روز مشترک لازم است
        if len(مشترک) >= 30:
            واریانس_شاخص = مشترک["بازدهی_شاخص"].var()
            if pd.notna(واریانس_شاخص) and واریانس_شاخص > 0:
                بتا = (
                    مشترک["بازدهی_صندوق"].cov(مشترک["بازدهی_شاخص"])
                    / واریانس_شاخص
                )

                # نرخ بدون ریسک روزانه در این پروژه صفر فرض شده است
                آلفای_روزانه = (
                    مشترک["بازدهی_صندوق"].mean()
                    - بتا * مشترک["بازدهی_شاخص"].mean()
                )
                آلفا = آلفای_روزانه * 252

        نتیجه.append({
            "scheme_code": str(کد),
            "beta": بتا,
            "alpha": آلفا,
            "common_days": len(مشترک)
        })

    return pd.DataFrame(
        نتیجه,
        columns=["scheme_code", "beta", "alpha", "common_days"]
    )
