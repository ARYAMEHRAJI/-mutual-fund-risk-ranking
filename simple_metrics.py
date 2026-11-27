# این فایل شاخص های بازدهی و ریسک صندوق ها را محاسبه می کند.
# آلفا و بتا مستقیماً از سرویس Charlie Alpha دریافت می شوند.

import requests
import numpy as np
import pandas as pd
from concurrent.futures import ThreadPoolExecutor


def بازدهی_در_بازه(جدول, تعداد_روز):
    # آخرین NAV و آخرین NAV در تاریخِ مساوی یا قبل از شروع بازه را پیدا می کنیم.
    تاریخ_پایان = جدول["date"].max()
    تاریخ_شروع = تاریخ_پایان - pd.Timedelta(days=تعداد_روز)
    داده_شروع = جدول[جدول["date"] <= تاریخ_شروع]

    if داده_شروع.empty:
        return np.nan

    nav_شروع = داده_شروع.iloc[-1]["nav"]
    nav_پایان = جدول.iloc[-1]["nav"]
    return nav_پایان / nav_شروع - 1


def محاسبه_شاخص_ها(اطلاعات_nav):
    # هر صندوق جداگانه بررسی می شود.
    نتیجه = []

    for کد, صندوق in اطلاعات_nav.groupby("scheme_code"):
        صندوق = صندوق.sort_values("date").reset_index(drop=True)

        if len(صندوق) < 2:
            continue

        nav = صندوق["nav"]
        بازدهی = nav.pct_change().dropna()

        # نوسان سالانه، با فرض ۲۵۲ روز معاملاتی در سال
        نوسان = بازدهی.std() * np.sqrt(252)

        # بیشترین افت از بالاترین NAV ثبت شده تا هر روز
        افت = nav / nav.cummax() - 1
        بیشترین_افت = افت.min()

        # شارپ: بازدهی سالانه تقسیم بر نوسان سالانه؛ نرخ بدون ریسک صفر فرض شده است.
        شارپ = (بازدهی.mean() * 252 / نوسان) if نوسان > 0 else np.nan

        # سورتینو: فقط بخش منفی بازدهی ها در ریسک نزولی اثر دارد.
        # روزهای بدون افت نیز در میانگین محاسبه باقی می مانند.
        بازدهی_منفی = بازدهی.clip(upper=0)
        ریسک_نزولی = np.sqrt((بازدهی_منفی ** 2).mean()) * np.sqrt(252)
        سورتینو = (
            بازدهی.mean() * 252 / ریسک_نزولی
            if ریسک_نزولی > 0 else np.nan
        )

        نتیجه.append({
            "scheme_code": کد,
            "scheme_name": صندوق.iloc[-1]["scheme_name"],
            "return_1w": بازدهی_در_بازه(صندوق, 7),
            "return_1m": بازدهی_در_بازه(صندوق, 30),
            "return_3m": بازدهی_در_بازه(صندوق, 90),
            "return_6m": بازدهی_در_بازه(صندوق, 180),
            "return_1y": بازدهی_در_بازه(صندوق, 365),
            "return_3y": بازدهی_در_بازه(صندوق, 365 * 3),
            "volatility": نوسان,
            "max_drawdown": بیشترین_افت,
            "sharpe": شارپ,
            "sortino": سورتینو
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

    # کدهای تکراری را حذف می کنیم تا برای یک صندوق چند درخواست نفرستیم.
    کدهای_یکتا = list(dict.fromkeys(
        str(کد).strip().removesuffix(".0") for کد in کد_صندوق_ها
    ))

    # سه درخواست هم زمان، سرعت را بهتر می کند و فشار زیادی به سرویس وارد نمی کند.
    with ThreadPoolExecutor(max_workers=3) as اجراکننده:
        ردیف_ها = list(اجراکننده.map(دریافت_یک_صندوق, کدهای_یکتا))

    return pd.DataFrame(ردیف_ها)
