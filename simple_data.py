# دریافت فهرست صندوق‌ها و تاریخچه NAV از منبع داده

import time
import io
import re
import requests
import pandas as pd

آدرس_اصلی = "https://api.tigzig.com/mf/v1"

# گروه‌های استاندارد را دقیق تشخیص می‌دهیم تا دسته‌هایی مثل Large & Mid Cap
# به‌اشتباه با Mid Cap یکی نشوند. دسته‌های بخشی، موضوعی و کالایی نیز جدا هستند.
گروه_ها = {
    "Equity - Large Cap": ["large cap", "large cap fund"],
    "Equity - Mid Cap": ["mid cap", "mid cap fund"],
    "Equity - Small Cap": ["small cap", "small cap fund"],
    "Equity - Flexi Cap": ["flexi cap", "flexi cap fund"],
    "Equity - Multi Cap": ["multi cap", "multi cap fund"],
    "Equity - Focused": ["focused", "focused fund", "focused equity fund"],
    "Debt - Overnight": ["overnight", "overnight fund"],
    "Debt - Liquid": ["liquid", "liquid fund"],
    "Debt - Ultra Short Duration": ["ultra short duration", "ultra short duration fund"],
    "Debt - Low Duration": ["low duration", "low duration fund"],
    "Debt - Money Market": ["money market", "money market fund"],
    "Debt - Short Duration": ["short duration", "short duration fund"],
    "Debt - Medium Duration": ["medium duration", "medium duration fund"],
    "Debt - Medium to Long Duration": ["medium to long duration", "medium to long duration fund"],
    "Debt - Long Duration": ["long duration", "long duration fund"],
    "Debt - Dynamic Bond": ["dynamic bond", "dynamic bond fund"],
    "Debt - Corporate Bond": ["corporate bond", "corporate bond fund"],
    "Debt - Credit Risk": ["credit risk", "credit risk fund"],
    "Debt - Banking and PSU": ["banking and psu", "banking and psu fund"],
    "Debt - Gilt": ["gilt", "gilt fund"],
    "Debt - Gilt 10Y": ["gilt fund with 10 year constant duration", "gilt with 10 year constant duration"],
    "Debt - Floater": ["floater", "floater fund"],
    "Hybrid - Conservative": ["conservative", "conservative hybrid", "conservative hybrid fund"],
    "Hybrid - Balanced": ["balanced", "balanced hybrid", "balanced hybrid fund"],
    "Hybrid - Aggressive": ["aggressive", "aggressive hybrid", "aggressive hybrid fund"],
    "Hybrid - Dynamic Allocation": ["dynamic asset allocation", "dynamic asset allocation or balanced advantage", "balanced advantage"],
    "Hybrid - Multi Asset": ["multi asset allocation", "multi asset allocation fund"],
    "Hybrid - Equity Savings": ["equity savings", "equity savings fund"],
    "Hybrid - Arbitrage": ["arbitrage", "arbitrage fund"]
}


def تمیزکردن_نام(مقدار):
    متن = str(مقدار).lower().strip()
    متن = re.sub(r"[^a-z0-9 ]", " ", متن)
    متن = " ".join(متن.split())

    # پیشوند گروه اصلی را حذف می‌کنیم تا تطبیق فقط با نام زیرگروه باشد.
    for پیشوند in ["equity scheme ", "debt scheme ", "hybrid scheme ", "other scheme ", "equity ", "debt ", "hybrid ", "other "]:
        if متن.startswith(پیشوند):
            متن = متن[len(پیشوند):].strip()
    return متن


