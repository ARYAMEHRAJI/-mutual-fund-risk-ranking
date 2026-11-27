# رتبه‌بندی ساده و قابل توضیح صندوق‌ها در مقایسه با هم‌گروهی‌هایشان

import pandas as pd


def تبدیل_به_امتیاز(جدول, ستون, بیشتر_بهتر=True):
    مقدارها = pd.to_numeric(جدول[ستون], errors="coerce")
    تعداد = مقدارها.notna().sum()

    if تعداد == 0:
        return pd.Series(float("nan"), index=جدول.index)

    # در گروه کوچک، امتیاز را به عدد میانی ۵۰ نزدیک می‌کنیم تا نتیجه افراطی نشود.
    if تعداد == 1:
        return pd.Series(50.0, index=جدول.index).where(مقدارها.notna())

    امتیاز_خام = مقدارها.rank(pct=True, ascending=بیشتر_بهتر, method="average") * 100
    ضریب_اعتماد = تعداد / (تعداد + 10)
    return 50 + (امتیاز_خام - 50) * ضریب_اعتماد


def تعدیل_نوع_دارایی(گروه, پروفایل):
    """امتیاز تناسب نوع صندوق؛ یک فرض آموزشی و قابل توضیح است."""
    گروه = str(گروه)

    if گروه.startswith("Debt") or گروه == "Other - Debt Index":
        return {"Conservative": 10, "Moderate": 3, "Growth": -5, "Aggressive": -10}[پروفایل]

    if گروه.startswith("Equity") or گروه == "Other - Index":
        return {"Conservative": -10, "Moderate": 3, "Growth": 7, "Aggressive": 10}[پروفایل]

    if گروه.startswith("Hybrid"):
        زیرگروه = گروه.split(" - ", 1)[-1]
        جدول = {
            "Conservative": {
                "Conservative": 8, "Balanced": 5, "Aggressive": -8,
                "Arbitrage": 8, "Dynamic Allocation": 3,
                "Multi Asset": 3, "Equity Savings": 2
            },
            "Moderate": {
                "Conservative": 3, "Balanced": 8, "Aggressive": 4,
                "Arbitrage": 5, "Dynamic Allocation": 6,
                "Multi Asset": 6, "Equity Savings": 5
            },
            "Growth": {
                "Conservative": -2, "Balanced": 3, "Aggressive": 7,
                "Arbitrage": 1, "Dynamic Allocation": 5,
                "Multi Asset": 6, "Equity Savings": 5
            },
            "Aggressive": {
                "Conservative": -5, "Balanced": 2, "Aggressive": 10,
                "Arbitrage": 1, "Dynamic Allocation": 5,
                "Multi Asset": 7, "Equity Savings": 6
            }
        }
        return جدول[پروفایل].get(زیرگروه, 0)

    if گروه == "Other - Gold":
        return {"Conservative": 1, "Moderate": 3, "Growth": 5, "Aggressive": 5}[پروفایل]

    if گروه == "Other - Silver":
        return {"Conservative": -4, "Moderate": 2, "Growth": 6, "Aggressive": 7}[پروفایل]

    return 0


