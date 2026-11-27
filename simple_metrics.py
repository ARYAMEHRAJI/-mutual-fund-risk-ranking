# این فایل شاخص های عملکرد و ریسک را در یک بازه مشترک سه ساله محاسبه می کند.
# آلفا و بتا مستقیماً از سرویس Charlie Alpha دریافت می شوند.

import requests
import numpy as np
import pandas as pd
from concurrent.futures import ThreadPoolExecutor


def بازدهی_در_بازه(جدول, تعداد_روز, تاریخ_پایان_مشترک):
    # برای همه صندوق ها از تاریخ پایان مشترک استفاده می کنیم.
    تاریخ_شروع = تاریخ_پایان_مشترک - pd.Timedelta(days=تعداد_روز)
    داده_شروع = جدول[جدول["date"] <= تاریخ_شروع]
    داده_پایان = جدول[جدول["date"] <= تاریخ_پایان_مشترک]

    if داده_شروع.empty or داده_پایان.empty:
        return np.nan

    nav_شروع = داده_شروع.iloc[-1]["nav"]
    nav_پایان = داده_پایان.iloc[-1]["nav"]
    return nav_پایان / nav_شروع - 1


def محاسبه_شاخص_ها(اطلاعات_nav):
    # تاریخ پایان مشترک باعث می شود صندوق ها با یک نقطه زمانی یکسان مقایسه شوند.
    اطلاعات_nav = اطلاعات_nav.copy()
    اطلاعات_nav["date"] = pd.to_datetime(اطلاعات_nav["date"], errors="coerce")
    اطلاعات_nav["nav"] = pd.to_numeric(اطلاعات_nav["nav"], errors="coerce")
    اطلاعات_nav = اطلاعات_nav.dropna(subset=["date", "nav"])
    اطلاعات_nav = اطلاعات_nav[اطلاعات_nav["nav"] > 0]

    if اطلاعات_nav.empty:
        return pd.DataFrame()

    تاریخ_پایان_مشترک = اطلاعات_nav["date"].max()
    تاریخ_شروع_سه_ساله = تاریخ_پایان_مشترک - pd.DateOffset(years=3)
    نتیجه = []

    for کد, صندوق_کامل in اطلاعات_nav.groupby("scheme_code"):
        صندوق_کامل = صندوق_کامل.sort_values("date").reset_index(drop=True)

        # برای محاسبه بازده سه ساله، تاریخچه کامل دریافت شده را نگه می داریم.
        if len(صندوق_کامل) < 2:
            continue

        # فقط داده های سه سال اخیر برای سنجش ریسک و کیفیت استفاده می شوند.
        صندوق = صندوق_کامل[
            صندوق_کامل["date"] >= تاریخ_شروع_سه_ساله
        ].copy().reset_index(drop=True)

        if len(صندوق) < 30:
            continue

        nav = صندوق["nav"]
        بازدهی = nav.pct_change().dropna()

        if len(بازدهی) < 20:
            continue

        # نوسان سالانه با فرض ۲۵۲ روز معاملاتی در سال
        نوسان = بازدهی.std() * np.sqrt(252)

        # بیشترین افت از قله قبلی در پنجره مشترک سه ساله
        افت = nav / nav.cummax() - 1
        بیشترین_افت = افت.min()

        # شارپ با نرخ بدون ریسک صفر؛ این فرض در گزارش پروژه ذکر می شود.
        شارپ = (
            بازدهی.mean() * 252 / نوسان
            if pd.notna(نوسان) and نوسان > 0 else np.nan
        )

        # سورتینو با بازده هدف صفر و لحاظ کردن روزهای بدون افت در مخرج
        بازدهی_منفی = بازدهی.clip(upper=0)
        ریسک_نزولی = np.sqrt((بازدهی_منفی ** 2).mean()) * np.sqrt(252)
        سورتینو = (
            بازدهی.mean() * 252 / ریسک_نزولی
            if pd.notna(ریسک_نزولی) and ریسک_نزولی > 0 else np.nan
        )

        نتیجه.append({
            "scheme_code": کد,
            "scheme_name": صندوق_کامل.iloc[-1]["scheme_name"],
            "return_1w": بازدهی_در_بازه(صندوق_کامل, 7, تاریخ_پایان_مشترک),
            "return_1m": بازدهی_در_بازه(صندوق_کامل, 30, تاریخ_پایان_مشترک),
            "return_3m": بازدهی_در_بازه(صندوق_کامل, 90, تاریخ_پایان_مشترک),
            "return_6m": بازدهی_در_بازه(صندوق_کامل, 180, تاریخ_پایان_مشترک),
            "return_1y": بازدهی_در_بازه(صندوق_کامل, 365, تاریخ_پایان_مشترک),
            "return_3y": بازدهی_در_بازه(صندوق_کامل, 365 * 3, تاریخ_پایان_مشترک),
            "volatility": نوسان,
            "max_drawdown": بیشترین_افت,
            "sharpe": شارپ,
            "sortino": سورتینو,
            "metrics_as_of": تاریخ_پایان_مشترک.strftime("%Y-%m-%d")
        })

    return pd.DataFrame(نتیجه)