def پیدا_کردن_گروه(نام_دسته, نام_صندوق=""):
    نام = تمیزکردن_نام(نام_دسته)
    نام_کامل = تمیزکردن_نام(str(نام_دسته) + " " + str(نام_صندوق))

    # ابتدا دسته‌های بخشی و موضوعی را از روی دسته رسمی تشخیص می‌دهیم.
    if "sectoral" in نام or "sector fund" in نام:
        return "Equity - Sectoral"
    if "thematic" in نام or "theme fund" in نام:
        return "Equity - Thematic"

    # طلا و نقره جدا از ETFهای شاخصی قرار می‌گیرند.
    if "gold" in نام or "gold fund" in نام_کامل or "gold etf" in نام_کامل:
        return "Other - Gold"
    if "silver" in نام or "silver fund" in نام_کامل or "silver etf" in نام_کامل:
        return "Other - Silver"
    if "index" in نام or "etf" in نام or "index" in نام_کامل or "etf" in نام_کامل:
        return "Other - Index"

    for گروه, نام_های_مجاز in گروه_ها.items():
        if نام in نام_های_مجاز:
            return گروه

    return None


def دریافت_دارایی_تحت_مدیریت(کد_صندوق_ها):
    """
    دریافت AUM روزانه کل صندوق (همه طرح‌ها و گزینه‌ها) از داده AMFI.
    واحد مقدار خروجی: کرور روپیه هند.
    """
    آدرس = "https://api.tigzig.com/mf/v1/download/scheme_details_latest"
    پاسخ = requests.get(آدرس, params={"format": "csv.gz"}, timeout=120)
    پاسخ.raise_for_status()

    جزئیات = pd.read_csv(io.BytesIO(پاسخ.content), compression="gzip", low_memory=False)

    ستون_های_لازم = [
        "scheme_code", "amfi_daily_fund_aum_cr_all_plans", "amfi_daily_aum_date"
    ]
    ستون_های_گم_شده = [ستون for ستون in ستون_های_لازم if ستون not in جزئیات.columns]
    if ستون_های_گم_شده:
        raise ValueError("ستون‌های دارایی تحت مدیریت در منبع پیدا نشد: " + ", ".join(ستون_های_گم_شده))

    if "source" in جزئیات.columns:
        جزئیات = جزئیات[جزئیات["source"].astype(str).str.upper() == "MF"].copy()

    جزئیات["scheme_code"] = (
        جزئیات["scheme_code"].astype(str).str.replace(r"\.0$", "", regex=True)
    )
    جزئیات["aum_cr"] = pd.to_numeric(
        جزئیات["amfi_daily_fund_aum_cr_all_plans"], errors="coerce"
    )
    جزئیات["aum_as_of"] = pd.to_datetime(
        جزئیات["amfi_daily_aum_date"], errors="coerce"
    ).dt.strftime("%Y-%m-%d")

    کدها = [
        str(کد).strip().removesuffix(".0") for کد in کد_صندوق_ها
    ]
    خروجی = جزئیات[جزئیات["scheme_code"].isin(کدها)][
        ["scheme_code", "aum_cr", "aum_as_of"]
    ].drop_duplicates("scheme_code")

    return خروجی.reset_index(drop=True)


def دریافت_صندوق_ها():
    پاسخ = requests.get(
        آدرس_اصلی + "/download",
        params={"format": "latest"},
        timeout=60
    )
    پاسخ.raise_for_status()
    return pd.read_csv(io.StringIO(پاسخ.text))


