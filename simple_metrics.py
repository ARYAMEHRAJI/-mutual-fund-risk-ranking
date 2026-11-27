# محاسبه بازدهی و ریسک صندوق‌ها از روی تاریخچه NAV

import requests
import numpy as np
import time
import pandas as pd
from concurrent.futures import ThreadPoolExecutor


def بازدهی_در_بازه(جدول, تعداد_روز, تاریخ_پایان_مشترک, حداکثر_فاصله):
    تاریخ_شروع_هدف = تاریخ_پایان_مشترک - pd.Timedelta(days=تعداد_روز)

    داده_پایان = جدول[جدول["date"] <= تاریخ_پایان_مشترک]
    داده_شروع = جدول[جدول["date"] <= تاریخ_شروع_هدف]

    if داده_شروع.empty or داده_پایان.empty:
        return np.nan

    ردیف_شروع = داده_شروع.iloc[-1]
    ردیف_پایان = داده_پایان.iloc[-1]

    # اگر NAV خیلی از تاریخ هدف دور باشد، بازدهی را محاسبه نمی‌کنیم.
    فاصله_شروع = (تاریخ_شروع_هدف - ردیف_شروع["date"]).days
    فاصله_پایان = (تاریخ_پایان_مشترک - ردیف_پایان["date"]).days

    if فاصله_شروع > حداکثر_فاصله or فاصله_پایان > 7:
        return np.nan

    nav_شروع = ردیف_شروع["nav"]
    nav_پایان = ردیف_پایان["nav"]

    if nav_شروع <= 0 or nav_پایان <= 0:
        return np.nan

    return nav_پایان / nav_شروع - 1


def محاسبه_شاخص_ها(اطلاعات_nav):
    داده = اطلاعات_nav.copy()
    داده["date"] = pd.to_datetime(داده["date"], errors="coerce")
    داده["nav"] = pd.to_numeric(داده["nav"], errors="coerce")
    داده = داده.dropna(subset=["date", "nav"])
    داده = داده[داده["nav"] > 0]

    if داده.empty:
        return pd.DataFrame()

    تاریخ_پایان_مشترک = داده["date"].max()
    تاریخ_شروع_سه_ساله = تاریخ_پایان_مشترک - pd.DateOffset(years=3)
    نتیجه = []

    for کد, صندوق_کامل in داده.groupby("scheme_code"):
        صندوق_کامل = صندوق_کامل.sort_values("date").drop_duplicates("date").reset_index(drop=True)

        if len(صندوق_کامل) < 30:
            continue

        # صندوق باید NAV به‌روز داشته باشد.
        if (تاریخ_پایان_مشترک - صندوق_کامل.iloc[-1]["date"]).days > 7:
            continue

        # برای شاخص‌های ریسک فقط سه سال اخیر را استفاده می‌کنیم.
        صندوق = صندوق_کامل[
            صندوق_کامل["date"] >= تاریخ_شروع_سه_ساله
        ].copy().reset_index(drop=True)

        if len(صندوق) < 200:
            continue

        بازدهی_روزانه = صندوق["nav"].pct_change().dropna()
        if len(بازدهی_روزانه) < 150:
            continue

        بازدهی_سه_ساله = بازدهی_در_بازه(
            صندوق_کامل, 365 * 3, تاریخ_پایان_مشترک, 60
        )
        بازدهی_یک_ساله = بازدهی_در_بازه(
            صندوق_کامل, 365, تاریخ_پایان_مشترک, 30
        )

        # بدون داده معتبر یک‌ساله و سه‌ساله، صندوق وارد رتبه‌بندی نمی‌شود.
        if pd.isna(بازدهی_سه_ساله) or pd.isna(بازدهی_یک_ساله):
            continue

        نوسان = بازدهی_روزانه.std() * np.sqrt(252)
        افت = صندوق["nav"] / صندوق["nav"].cummax() - 1
        بیشترین_افت = افت.min()

        شارپ = (
            بازدهی_روزانه.mean() * 252 / نوسان
            if pd.notna(نوسان) and نوسان > 0 else np.nan
        )

        بازدهی_منفی = بازدهی_روزانه.clip(upper=0)
        ریسک_نزولی = np.sqrt((بازدهی_منفی ** 2).mean()) * np.sqrt(252)
        سورتینو = (
            بازدهی_روزانه.mean() * 252 / ریسک_نزولی
            if pd.notna(ریسک_نزولی) and ریسک_نزولی > 0 else np.nan
        )

        نتیجه.append({
            "scheme_code": str(کد),
            "scheme_name": صندوق_کامل.iloc[-1]["scheme_name"],
            "return_1w": بازدهی_در_بازه(صندوق_کامل, 7, تاریخ_پایان_مشترک, 5),
            "return_1m": بازدهی_در_بازه(صندوق_کامل, 30, تاریخ_پایان_مشترک, 7),
            "return_3m": بازدهی_در_بازه(صندوق_کامل, 90, تاریخ_پایان_مشترک, 10),
            "return_6m": بازدهی_در_بازه(صندوق_کامل, 180, تاریخ_پایان_مشترک, 15),
            "return_1y": بازدهی_یک_ساله,
            "return_3y": بازدهی_سه_ساله,
            "volatility": نوسان,
            "max_drawdown": بیشترین_افت,
            "sharpe": شارپ,
            "sortino": سورتینو,
            "metrics_as_of": تاریخ_پایان_مشترک.strftime("%Y-%m-%d")
        })

    return pd.DataFrame(نتیجه)


