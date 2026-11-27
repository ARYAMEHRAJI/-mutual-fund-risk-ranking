# دریافت فهرست صندوق‌ها و تاریخچه NAV از منبع داده

import time
import io
import re
import requests
import pandas as pd

آدرس_اصلی = "https://api.tigzig.com/mf/v1"

# فقط گروه‌هایی را می‌پذیریم که نام دسته‌بندی آن‌ها را دقیق می‌شناسیم.
# این کار جلوی اشتباه گرفتن «Large & Mid Cap» با «Mid Cap» را می‌گیرد.
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
    "Hybrid - Conservative": ["conservative hybrid", "conservative hybrid fund"],
    "Hybrid - Balanced": ["balanced hybrid", "balanced hybrid fund"],
    "Hybrid - Aggressive": ["aggressive hybrid", "aggressive hybrid fund"],
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
    for پیشوند in ["equity ", "debt ", "equity scheme ", "debt scheme "]:
        if متن.startswith(پیشوند):
            متن = متن[len(پیشوند):].strip()
    return متن


def پیدا_کردن_گروه(نام_دسته):
    نام = تمیزکردن_نام(نام_دسته)

    for گروه, نام_های_مجاز in گروه_ها.items():
        if نام in نام_های_مجاز:
            return گروه

    return None


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

    # فقط صندوق‌های فعال، طرح مستقیم، نوع رشد و باز را انتخاب می‌کنیم.
    فعال = داده["is_active"].astype(str).str.lower().isin(["true", "1", "yes"])
    مستقیم = داده["scheme_plan"].astype(str).str.lower().str.strip().eq("direct")
    رشد = داده["scheme_option"].astype(str).str.lower().str.strip().eq("growth")
    باز = داده["scheme_type"].astype(str).str.lower().str.contains("open ended", na=False)

    # برای محاسبه عملکرد سه‌ساله، صندوق باید حداقل سه سال سابقه داشته باشد.
    داده["first_date"] = pd.to_datetime(dاده["first_date"], errors="coerce")
    تاریخ_مجاز = pd.Timestamp.now().normalize() - pd.DateOffset(years=3)
    سابقه = داده["first_date"].notna() & (داده["first_date"] <= تاریخ_مجاز)

    # نام ستون دسته‌بندی در نسخه‌های مختلف فایل ممکن است فرق کند.
    دسته_ها = pd.Series(index=داده.index, dtype="object")
    for ستون in ["scheme_sub_category", "category_sub", "scheme_category", "category"]:
        if ستون in داده.columns:
            دسته_ها = دسته_ها.combine_first(داده[ستون])

    if دسته_ها.isna().all():
        raise ValueError("ستون دسته‌بندی صندوق در فایل منبع پیدا نشد.")

    داده["fund_group"] = دسته_ها.apply(پیدا_کردن_گروه)
    انتخاب = فعال & مستقیم & رشد & باز & سابقه & داده["fund_group"].notna()

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
