# این فایل صندوق ها را برای چهار نوع سرمایه گذار رتبه بندی می کند.

import pandas as pd


def تبدیل_به_امتیاز(جدول, ستون, بیشتر_بهتر=True):
    # هر صندوق را با صندوق های هم گروه خودش مقایسه می کنیم
    رتبه = جدول[ستون].rank(pct=True, ascending=بیشتر_بهتر)
    return رتبه * 100


def رتبه_بندی(جدول):
    داده = جدول.copy()

    # امتیاز بازدهی از میانگین رتبه شش بازه به دست می آید
    ستون_های_بازدهی = [
        "return_1w", "return_1m", "return_3m",
        "return_6m", "return_1y", "return_3y"
    ]

    امتیازهای_بازدهی = []
    for ستون in ستون_های_بازدهی:
        داده[ستون + "_score"] = تبدیل_به_امتیاز(داده, ستون, True)
        امتیازهای_بازدهی.append(ستون + "_score")

    داده["return_score"] = داده[امتیازهای_بازدهی].mean(axis=1)

    # برای ریسک، نوسان و افت کمتر امتیاز بهتری می گیرد
    داده["volatility_score"] = تبدیل_به_امتیاز(داده, "volatility", False)
    داده["drawdown_score"] = تبدیل_به_امتیاز(داده, "max_drawdown", True)

    # برای نسبت های شارپ، سورتینو و آلفا مقدار بیشتر بهتر است
    داده["sharpe_score"] = تبدیل_به_امتیاز(داده, "sharpe", True)
    داده["sortino_score"] = تبدیل_به_امتیاز(داده, "sortino", True)
    داده["alpha_score"] = تبدیل_به_امتیاز(داده, "alpha", True)

    # بتا در جدول نمایش داده می شود اما مستقیم امتیاز نمی گیرد؛
    # چون بتای بالاتر برای همه سرمایه گذاران بهتر یا بدتر نیست.
    داده["risk_score"] = داده[
        ["volatility_score", "drawdown_score"]
    ].mean(axis=1)

    داده["quality_score"] = داده[
        ["sharpe_score", "sortino_score", "alpha_score"]
    ].mean(axis=1)

    # وزن هر بخش برای هر نوع سرمایه گذار
    وزن_ها = {
        "Conservative": [20, 50, 30],
        "Moderate": [40, 30, 30],
        "Growth": [55, 20, 25],
        "Aggressive": [65, 10, 25]
    }

    # امتیاز نهایی را برای هر نوع سرمایه گذار حساب می کنیم
    for نام, وزن in وزن_ها.items():
        داده[نام + "_score"] = (
            داده["return_score"] * وزن[0]
            + داده["risk_score"] * وزن[1]
            + داده["quality_score"] * وزن[2]
        ) / 100

        داده[نام + "_rank"] = داده[نام + "_score"].rank(
            ascending=False, method="min"
        )

    return داده.sort_values("Moderate_rank")
