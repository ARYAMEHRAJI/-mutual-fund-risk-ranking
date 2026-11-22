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
    # اطلاعات شاخص کل بازدهی را از سایت Nifty دریافت می کنیم
    آدرس = "https://www.niftyindices.com/Backpage.aspx/getTotalReturnIndexString"

    # تاریخ ها را به شکل مورد قبول سایت تبدیل می کنیم
    شروع = pd.Timestamp(تاریخ_شروع).strftime("%d-%b-%Y")
    پایان = pd.Timestamp(تاریخ_پایان).strftime("%d-%b-%Y")

    # سایت Nifty این اطلاعات را داخل یک متن مخصوص دریافت می کند
    اطلاعات_درخواست = {
        "cinfo": "{'name':'" + نام_شاخص + "','startDate':'" + شروع
        + "','endDate':'" + پایان + "','indexName':'" + نام_شاخص + "'}"
    }

    # سربرگ های شبیه مرورگر را ارسال می کنیم
    سربرگ = {
        "Content-Type": "application/json; charset=UTF-8",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": "https://www.niftyindices.com/reports/historical-data",
        "Origin": "https://www.niftyindices.com",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/131.0 Safari/537.36"
    }

    پاسخ = None
    خطاها = []

    # ابتدا با cloudscraper تلاش می کنیم تا در صورت وجود محافظت سایت عبور کنیم
    try:
        import cloudscraper
        مرورگر = cloudscraper.create_scraper()
        پاسخ = مرورگر.post(
            آدرس,
            headers=سربرگ,
            json=اطلاعات_درخواست,
            timeout=60
        )
        پاسخ.raise_for_status()
    except Exception as خطا:
        خطاها.append(str(خطا))
        # اگر روش اول جواب نداد، یک بار با requests معمولی تلاش می کنیم
        try:
            پاسخ = requests.post(
                آدرس,
                headers=سربرگ,
                json=اطلاعات_درخواست,
                timeout=60
            )
            پاسخ.raise_for_status()
        except Exception as خطای_دوم:
            خطاها.append(str(خطای_دوم))
            raise RuntimeError(
                "دریافت شاخص " + نام_شاخص + " از سایت Nifty ناموفق بود: "
                + " | ".join(خطاها)
            )

    # پاسخ سایت باید JSON باشد؛ اگر نبود، پیام قابل فهم نشان می دهیم
    try:
        محتوای_پاسخ = پاسخ.json()
    except ValueError:
        نمونه_پاسخ = پاسخ.text[:200].replace("\\n", " ")
        raise ValueError(
            "سایت Nifty به جای JSON پاسخ دیگری فرستاد. "
            + "کد پاسخ: " + str(پاسخ.status_code)
            + "، ابتدای پاسخ: " + نمونه_پاسخ
        )

    if "d" not in محتوای_پاسخ:
        raise ValueError("ساختار پاسخ سایت Nifty معتبر نیست.")

    # اطلاعات اصلی داخل بخش d قرار دارد
    ردیف_ها = محتوای_پاسخ["d"]
    if isinstance(ردیف_ها, str):
        ردیف_ها = json.loads(ردیف_ها)

    شاخص = pd.DataFrame(ردیف_ها)
    if شاخص.empty:
        raise ValueError(
            "برای شاخص " + نام_شاخص + " در بازه انتخاب شده داده ای پیدا نشد."
        )

    # نام ستون تاریخ در پاسخ Nifty ممکن است متفاوت باشد
    ستون_تاریخ = "Date" if "Date" in شاخص.columns else "HistoricalDate"
    if ستون_تاریخ not in شاخص.columns or "TotalReturnsIndex" not in شاخص.columns:
        raise ValueError("ستون های مورد انتظار در اطلاعات شاخص پیدا نشد.")

    شاخص = شاخص[[ستون_تاریخ, "TotalReturnsIndex"]].copy()
    شاخص.columns = ["date", "close"]
    شاخص["date"] = pd.to_datetime(شاخص["date"], errors="coerce")
    شاخص["close"] = pd.to_numeric(شاخص["close"], errors="coerce")
    شاخص = شاخص.dropna().sort_values("date")

    if شاخص.empty:
        raise ValueError("داده های شاخص پس از پاک سازی خالی شدند.")

    return شاخص


def محاسبه_آلفا_بتا(اطلاعات_nav, اطلاعات_شاخص):
    # ستون های فایل شاخص باید date و close باشند
    شاخص = اطلاعات_شاخص[["date", "close"]].copy()
    شاخص["date"] = pd.to_datetime(شاخص["date"])
    شاخص["close"] = pd.to_numeric(شاخص["close"], errors="coerce")
    شاخص = شاخص.dropna().sort_values("date")

    # بازدهی روزانه شاخص را حساب می کنیم
    شاخص["بازدهی_شاخص"] = شاخص["close"].pct_change()

    نتیجه = []
    for کد, صندوق in اطلاعات_nav.groupby("scheme_code"):
        صندوق = صندوق.sort_values("date").copy()
        صندوق["بازدهی_صندوق"] = صندوق["nav"].pct_change()

        # بازدهی صندوق و شاخص را بر اساس تاریخ مشترک کنار هم می گذاریم
        مشترک = pd.merge(
            صندوق[["date", "بازدهی_صندوق"]],
            شاخص[["date", "بازدهی_شاخص"]],
            on="date"
        ).dropna()

        if len(مشترک) < 30:
            continue

        # بتا یعنی میزان حساسیت صندوق به تغییرات شاخص
        واریانس_شاخص = مشترک["بازدهی_شاخص"].var()
        if واریانس_شاخص == 0:
            continue

        بتا = مشترک["بازدهی_صندوق"].cov(مشترک["بازدهی_شاخص"]) / واریانس_شاخص

        # آلفا یعنی بازدهی اضافه صندوق نسبت به بازدهی مورد انتظار
        نرخ_بدون_ریسک_روزانه = 0
        آلفای_روزانه = (
            مشترک["بازدهی_صندوق"].mean()
            - نرخ_بدون_ریسک_روزانه
            - بتا * (مشترک["بازدهی_شاخص"].mean() - نرخ_بدون_ریسک_روزانه)
        )
        آلفای_سالانه = آلفای_روزانه * 252

        نتیجه.append({
            "scheme_code": کد,
            "beta": بتا,
            "alpha": آلفای_سالانه
        })

    return pd.DataFrame(نتیجه, columns=["scheme_code", "beta", "alpha"])
