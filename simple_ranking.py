# این فایل صندوق ها را در مقایسه با هم گروه هایشان امتیازدهی می کند.

import pandas as pd


def تبدیل_به_امتیاز(جدول, ستون, بیشتر_بهتر=True):
    # رتبه صدکی باعث می شود امتیاز هر صندوق فقط با هم گروهی هایش مقایسه شود.
    مقدارها = pd.to_numeric(جدول[ستون], errors="coerce")
    if مقدارها.notna().sum() <= 1:
        return pd.Series(50.0, index=جدول.index).where(مقدارها.notna())
    رتبه = مقدارها.rank(pct=True, ascending=بیشتر_بهتر, method="average")
    return رتبه * 100


def امتیازدهی_یک_گروه(گروه):
    داده = گروه.copy()

    # ۱) امتیاز بازدهی از میانگین رتبه شش بازه زمانی ساخته می شود.
    ستون_های_بازدهی = [
        "return_1w", "return_1m", "return_3m",
        "return_6m", "return_1y", "return_3y"
    ]
    for ستون in ستون_های_بازدهی:
        داده[ستون + "_score"] = تبدیل_به_امتیاز(داده, ستون)

    داده["return_score"] = داده[
        [ستون + "_score" for ستون in ستون_های_بازدهی]
    ].mean(axis=1)

    # ۲) در نوسان کمتر بهتر است؛ افت سرمایه نزدیک تر به صفر بهتر است.
    داده["volatility_score"] = تبدیل_به_امتیاز(
        داده, "volatility", بیشتر_بهتر=False
    )
    داده["drawdown_score"] = تبدیل_به_امتیاز(
        داده, "max_drawdown", بیشتر_بهتر=True
    )
    داده["risk_score"] = داده[
        ["volatility_score", "drawdown_score"]
    ].mean(axis=1)

    # ۳) کیفیت عملکرد با نسبت شارپ و سورتینو سنجیده می شود.
    for ستون in ["sharpe", "sortino"]:
        داده[ستون + "_score"] = تبدیل_به_امتیاز(داده, ستون)

    داده["quality_score"] = داده[
        ["sharpe_score", "sortino_score"]
    ].mean(axis=1)

    # ۴) وزن هر بخش برای چهار پروفایل سرمایه گذار.
    وزن_ها = {
        "Conservative": [20, 50, 30],
        "Moderate": [40, 30, 30],
        "Growth": [55, 20, 25],
        "Aggressive": [65, 10, 25]
    }

    ستون_ها = ["return_score", "risk_score", "quality_score"]
    for پروفایل, وزن in وزن_ها.items():
        امتیازها = داده[ستون_ها]
        وزن_های_موجود = امتیازها.notna().mul(وزن, axis=1)
        مجموع_وزن = وزن_های_موجود.sum(axis=1)
        مجموع_امتیاز = امتیازها.mul(وزن, axis=1).sum(axis=1, min_count=1)

        داده[پروفایل + "_score"] = مجموع_امتیاز / مجموع_وزن.where(مجموع_وزن != 0)

    return داده


def رتبه_بندی(جدول, ستون_گروه="fund_group"):
    داده = جدول.copy()

    if ستون_گروه not in داده.columns:
        raise ValueError("برای رتبه بندی درون گروهی، ستون گروه صندوق لازم است.")

    # هر گروه جداگانه امتیازدهی می شود؛ امتیازها سپس در مقیاس صفر تا صد قابل مقایسه اند.
    بخش_ها = []
    for نام_گروه, گروه in داده.groupby(ستون_گروه, dropna=False):
        بخش_امتیازدهی_شده = امتیازدهی_یک_گروه(گروه)
        بخش_ها.append(بخش_امتیازدهی_شده)

    نتیجه = pd.concat(بخش_ها, ignore_index=True)

    # رتبه نهایی، رتبه امتیازهای نسبی بین گروه هاست؛ نه مقایسه مستقیم بازده خام.
    for پروفایل in ["Conservative", "Moderate", "Growth", "Aggressive"]:
        نتیجه[پروفایل + "_rank"] = نتیجه[پروفایل + "_score"].rank(
            ascending=False, method="min"
        )

    return نتیجه.sort_values("Moderate_rank")