def امتیازدهی_یک_گروه(گروه):
    داده = گروه.copy()

    # فقط بازدهی یک‌ساله و سه‌ساله وارد امتیاز می‌شود؛
    # بازه‌های کوتاه‌تر برای نمایش هستند تا یک روند چند بار شمرده نشود.
    داده["return_score"] = pd.concat([
        تبدیل_به_امتیاز(داده, "return_1y"),
        تبدیل_به_امتیاز(داده, "return_3y")
    ], axis=1).mean(axis=1)

    # نوسان کمتر و افت سرمایه نزدیک‌تر به صفر بهتر است.
    داده["volatility_score"] = تبدیل_به_امتیاز(
        داده, "volatility", بیشتر_بهتر=False
    )
    داده["drawdown_score"] = تبدیل_به_امتیاز(
        داده, "max_drawdown", بیشتر_بهتر=True
    )
    داده["risk_score"] = داده[
        ["volatility_score", "drawdown_score"]
    ].mean(axis=1)

    # کیفیت عملکرد با شارپ و سورتینو سنجیده می‌شود.
    داده["sharpe_score"] = تبدیل_به_امتیاز(داده, "sharpe")
    داده["sortino_score"] = تبدیل_به_امتیاز(داده, "sortino")
    داده["quality_score"] = داده[
        ["sharpe_score", "sortino_score"]
    ].mean(axis=1)

    # AUM معیار مکمل اندازه صندوق است؛ رتبه آن فقط درون همان گروه محاسبه می‌شود.
    if "aum_cr" not in داده.columns:
        داده["aum_cr"] = float("nan")
    داده["size_score"] = تبدیل_به_امتیاز(داده, "aum_cr")

    # برای رتبه‌بندی، بازدهی بلندمدت، ریسک و کیفیت باید قابل محاسبه باشند.
    داده["data_coverage"] = داده[
        ["return_1w", "return_1m", "return_3m", "return_6m",
         "return_1y", "return_3y", "volatility", "max_drawdown",
         "sharpe", "sortino", "aum_cr"]
    ].notna().mean(axis=1) * 100

    داده["eligible_for_ranking"] = (
        داده["return_1y"].notna()
        & داده["return_3y"].notna()
        & داده["volatility"].notna()
        & داده["max_drawdown"].notna()
        & داده["quality_score"].notna()
    )

    # وزن‌های مدل برای هر سطح ریسک.
    وزن_ها = {
        "Conservative": [18, 45, 27, 10],
        "Moderate": [36, 27, 27, 10],
        "Growth": [49.5, 18, 22.5, 10],
        "Aggressive": [58.5, 9, 22.5, 10]
    }

    ستون_ها = ["return_score", "risk_score", "quality_score", "size_score"]
    for پروفایل, وزن in وزن_ها.items():
        امتیازها = داده[ستون_ها]
        وزن_های_موجود = امتیازها.notna().mul(وزن, axis=1)
        مجموع_وزن = وزن_های_موجود.sum(axis=1)
        مجموع_امتیاز = امتیازها.mul(وزن, axis=1).sum(axis=1, min_count=1)
        داده[پروفایل + "_score"] = مجموع_امتیاز / مجموع_وزن.where(مجموع_وزن != 0)

        # تعدیل نوع دارایی را با توجه به زیرگروه هم انجام می‌دهیم؛
        # برای نمونه، مختلط تهاجمی برای کاربر محافظه‌کار امتیاز منفی می‌گیرد.
        تعدیل_ها = داده["fund_group"].apply(
            lambda گروه: تعدیل_نوع_دارایی(گروه, پروفایل)
        )

        # ۹۰ درصد امتیاز از شاخص‌های محاسبه‌شده و ۱۰ درصد از تناسب نوع دارایی است.
        امتیاز_نهایی = داده[پروفایل + "_score"] * 0.9 + تعدیل_ها
        داده[پروفایل + "_score"] = امتیاز_نهایی.clip(0, 100)

        داده.loc[~داده["eligible_for_ranking"], پروفایل + "_score"] = float("nan")

    return داده


def رتبه_بندی(جدول, ستون_گروه="fund_group"):
    داده = جدول.copy()

    if ستون_گروه not in داده.columns:
        raise ValueError("ستون گروه صندوق برای رتبه‌بندی لازم است.")

    if داده.empty:
        raise ValueError("داده‌ای برای رتبه‌بندی وجود ندارد.")

    بخش_ها = []
    for _, گروه in داده.groupby(ستون_گروه, dropna=False):
        بخش_ها.append(امتیازدهی_یک_گروه(گروه))

    نتیجه = pd.concat(بخش_ها, ignore_index=True)

    for پروفایل in ["Conservative", "Moderate", "Growth", "Aggressive"]:
        نتیجه[پروفایل + "_rank"] = نتیجه[پروفایل + "_score"].rank(
            ascending=False, method="min"
        )

    return نتیجه.sort_values("Moderate_rank", na_position="last").reset_index(drop=True)



def دسته_دارایی(گروه):
    """گروه‌های اصلی دارایی را برای متنوع‌سازی مشخص می‌کند."""
    گروه = str(گروه)
    if گروه.startswith("Debt") or گروه == "Other - Debt Index":
        return "debt"
    if گروه.startswith("Hybrid"):
        return "hybrid"
    if گروه.startswith("Equity") or گروه == "Other - Index":
        return "equity"
    if گروه in ["Other - Gold", "Other - Silver"]:
        return "alternative"
    return "other"



