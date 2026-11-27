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

    نتیجه = رتبه_بندی(شاخص_ها, ستون_گروه="fund_group")
    کدهای_نهایی = []
    for پروفایل in ["Conservative", "Moderate", "Growth", "Aggressive"]:
        بهترین = انتخاب_صندوق_های_متنوع(نتیجه, پروفایل + "_score", تعداد=5, حداکثر_از_هر_گروه=2)
        کدهای_نهایی.extend(بهترین["scheme_code"].astype(str).tolist())

    کدهای_نهایی = list(dict.fromkeys(کدهای_نهایی))
    print(f"دریافت آلفا و بتا برای {len(کدهای_نهایی)} صندوق منتخب...")
    آلفا_بتا = دریافت_آلفا_بتا_از_سرویس(کدهای_نهایی, افق="3Y")
    آلفا_بتا["scheme_code"] = آلفا_بتا["scheme_code"].astype(str).str.replace(r"\.0$", "", regex=True)
    نتیجه = نتیجه.merge(آلفا_بتا, on="scheme_code", how="left")

    for ستون in ["alpha", "beta"]:
        if ستون not in نتیجه.columns:
            نتیجه[ستون] = None

    تاریخ_شاخص = str(نتیجه["metrics_as_of"].dropna().max())
    آمار_گروه = واجد_شرایط.groupby("fund_group")["scheme_code"].nunique().to_dict()
    خروجی = {
        "updated_at_utc": datetime.now(timezone.utc).isoformat(),
        "metrics_as_of": تاریخ_شاخص,
        "source_funds": int(همه_صندوق_ها["scheme_code"].nunique()),
        "eligible_funds": int(واجد_شرایط["scheme_code"].nunique()),
        "analyzed_funds": int(نتیجه["scheme_code"].nunique()),
        "funds_with_metrics": int(نتیجه["scheme_code"].nunique()),
        "funds_with_nav": int(nav["scheme_code"].nunique()),
        "nav_funds_received": int(nav["scheme_code"].nunique()),
        "alpha_received": int(نتیجه["alpha"].notna().sum()),
        "beta_received": int(نتیجه["beta"].notna().sum()),
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
