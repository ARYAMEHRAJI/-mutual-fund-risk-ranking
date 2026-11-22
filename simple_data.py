# این فایل فقط اطلاعات صندوق ها و قیمت واحدهای آن ها را از اینترنت می گیرد.

import time
import io
import requests
import pandas as pd

# آدرس اصلی سایت دریافت اطلاعات
آدرس_اصلی = "https://api.tigzig.com/mf/v1"


def دریافت_صندوق_ها():
    # فهرست صندوق ها را از سایت می گیریم
    آدرس = آدرس_اصلی + "/download"
    پاسخ = requests.get(آدرس, params={"format": "latest"}, timeout=60)
    پاسخ.raise_for_status()

    # اطلاعات را به جدول تبدیل می کنیم
    صندوق_ها = pd.read_csv(io.StringIO(پاسخ.text))
    return صندوق_ها


def انتخاب_صندوق_ها(صندوق_ها, گروه):
    # فقط صندوق های فعال را نگه می داریم
    فعال = صندوق_ها["is_active"].astype(str).str.lower().isin(["true", "1", "yes"])

    # فقط طرح مستقیم و نوع رشد را انتخاب می کنیم
    مستقیم = صندوق_ها["scheme_plan"].astype(str).str.lower() == "direct"
    رشد = صندوق_ها["scheme_option"].astype(str).str.lower() == "growth"

    # فقط صندوق های سهامی باز را نگه می داریم
    نوع = صندوق_ها["scheme_type"].astype(str).str.lower() == "open ended schemes"

    # تاریخ شروع صندوق باید حداقل سه سال قبل باشد
    صندوق_ها["first_date"] = pd.to_datetime(صندوق_ها["first_date"], errors="coerce")
    تاریخ_مجاز = pd.Timestamp.now() - pd.DateOffset(years=3)
    سابقه = صندوق_ها["first_date"] <= تاریخ_مجاز

    # نام ستون گروه ممکن است در نسخه های مختلف داده فرق کند
    ستون_گروه = None
    for نام in ["scheme_sub_category", "scheme_category", "category"]:
        if نام in صندوق_ها.columns:
            ستون_گروه = نام
            break

    if ستون_گروه is None:
        raise ValueError("ستون دسته بندی صندوق در اطلاعات پیدا نشد.")

    # گروه انتخاب شده را پیدا می کنیم
    گروه_صندوق = صندوق_ها[ستون_گروه].astype(str).str.lower()
    انتخاب_گروه = گروه_صندوق.str.contains(گروه.lower(), na=False)

    نتیجه = صندوق_ها[فعال & مستقیم & رشد & نوع & سابقه & انتخاب_گروه].copy()
    return نتیجه.reset_index(drop=True)


def دریافت_nav(کد_صندوق_ها):
    # کدها را به دسته های کوچک تقسیم می کنیم
    همه_اطلاعات = []
    اندازه_دسته = 20

    for شروع in range(0, len(کد_صندوق_ها), اندازه_دسته):
        دسته = کد_صندوق_ها[شروع:شروع + اندازه_دسته]

        # اطلاعات NAV این دسته را دریافت می کنیم
        آدرس = آدرس_اصلی + "/nav"
        پارامترها = {"schemes": ",".join(str(کد) for کد in دسته)}
        پاسخ = requests.get(آدرس, params=پارامترها, timeout=90)
        پاسخ.raise_for_status()

        اطلاعات = پاسخ.json()
        for صندوق in اطلاعات.get("schemes", []):
            for ردیف in صندوق.get("data", []):
                همه_اطلاعات.append({
                    "scheme_code": صندوق["scheme_code"],
                    "scheme_name": صندوق.get("scheme_name", ""),
                    "date": ردیف.get("date"),
                    "nav": ردیف.get("nav")
                })

        # کمی صبر می کنیم تا درخواست ها پشت سر هم ارسال نشوند
        if شروع + اندازه_دسته < len(کد_صندوق_ها):
            time.sleep(21)

    جدول = pd.DataFrame(همه_اطلاعات)
    if جدول.empty:
        raise ValueError("برای صندوق های انتخاب شده اطلاعات NAV دریافت نشد.")

    جدول["date"] = pd.to_datetime(جدول["date"], errors="coerce")
    جدول["nav"] = pd.to_numeric(جدول["nav"], errors="coerce")
    جدول = جدول.dropna(subset=["date", "nav"])
    جدول = جدول[جدول["nav"] > 0]
    return جدول.sort_values(["scheme_code", "date"])