def محاسبه_وزن_سبد(جدول, پروفایل):
    """وزن پیشنهادی صندوق‌ها را بر اساس ریسک و نوع دارایی محاسبه می‌کند."""
    if جدول.empty:
        نتیجه = جدول.copy()
        نتیجه["portfolio_weight"] = []
        return نتیجه

    # درصد هدف هر نوع دارایی برای هر سطح ریسک
    وزن_هدف = {
        "Conservative": {"debt": 65, "hybrid": 30, "equity": 5, "alternative": 0, "other": 0},
        "Moderate": {"debt": 25, "hybrid": 30, "equity": 35, "alternative": 10, "other": 0},
        "Growth": {"debt": 10, "hybrid": 15, "equity": 60, "alternative": 15, "other": 0},
        "Aggressive": {"debt": 5, "hybrid": 10, "equity": 70, "alternative": 15, "other": 0}
    }

    هدف = وزن_هدف.get(پروفایل, وزن_هدف["Moderate"])
    نتیجه = جدول.copy()
    انواع = [دسته_دارایی(گروه) for گروه in نتیجه["fund_group"]]

    # فقط وزن گروه‌هایی را نگه می‌داریم که در پنج پیشنهاد حضور دارند.
    وزن_موجود = sum(هدف.get(نوع, 0) for نوع in set(انواع))
    تعداد_هر_نوع = {}
    for نوع in انواع:
        تعداد_هر_نوع[نوع] = تعداد_هر_نوع.get(نوع, 0) + 1

    if وزن_موجود == 0:
        وزن_خام = [100 / len(انواع)] * len(انواع)
    else:
        وزن_خام = [
            هدف.get(نوع, 0) / وزن_موجود / تعداد_هر_نوع[نوع] * 100
            for نوع in انواع
        ]

    # گرد کردن به یک رقم اعشار، طوری که مجموع دقیقاً ۱۰۰ درصد بماند.
    واحدها = [int(وزن * 10) for وزن in وزن_خام]
    باقی_مانده = 1000 - sum(واحدها)
    ترتیب = sorted(
        range(len(واحدها)),
        key=lambda شماره: وزن_خام[شماره] * 10 - واحدها[شماره],
        reverse=True
    )
    for شماره in ترتیب[:باقی_مانده]:
        واحدها[شماره] += 1

    نتیجه["portfolio_weight"] = [واحد / 10 for واحد in واحدها]
    return نتیجه

def صنعت_صندوق(نام):
    """برای جلوگیری از پیشنهاد چند صندوق از یک صنعت، کلیدواژه‌های رایج را می‌سنجد."""
    نام = str(نام).lower()
    صنایع = {
        "healthcare": ["health", "healthcare", "pharma", "medical"],
        "banking": ["bank", "banking", "financial"],
        "technology": ["technology", "tech", "it fund", "software"],
        "energy": ["energy", "power", "oil", "gas"],
        "infrastructure": ["infrastructure", "construction"],
        "consumption": ["consumption", "consumer", "fmcg"],
        "auto": ["automobile", "auto"],
        "real_estate": ["realty", "real estate"],
        "metal": ["metal", "mining", "commodity"]
    }
    for صنعت, واژه_ها in صنایع.items():
        if any(واژه in نام for واژه in واژه_ها):
            return صنعت
    return ""