def دریافت_آلفا_بتا_از_سرویس(کد_صندوق_ها, افق="3Y"):
    # این سرویس آلفا و بتا را با شاخص مرجع مرتبط با هر صندوق برمی گرداند.
    آدرس_پایه = "https://api.charliealpha.in/v1/mf/metrics/"

    def دریافت_یک_صندوق(کد):
        کد = str(کد).strip()
        if کد.endswith(".0"):
            کد = کد[:-2]

        try:
            پاسخ = requests.get(
                آدرس_پایه + کد,
                headers={
                    "Accept": "application/json",
                    "User-Agent": "Mozilla/5.0",
                    "Referer": "https://charliealpha.in/",
                    "Origin": "https://charliealpha.in"
                },
                timeout=25
            )
            پاسخ.raise_for_status()
            داده = پاسخ.json()

            شاخص_ها = داده.get("metrics", {}).get(افق, {})
            آلفا = شاخص_ها.get("alpha")
            بتا = شاخص_ها.get("beta")
            تعداد_نمونه = (
                داده.get("sample_counts", {})
                .get("metrics", {})
                .get(افق, {})
                .get("alpha")
            )

            return {
                "scheme_code": کد,
                "alpha": float(آلفا) / 100 if آلفا is not None else np.nan,
                "beta": float(بتا) if بتا is not None else np.nan,
                "alpha_beta_sample_count": تعداد_نمونه,
                "alpha_beta_benchmark": داده.get("benchmark", ""),
                "alpha_beta_as_of": داده.get("data_as_of", ""),
                "alpha_beta_source": "Charlie Alpha API",
                "alpha_beta_error": ""
            }

        except Exception as خطا:
            return {
                "scheme_code": کد,
                "alpha": np.nan,
                "beta": np.nan,
                "alpha_beta_sample_count": 0,
                "alpha_beta_benchmark": "",
                "alpha_beta_as_of": "",
                "alpha_beta_source": "Charlie Alpha API",
                "alpha_beta_error": str(خطا)[:220]
            }

    # کدهای تکراری حذف می شوند تا برای یک صندوق چند درخواست نفرستیم.
    کدهای_یکتا = list(dict.fromkeys(
        str(کد).strip().removesuffix(".0") for کد in کد_صندوق_ها
    ))

    # سه درخواست هم زمان برای کاهش فشار روی سرویس
    with ThreadPoolExecutor(max_workers=3) as اجراکننده:
        ردیف_ها = list(اجراکننده.map(دریافت_یک_صندوق, کدهای_یکتا))

    return pd.DataFrame(ردیف_ها)
