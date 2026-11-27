# به‌روزرسانی خودکار روزانه داده‌های صندوق‌ها
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from simple_data import دریافت_صندوق_ها, انتخاب_صندوق_ها, دریافت_nav, دریافت_دارایی_تحت_مدیریت
from simple_metrics import محاسبه_شاخص_ها, دریافت_آلفا_بتا_از_سرویس
from simple_ranking import رتبه_بندی, انتخاب_صندوق_های_متنوع


def main():
    print("دریافت فهرست صندوق‌ها...")
    همه_صندوق_ها = دریافت_صندوق_ها()
    واجد_شرایط = انتخاب_صندوق_ها(همه_صندوق_ها)
    if واجد_شرایط.empty:
        raise RuntimeError("هیچ صندوق واجد شرایطی پیدا نشد.")

    print(f"دریافت NAV برای {len(واجد_شرایط)} صندوق...")
    nav = دریافت_nav(واجد_شرایط["scheme_code"].astype(str).tolist())
    شاخص_ها = محاسبه_شاخص_ها(nav)
    if شاخص_ها.empty:
        raise RuntimeError("شاخص معتبری از NAV دریافت نشد.")

    شاخص_ها["scheme_code"] = شاخص_ها["scheme_code"].astype(str).str.replace(r"\.0$", "", regex=True)
    گروه_ها = واجد_شرایط[["scheme_code", "fund_group"]].copy()
    گروه_ها["scheme_code"] = گروه_ها["scheme_code"].astype(str).str.replace(r"\.0$", "", regex=True)
    شاخص_ها = شاخص_ها.merge(گروه_ها.drop_duplicates("scheme_code"), on="scheme_code", how="left")

    print("دریافت دارایی تحت مدیریت از گزارش روزانه AMFI...")
    try:
        دارایی_تحت_مدیریت = دریافت_دارایی_تحت_مدیریت(
            واجد_شرایط["scheme_code"].astype(str).tolist()
        )
    except Exception as خطای_دارایی:
        print("هشدار: دریافت AUM ناموفق بود؛ رتبه‌بندی بدون این معیار انجام می‌شود: " + str(خطای_دارایی))
        دارایی_تحت_مدیریت = pd.DataFrame(columns=["scheme_code", "aum_cr", "aum_as_of"])
    شاخص_ها = شاخص_ها.merge(دارایی_تحت_مدیریت, on="scheme_code", how="left")

    # ابتدا رتبه‌بندی همه صندوق‌ها را انجام می‌دهیم.
    نتیجه = رتبه_بندی(شاخص_ها, ستون_گروه="fund_group")

    # اطلاعات طرح و نوع معامله را نیز به فایل نهایی اضافه می‌کنیم.
    ستون_های_طرح = [
        ستون for ستون in [
            "scheme_code", "scheme_plan", "scheme_option", "scheme_type",
            "category_sub", "is_etf", "trading_type", "source"
        ] if ستون in واجد_شرایط.columns
    ]
    اطلاعات_طرح = واجد_شرایط[ستون_های_طرح].copy()
    اطلاعات_طرح["scheme_code"] = اطلاعات_طرح["scheme_code"].astype(str).str.replace(r"\.0$", "", regex=True)
    نتیجه["scheme_code"] = نتیجه["scheme_code"].astype(str).str.replace(r"\.0$", "", regex=True)
    نتیجه = نتیجه.merge(اطلاعات_طرح.drop_duplicates("scheme_code"), on="scheme_code", how="left")

    # آلفا و بتا را برای همه صندوق‌های تحلیل‌شده می‌گیریم، نه فقط پنج پیشنهاد.
    کدهای_همه_صندوق_ها = نتیجه["scheme_code"].astype(str).tolist()
    print(f"دریافت آلفا و بتا برای همه {len(کدهای_همه_صندوق_ها)} صندوق...")
    آلفا_بتا = دریافت_آلفا_بتا_از_سرویس(کدهای_همه_صندوق_ها, افق="3Y")

    تعداد_آلفا = int(آلفا_بتا["alpha"].notna().sum())
    تعداد_بتا = int(آلفا_بتا["beta"].notna().sum())
    print("صندوق‌های دارای آلفا:", تعداد_آلفا, "/", len(کدهای_همه_صندوق_ها))
    print("صندوق‌های دارای بتا:", تعداد_بتا, "/", len(کدهای_همه_صندوق_ها))

    خطاهای_آلفا_بتا = آلفا_بتا[
        آلفا_بتا["alpha_beta_error"].astype(str).str.strip().ne("")
    ]
    for _, ردیف_خطا in خطاهای_آلفا_بتا.iterrows():
        print("هشدار آلفا/بتا برای", ردیف_خطا["scheme_code"], ":", ردیف_خطا["alpha_beta_error"])

    آلفا_بتا["scheme_code"] = آلفا_بتا["scheme_code"].astype(str).str.replace(r"\.0$", "", regex=True)
    نتیجه = نتیجه.merge(آلفا_بتا, on="scheme_code", how="left")

    for ستون in ["alpha", "beta"]:
        if ستون not in نتیجه.columns:
            نتیجه[ستون] = None

    تاریخ_شاخص = str(نتیجه["metrics_as_of"].dropna().max())
    آمار_گروه = واجد_شرایط.groupby("fund_group")["scheme_code"].nunique().to_dict()

    # صندوق‌های واجد شرایطی که به دلیل سابقه یا تازگی ناکافی NAV تحلیل نشدند.
    کدهای_تحلیل_شده = set(نتیجه["scheme_code"].astype(str))
    تحلیل_نشده = واجد_شرایط[
        ~واجد_شرایط["scheme_code"].astype(str).isin(کدهای_تحلیل_شده)
    ]
    فهرست_تحلیل_نشده = [
        {
            "scheme_code": str(ردیف["scheme_code"]),
            "scheme_name": str(ردیف["scheme_name"]),
            "fund_group": str(ردیف["fund_group"]),
            "reason": "تاریخچه NAV برای محاسبه شاخص‌های سه‌ساله کافی یا به‌روز نیست"
        }
        for _, ردیف in تحلیل_نشده.iterrows()
    ]

    تعداد_ETF = int(واجد_شرایط["is_etf"].sum()) if "is_etf" in واجد_شرایط.columns else 0
    تعداد_غیر_ETF = int(len(واجد_شرایط) - تعداد_ETF)
    from zoneinfo import ZoneInfo
    زمان_هند = datetime.now(ZoneInfo("Asia/Kolkata")).isoformat()

    خروجی = {
        "updated_at_utc": datetime.now(timezone.utc).isoformat(),
        "updated_at_india": زمان_هند,
        "metrics_as_of": تاریخ_شاخص,
        "source_funds": int(همه_صندوق_ها["scheme_code"].nunique()),
        "eligible_funds": int(واجد_شرایط["scheme_code"].nunique()),
        "etf_funds": تعداد_ETF,
        "non_etf_funds": تعداد_غیر_ETF,
        "etf_classification_method": "تشخیص از نام رسمی طرح AMFI؛ طرح‌های ETF Fund of Fund در گروه غیر ETF قرار می‌گیرند",
        "analyzed_funds": int(نتیجه["scheme_code"].nunique()),
        "not_analyzed_count": int(len(تحلیل_نشده)),
        "not_analyzed_funds": فهرست_تحلیل_نشده,
        "funds_with_metrics": int(نتیجه["scheme_code"].nunique()),
        "funds_with_nav": int(nav["scheme_code"].nunique()),
        "nav_funds_received": int(nav["scheme_code"].nunique()),
        "alpha_received": int(نتیجه["alpha"].notna().sum()),
        "beta_received": int(نتیجه["beta"].notna().sum()),
        "alpha_beta_errors": [
            {"scheme_code": str(ردیف["scheme_code"]), "error": str(ردیف["alpha_beta_error"])}
            for _, ردیف in خطاهای_آلفا_بتا.iterrows()
        ],
        "aum_available": int(نتیجه["aum_cr"].notna().sum()) if "aum_cr" in نتیجه.columns else 0,
        "aum_as_of": str(نتیجه["aum_as_of"].dropna().max()) if "aum_as_of" in نتیجه.columns and not نتیجه["aum_as_of"].dropna().empty else "نامشخص",
        "group_counts": {str(k): int(v) for k, v in آمار_گروه.items()},
        "results": json.loads(نتیجه.to_json(orient="records", force_ascii=False, date_format="iso"))
    }

    مسیر = Path("data/latest_snapshot.json")
    مسیر.parent.mkdir(parents=True, exist_ok=True)
    مسیر.write_text(json.dumps(خروجی, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Snapshot saved: {مسیر}; metrics date: {تاریخ_شاخص}; rows: {len(نتیجه)}")


if __name__ == "__main__":
    main()
