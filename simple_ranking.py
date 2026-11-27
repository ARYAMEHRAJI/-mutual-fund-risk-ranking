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

        # ترجیح نوع دارایی نیز روشن و قابل توضیح است:
        # محافظه‌کار به درآمد ثابت و ریسک‌پذیر به سهام وزن بیشتری می‌دهد.
        گروه_متنی = داده["fund_group"].astype(str)
        درآمد_ثابت = گروه_متنی.str.startswith("Debt")
        سهامی = گروه_متنی.str.startswith("Equity")
        ترکیبی = گروه_متنی.str.startswith("Hybrid")

        تعدیل = {
            "Conservative": (10, 5, -10),
            "Moderate": (5, 5, 0),
            "Growth": (-5, 0, 5),
            "Aggressive": (-10, -5, 10)
        }
        امتیاز_درآمد_ثابت, امتیاز_ترکیبی, امتیاز_سهامی = تعدیل[پروفایل]

        # کمی از امتیاز نسبی کم می‌کنیم و سپس ترجیح نوع دارایی را اضافه می‌کنیم.
        # این روش از جمع شدن امتیازها بالاتر از ۱۰۰ جلوگیری می‌کند.
        امتیاز_نهایی = داده[پروفایل + "_score"] * 0.9
        امتیاز_نهایی = امتیاز_نهایی + درآمد_ثابت.astype(int) * امتیاز_درآمد_ثابت
        امتیاز_نهایی = امتیاز_نهایی + ترکیبی.astype(int) * امتیاز_ترکیبی
        امتیاز_نهایی = امتیاز_نهایی + سهامی.astype(int) * امتیاز_سهامی
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



def انتخاب_صندوق_های_متنوع(جدول, ستون_امتیاز, تعداد=5, حداکثر_از_هر_گروه=2):
    """پنج صندوق با امتیاز بالا انتخاب می‌کند و تا حد ممکن تنوع گروهی را حفظ می‌کند."""
    if جدول.empty or ستون_امتیاز not in جدول.columns:
        return جدول.head(0).copy()

    داده = جدول.dropna(subset=[ستون_امتیاز]).copy()
    داده = داده.sort_values(ستون_امتیاز, ascending=False, kind="mergesort")
    if "fund_group" not in داده.columns:
        return داده.head(تعداد).reset_index(drop=True)

    انتخاب = []
    شمارش = {}
    باقی = []
    for _, ردیف in داده.iterrows():
        گروه = str(ردیف.get("fund_group", "نامشخص"))
        if شمارش.get(گروه, 0) < حداکثر_از_هر_گروه and len(انتخاب) < تعداد:
            انتخاب.append(ردیف)
            شمارش[گروه] = شمارش.get(گروه, 0) + 1
        else:
            باقی.append(ردیف)

    # اگر تعداد گروه‌های موجود برای رعایت سقف کافی نبود، فهرست را تا تعداد درخواستی کامل می‌کنیم.
    if len(انتخاب) < تعداد:
        for ردیف in باقی:
            انتخاب.append(ردیف)
            if len(انتخاب) == تعداد:
                break

    if not انتخاب:
        return داده.head(تعداد).reset_index(drop=True)
    return pd.DataFrame(انتخاب).reset_index(drop=True)