def انتخاب_صندوق_های_متنوع(
    جدول, ستون_امتیاز, تعداد=5, حداکثر_از_هر_گروه=1, پروفایل="Moderate"
):
    """
    انتخاب صندوق با حفظ تنوع دارایی و صنعت.
    امتیازها همچنان درون هر گروه محاسبه می‌شوند؛ این تابع فقط ترکیب پیشنهادها را متنوع می‌کند.
    """
    if جدول.empty or ستون_امتیاز not in جدول.columns:
        return جدول.head(0).copy()

    داده = جدول.dropna(subset=[ستون_امتیاز]).copy()
    داده = داده.sort_values(ستون_امتیاز, ascending=False, kind="mergesort")
    if داده.empty:
        return داده

    سقف_دارایی = {
        "Conservative": {"debt": 3, "hybrid": 2, "equity": 1, "alternative": 1, "other": 1},
        "Moderate": {"debt": 2, "hybrid": 2, "equity": 2, "alternative": 1, "other": 1},
        "Growth": {"debt": 1, "hybrid": 2, "equity": 3, "alternative": 1, "other": 1},
        "Aggressive": {"debt": 1, "hybrid": 1, "equity": 3, "alternative": 2, "other": 1}
    }
    سقف = سقف_دارایی.get(پروفایل, سقف_دارایی["Moderate"])
    انتخاب = []
    شمارش_دارایی = {}
    شمارش_گروه = {}
    شمارش_صنعت = {}
    تعداد_متمرکز = 0

    def افزودن(ردیف, محدودیت_صنعت, محدودیت_گروه, محدودیت_دارایی):
        nonlocal تعداد_متمرکز
        گروه = str(ردیف.get("fund_group", "نامشخص"))
        دارایی = دسته_دارایی(گروه)
        نام = ردیف.get("scheme_name", "")
        صنعت = صنعت_صندوق(نام)
        بخشی = گروه in ["Equity - Sectoral", "Equity - Thematic"]

        if محدودیت_دارایی and شمارش_دارایی.get(دارایی, 0) >= سقف.get(دارایی, 1):
            return False
        if محدودیت_گروه and شمارش_گروه.get(گروه, 0) >= حداکثر_از_هر_گروه:
            return False
        if محدودیت_صنعت and صنعت and شمارش_صنعت.get(صنعت, 0) >= 1:
            return False
        # صندوق‌های بخشی، موضوعی و صندوق‌های متمرکز بر یک صنعت را محدود می‌کنیم.
        # برای محافظه‌کار و متوسط حذف می‌شوند؛ برای دو پروفایل دیگر حداکثر یکی مجاز است.
        تمرکز_صنعتی = بخشی or bool(صنعت)
        if تمرکز_صنعتی and پروفایل in ["Conservative", "Moderate"]:
            return False
        if تمرکز_صنعتی and تعداد_متمرکز >= 1:
            return False

        انتخاب.append(ردیف)
        شمارش_دارایی[دارایی] = شمارش_دارایی.get(دارایی, 0) + 1
        شمارش_گروه[گروه] = شمارش_گروه.get(گروه, 0) + 1
        if صنعت:
            شمارش_صنعت[صنعت] = شمارش_صنعت.get(صنعت, 0) + 1
        if تمرکز_صنعتی:
            تعداد_متمرکز += 1
        return True

    # ابتدا همه محدودیت‌ها رعایت می‌شوند.
    for _, ردیف in داده.iterrows():
        if len(انتخاب) >= تعداد:
            break
        افزودن(ردیف, True, True, True)

    # اگر تعداد کافی نبود، فقط محدودیت صنعت و سپس گروه کمی آسان‌تر می‌شود.
    if len(انتخاب) < تعداد:
        انتخاب_شده = {str(ردیف.get("scheme_code", "")) for ردیف in انتخاب}
        for _, ردیف in داده.iterrows():
            if len(انتخاب) >= تعداد:
                break
            if str(ردیف.get("scheme_code", "")) in انتخاب_شده:
                continue
            if افزودن(ردیف, False, True, True):
                انتخاب_شده.add(str(ردیف.get("scheme_code", "")))

    if len(انتخاب) < تعداد:
        انتخاب_شده = {str(ردیف.get("scheme_code", "")) for ردیف in انتخاب}
        سقف_قدیمی = حداکثر_از_هر_گروه
        حداکثر_از_هر_گروه = max(2, سقف_قدیمی)
        for _, ردیف in داده.iterrows():
            if len(انتخاب) >= تعداد:
                break
            if str(ردیف.get("scheme_code", "")) in انتخاب_شده:
                continue
            if افزودن(ردیف, False, False, True):
                انتخاب_شده.add(str(ردیف.get("scheme_code", "")))

    # فقط در نبود گزینه کافی، سقف طبقه دارایی برداشته می‌شود تا پنج نتیجه نمایش داده شود.
    if len(انتخاب) < تعداد:
        انتخاب_شده = {str(ردیف.get("scheme_code", "")) for ردیف in انتخاب}
        for _, ردیف in داده.iterrows():
            if len(انتخاب) >= تعداد:
                break
            if str(ردیف.get("scheme_code", "")) in انتخاب_شده:
                continue
            افزودن(ردیف, False, False, False)

    return pd.DataFrame(انتخاب).reset_index(drop=True)
