# این فایل به صندوق ها امتیاز می دهد و آن ها را برای چهار نوع سرمایه گذار مرتب می کند.

import pandas as pd


def تبدیل_به_امتیاز(جدول, ستون, بیشتر_بهتر=True):
    # مقدار بهتر باید امتیاز بالاتری بگیرد.
    رتبه = جدول[ستون].rank(pct=True, ascending=بیشتر_بهتر)
    return رتبه * 100


def رتبه_بندی(جدول):
    داده = جدول.copy()

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

    # ۲) در شاخص های ریسک، مقدار کمتر بهتر است.
    داده["volatility_score"] = تبدیل_به_امتیاز(
        داده, "volatility", بیشتر_بهتر=False
    )
    داده["drawdown_score"] = تبدیل_به_امتیاز(
        داده, "max_drawdown", بیشتر_بهتر=True
    )
    داده["risk_score"] = داده[
        ["volatility_score", "drawdown_score"]
    ].mean(axis=1)

    # ۳) در شاخص های کیفیت عملکرد، مقدار بالاتر بهتر است.
    for ستون in ["sharpe", "sortino", "alpha"]:
        داده[ستون + "_score"] = تبدیل_به_امتیاز(داده, ستون)

    داده["quality_score"] = داده[
        ["sharpe_score", "sortino_score", "alpha_score"]
    ].mean(axis=1)

    # ۴) وزن بازدهی، ریسک و کیفیت برای هر پروفایل.
    وزن_ها = {
        "Conservative": [20, 50, 30],
        "Moderate": [40, 30, 30],
        "Growth": [55, 20, 25],
        "Aggressive": [65, 10, 25]
    }

    # اگر یک بخش داده نداشته باشد، وزن آن بین بخش های موجود پخش می شود.
    ستون_ها = ["return_score", "risk_score", "quality_score"]
    for پروفایل, وزن in وزن_ها.items():
        امتیازها = داده[ستون_ها]
        وزن_های_موجود = امتیازها.notna().mul(وزن, axis=1)
        مجموع_وزن = وزن_های_موجود.sum(axis=1)
        مجموع_امتیاز = امتیازها.mul(وزن, axis=1).sum(axis=1, min_count=1)

        داده[پروفایل + "_score"] = مجموع_امتیاز / مجموع_وزن.where(مجموع_وزن != 0)
        داده[پروفایل + "_rank"] = داده[پروفایل + "_score"].rank(
            ascending=False, method="min"
        )

    return داده.sort_values("Moderate_rank")