def تبدیل_پاسخ_آلفا_بتا(داده, کد, افق="3Y"):
    """ساختار پاسخ مستند Charlie API را به ستون‌های داخلی تبدیل می‌کند."""
    همه_افق_ها = داده.get("metrics") or {}
    شاخص_ها = (
        همه_افق_ها.get(افق)
        or همه_افق_ها.get(str(افق).upper())
        or همه_افق_ها.get(str(افق).lower())
        or {}
    )
    آلفا = شاخص_ها.get("alpha") if isinstance(شاخص_ها, dict) else None
    بتا = شاخص_ها.get("beta") if isinstance(شاخص_ها, dict) else None

    شمارش_ها = (داده.get("sample_counts") or {}).get("metrics", {})
    شمارش_افق = شمارش_ها.get(افق) or شمارش_ها.get(str(افق).upper()) or {}

    خطاها = []
    if آلفا is None:
        خطاها.append("آلفا در پاسخ افق " + str(افق) + " موجود نیست")
    if بتا is None:
        خطاها.append("بتا در پاسخ افق " + str(افق) + " موجود نیست")

    return {
        "scheme_code": str(کد).strip().removesuffix(".0"),
        "alpha": float(آلفا) / 100 if آلفا is not None else np.nan,
        "beta": float(بتا) if بتا is not None else np.nan,
        "alpha_beta_sample_count": شمارش_افق.get("alpha"),
        "alpha_beta_benchmark": داده.get("benchmark", ""),
        "alpha_beta_as_of": داده.get("data_as_of", ""),
        "alpha_beta_source": "Charlie Alpha API",
        "alpha_beta_error": "؛ ".join(خطاها)
    }


def دریافت_آلفا_بتا_از_سرویس(کد_صندوق_ها, افق="3Y"):
    """دریافت آلفا و بتا؛ خطای سرویس را از مقدار واقعی صفر جدا نگه می‌دارد."""
    آدرس_پایه = "https://api.charliealpha.in/v1/mf/metrics/"

    def دریافت_یک_صندوق(کد):
        کد = str(کد).strip().removesuffix(".0")
        خطای_آخر = ""
        for تلاش in range(2):
            try:
                پاسخ = requests.get(
                    آدرس_پایه + کد,
                    headers={
                        "Accept": "application/json",
                        "User-Agent": "Mozilla/5.0",
                        "Referer": "https://charliealpha.in/",
                        "Origin": "https://charliealpha.in"
                    },
                    timeout=30
                )
                if پاسخ.status_code == 429 or پاسخ.status_code >= 500:
                    خطای_آخر = "خطای موقت سرویس (HTTP " + str(پاسخ.status_code) + ")"
                    if تلاش == 0:
                        time.sleep(2)
                        continue
                پاسخ.raise_for_status()
                داده = پاسخ.json()
                نتیجه = تبدیل_پاسخ_آلفا_بتا(داده, کد, افق)
                if pd.isna(نتیجه["alpha"]) and pd.isna(نتیجه["beta"]):
                    raise ValueError(
                        نتیجه["alpha_beta_error"] or "شاخصی برای این صندوق در پاسخ API موجود نیست"
                    )
                return نتیجه
            except Exception as خطا:
                خطای_آخر = str(خطا)
                if تلاش == 0 and not isinstance(خطا, ValueError):
                    time.sleep(1)

        return {
            "scheme_code": کد,
            "alpha": np.nan,
            "beta": np.nan,
            "alpha_beta_sample_count": 0,
            "alpha_beta_benchmark": "",
            "alpha_beta_as_of": "",
            "alpha_beta_source": "Charlie Alpha API",
            "alpha_beta_error": خطای_آخر[:300]
        }

    کدهای_یکتا = list(dict.fromkeys(
        str(کد).strip().removesuffix(".0") for کد in کد_صندوق_ها
        if str(کد).strip() and str(کد).lower() != "nan"
    ))

    with ThreadPoolExecutor(max_workers=3) as اجراکننده:
        ردیف_ها = list(اجراکننده.map(دریافت_یک_صندوق, کدهای_یکتا))

    return pd.DataFrame(ردیف_ها)