def انتخاب_صندوق_ها(صندوق_ها):
    داده = صندوق_ها.copy()

    ستون_های_لازم = [
        "scheme_code", "scheme_name", "is_active",
        "scheme_plan", "scheme_option", "scheme_type", "first_date"
    ]
    ستون_های_گم_شده = [ستون for ستون in ستون_های_لازم if ستون not in داده.columns]
    if ستون_های_گم_شده:
        raise ValueError("ستون‌های ضروری در فایل منبع پیدا نشد: " + ", ".join(ستون_های_گم_شده))

    # صندوق‌های فعال، باز و باسابقه را انتخاب می‌کنیم؛ ETFها می‌توانند طرح Other داشته باشند.
    فعال = داده["is_active"].astype(str).str.lower().isin(["true", "1", "yes"])
    مستقیم = داده["scheme_plan"].astype(str).str.lower().str.strip().eq("direct")
    رشد = داده["scheme_option"].astype(str).str.lower().str.strip().eq("growth")
    باز = داده["scheme_type"].astype(str).str.lower().str.contains("open ended", na=False)

    # برای محاسبه عملکرد سه‌ساله، صندوق باید حداقل سه سال سابقه داشته باشد.
    داده["first_date"] = pd.to_datetime(داده["first_date"], errors="coerce")
    تاریخ_مجاز = pd.Timestamp.now().normalize() - pd.DateOffset(years=3)
    سابقه = داده["first_date"].notna() & (داده["first_date"] <= تاریخ_مجاز)

    # نام ستون دسته‌بندی در نسخه‌های مختلف فایل ممکن است فرق کند.
    دسته_ها = pd.Series(index=داده.index, dtype="object")
    for ستون in ["scheme_sub_category", "category_sub", "scheme_category", "category"]:
        if ستون in داده.columns:
            مقدار_دسته = داده[ستون].replace(r"^\\s*$", pd.NA, regex=True)
            دسته_ها = دسته_ها.combine_first(مقدار_دسته)

    if دسته_ها.isna().all():
        raise ValueError("ستون دسته‌بندی صندوق در فایل منبع پیدا نشد.")

    داده["fund_group"] = [
        پیدا_کردن_گروه(دسته, نام)
        for دسته, نام in zip(دسته_ها, داده["scheme_name"])
    ]

    # صندوق‌های فعال، باز و باسابقه؛ ETFها و صندوق‌های شاخصی ممکن است طرح Direct نداشته باشند.
    طرح_مجاز = مستقیم | (
        داده["fund_group"].astype(str).str.startswith("Other -")
        & داده["scheme_plan"].astype(str).str.lower().str.strip().isin(["other", "direct"])
    )
    گزینه_مجاز = رشد | (
        داده["fund_group"].astype(str).str.startswith("Other -")
        & داده["scheme_option"].astype(str).str.lower().str.strip().eq("other")
    )
    منبع_مجاز = (
        داده["source"].astype(str).str.upper().eq("MF")
        if "source" in داده.columns else pd.Series(True, index=داده.index)
    )
    انتخاب = فعال & طرح_مجاز & گزینه_مجاز & باز & سابقه & منبع_مجاز & داده["fund_group"].notna()

    نتیجه = داده[انتخاب].copy()
    نتیجه["scheme_code"] = نتیجه["scheme_code"].astype(str).str.replace(r"\.0$", "", regex=True)
    نتیجه = نتیجه.drop_duplicates("scheme_code")
    return نتیجه.reset_index(drop=True)


def دریافت_nav(کد_صندوق_ها):
    همه_اطلاعات = []
    اندازه_دسته = 20

    کدها = list(dict.fromkeys(str(کد).strip().removesuffix(".0") for کد in کد_صندوق_ها))

    for شروع in range(0, len(کدها), اندازه_دسته):
        دسته = کدها[شروع:شروع + اندازه_دسته]
        پاسخ = requests.get(
            آدرس_اصلی + "/nav",
            params={"schemes": ",".join(دسته)},
            timeout=90
        )
        پاسخ.raise_for_status()

        اطلاعات = پاسخ.json()
        for صندوق in اطلاعات.get("schemes", []):
            for ردیف in صندوق.get("data", []):
                همه_اطلاعات.append({
                    "scheme_code": str(صندوق["scheme_code"]),
                    "scheme_name": صندوق.get("scheme_name", ""),
                    "date": ردیف.get("date"),
                    "nav": ردیف.get("nav")
                })

        if شروع + اندازه_دسته < len(کدها):
            time.sleep(1)

    جدول = pd.DataFrame(همه_اطلاعات)
    if جدول.empty:
        raise ValueError("برای صندوق‌های انتخاب‌شده اطلاعات NAV دریافت نشد.")

    جدول["date"] = pd.to_datetime(جدول["date"], errors="coerce")
    جدول["nav"] = pd.to_numeric(جدول["nav"], errors="coerce")
    جدول = جدول.dropna(subset=["date", "nav"])
    جدول = جدول[جدول["nav"] > 0]
    return جدول.sort_values(["scheme_code", "date"]).reset_index(drop=True)
