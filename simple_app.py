# داشبورد ساده پیشنهاد صندوق بر اساس میزان ریسک پذیری کاربر

import streamlit as st
import pandas as pd
import altair as alt

from simple_data import دریافت_صندوق_ها, انتخاب_صندوق_ها, دریافت_nav
from simple_metrics import (
    محاسبه_شاخص_ها, دریافت_شاخص_بازار, محاسبه_آلفا_بتا
)
from simple_ranking import رتبه_بندی

st.set_page_config(
    page_title="پیشنهادگر صندوق سرمایه گذاری",
    page_icon="📊",
    layout="wide"
)

# ظاهر فارسی و راست چین داشبورد
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Vazirmatn:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"], button, input, textarea, select {
    font-family: 'Vazirmatn', sans-serif !important;
    direction: rtl;
    text-align: right;
}
[data-testid="stAppViewContainer"] {
    direction: rtl;
}
[data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] li {
    text-align: right;
}
div[data-testid="stRadio"] label {
    direction: rtl;
}
.block-container {
    max-width: 1200px;
    padding-top: 2rem;
}
h1, h2, h3 {
    text-align: right;
    font-family: 'Vazirmatn', sans-serif !important;
}
[data-testid="stDataFrame"], [data-testid="stTable"] {
    direction: rtl;
}
</style>
""", unsafe_allow_html=True)

st.title("پیدا کردن صندوق مناسب شما")
st.write(
    "به چند سؤال ساده پاسخ دهید تا میزان ریسک پذیری شما مشخص شود. "
    "سپس پنج صندوق متناسب با پاسخ های شما را بررسی و مقایسه می کنیم."
)
st.info(
    "برای پاسخ دادن به این سؤال ها به دانش بورسی نیاز ندارید. "
    "فقط گزینه ای را انتخاب کنید که بیشتر به رفتار واقعی شما نزدیک است."
)

# چهار سؤال ساده برای شناخت رفتار سرمایه گذار
st.subheader("آزمون شناخت ریسک پذیری")

پاسخ_ها = []

سوال_ها = [
    {
        "سوال": "۱. اگر ارزش سرمایه شما در یک ماه ۱۵ درصد کم شود، چه واکنشی نشان می دهید؟",
        "گزینه": [
            "احتمالاً سرمایه ام را می فروشم تا ضرر بیشتری نکنم.",
            "نگران می شوم و شاید بخشی از سرمایه را خارج کنم.",
            "صبر می کنم تا شرایط بازار بهتر شود.",
            "اگر پول اضافه داشته باشم، ممکن است بیشتر سرمایه گذاری کنم."
        ]
    },
    {
        "سوال": "۲. چه مدت می توانید پول خود را سرمایه گذاری کنید؟",
        "گزینه": [
            "کمتر از یک سال",
            "بین یک تا سه سال",
            "بین سه تا پنج سال",
            "بیشتر از پنج سال"
        ]
    },
    {
        "سوال": "۳. کدام مورد برای شما مهم تر است؟",
        "گزینه": [
            "حفظ اصل پول و دوری از نوسان",
            "تعادل بین حفظ سرمایه و کسب سود",
            "کسب سود بیشتر با پذیرش مقداری ریسک",
            "بیشترین بازده ممکن، حتی با نوسان زیاد"
        ]
    },
    {
        "سوال": "۴. اگر سرمایه گذاری شما برای مدتی وارد ضرر شود، چه می کنید؟",
        "گزینه": [
            "ترجیح می دهم سریع از آن خارج شوم.",
            "بخشی را نگه می دارم و بخشی را می فروشم.",
            "برای مدتی صبر می کنم.",
            "اگر به آینده آن اطمینان داشته باشم، ممکن است بیشتر بخرم."
        ]
    }
]

for سوال in سوال_ها:
    پاسخ = st.radio(
        سوال["سوال"],
        سوال["گزینه"],
        key=سوال["سوال"]
    )
    پاسخ_ها.append(سوال["گزینه"].index(پاسخ))

if st.button("مشاهده نتیجه و صندوق های پیشنهادی", type="primary", use_container_width=True):
    # میانگین امتیاز پاسخ ها، سطح ریسک را مشخص می کند
    امتیاز = sum(پاسخ_ها) / len(پاسخ_ها)

    if امتیاز <= 0.75:
        سطح_ریسک = "محافظه کار"
        پروفایل = "Conservative"
        توضیح_ریسک = "معمولاً حفظ سرمایه و کاهش نوسان برای شما مهم تر از کسب سود بسیار زیاد است."
    elif امتیاز <= 1.5:
        سطح_ریسک = "متوسط"
        پروفایل = "Moderate"
        توضیح_ریسک = "شما به دنبال تعادل بین بازدهی و ریسک هستید و نوسان محدود را می پذیرید."
    elif امتیاز <= 2.25:
        سطح_ریسک = "رشدگرا"
        پروفایل = "Growth"
        توضیح_ریسک = "برای کسب بازدهی بیشتر، حاضر به پذیرش نوسان و افت مقطعی سرمایه هستید."
    else:
        سطح_ریسک = "ریسک پذیر"
        پروفایل = "Aggressive"
        توضیح_ریسک = "شما نوسان های زیاد را بهتر تحمل می کنید و به دنبال بازدهی بالاتر در بلندمدت هستید."

    st.session_state["سطح_ریسک"] = سطح_ریسک
    st.session_state["پروفایل"] = پروفایل
    st.session_state["توضیح_ریسک"] = توضیح_ریسک
    st.session_state["شروع_تحلیل"] = True

if st.session_state.get("شروع_تحلیل", False):
    st.divider()
    st.subheader("نتیجه آزمون شما")
    st.success("سطح ریسک پذیری شما: " + st.session_state["سطح_ریسک"])
    st.write(st.session_state["توضیح_ریسک"])
    st.caption(
        "این نتیجه یک ارزیابی آموزشی بر اساس پاسخ های شماست و جایگزین "
        "مشاوره مالی یا بررسی شرایط شخصی شما نیست."
    )

    if st.button("پیدا کردن صندوق های مناسب من", type="primary", use_container_width=True):
        try:
            with st.spinner("در حال دریافت فهرست صندوق های سرمایه گذاری..."):
                همه_صندوق_ها = دریافت_صندوق_ها()

                # کاربر گروه صندوق را انتخاب نمی کند؛ برنامه خودش گروه ها را بررسی می کند
                گروه_ها = [
                    "Large Cap", "Mid Cap", "Small Cap",
                    "Flexi Cap", "Multi Cap", "Focused"
                ]
                فهرست_انتخابی = []

                for گروه in گروه_ها:
                    صندوق_های_گروه = انتخاب_صندوق_ها(همه_صندوق_ها, گروه)
                    فهرست_انتخابی.append(صندوق_های_گروه.head(5))

                صندوق_های_انتخابی = pd.concat(
                    فهرست_انتخابی, ignore_index=True
                ).drop_duplicates(subset=["scheme_code"])

            if صندوق_های_انتخابی.empty:
                st.error("در حال حاضر صندوق مناسبی در اطلاعات دریافتی پیدا نشد.")
            else:
                # برای هر گروه، شاخص مرجع مناسب را مشخص می کنیم
                شاخص_مرجع = {
                    "Large Cap": "NIFTY 50 TRI",
                    "Mid Cap": "NIFTY MIDCAP 150 TRI",
                    "Small Cap": "NIFTY SMALLCAP 250 TRI",
                    "Flexi Cap": "NIFTY 500 TRI",
                    "Multi Cap": "NIFTY 500 TRI",
                    "Focused": "NIFTY 500 TRI"
                }
                صندوق_های_انتخابی["benchmark"] = ""
                for گروه in گروه_ها:
                    کدها = انتخاب_صندوق_ها(همه_صندوق_ها, گروه)["scheme_code"]
                    صندوق_های_انتخابی.loc[
                        صندوق_های_انتخابی["scheme_code"].isin(کدها),
                        "benchmark"
                    ] = شاخص_مرجع[گروه]

                with st.spinner("در حال دریافت اطلاعات صندوق ها و محاسبه شاخص ها..."):
                    nav = دریافت_nav(
                        صندوق_های_انتخابی["scheme_code"].tolist()
                    )
                    شاخص_ها = محاسبه_شاخص_ها(nav)

                    # آلفا و بتا با شاخص کل بازدهی متناسب با گروه صندوق حساب می شوند
                    نتیجه_آلفا_بتا = []
                    for نام_شاخص in صندوق_های_انتخابی["benchmark"].dropna().unique():
                        کدهای_این_گروه = صندوق_های_انتخابی.loc[
                            صندوق_های_انتخابی["benchmark"] == نام_شاخص,
                            "scheme_code"
                        ].tolist()
                        nav_این_گروه = nav[nav["scheme_code"].isin(کدهای_این_گروه)]
                        try:
                            شاخص_بازار = دریافت_شاخص_بازار(
                                نام_شاخص,
                                nav_این_گروه["date"].min(),
                                nav_این_گروه["date"].max()
                            )
                            آلفا_بتا = محاسبه_آلفا_بتا(nav_این_گروه, شاخص_بازار)
                            نتیجه_آلفا_بتا.append(آلفا_بتا)
                        except Exception:
                            # اگر منبع شاخص در دسترس نبود، مقدارها خالی می مانند
                            continue

                    if نتیجه_آلفا_بتا:
                        جدول_آلفا_بتا = pd.concat(
                            نتیجه_آلفا_بتا, ignore_index=True
                        ).drop_duplicates(subset=["scheme_code"])
                        شاخص_ها = شاخص_ها.merge(
                            جدول_آلفا_بتا, on="scheme_code", how="left"
                        )
                    else:
                        شاخص_ها["alpha"] = float("nan")
                        شاخص_ها["beta"] = float("nan")

                    نتیجه = رتبه_بندی(شاخص_ها)

                ستون_رتبه = st.session_state["پروفایل"] + "_rank"
                نتیجه = نتیجه.sort_values(ستون_رتبه).head(5).reset_index(drop=True)

                # نام فارسی شاخص ها برای نمایش ساده تر
                نام_شاخص_ها = {
                    "return_1w": "بازدهی یک هفته",
                    "return_1m": "بازدهی یک ماه",
                    "return_3m": "بازدهی سه ماه",
                    "return_6m": "بازدهی شش ماه",
                    "return_1y": "بازدهی یک سال",
                    "return_3y": "بازدهی سه سال",
                    "volatility": "نوسان پذیری",
                    "max_drawdown": "بیشترین افت سرمایه",
                    "sharpe": "نسبت شارپ",
                    "sortino": "نسبت سورتینو",
                    "alpha": "آلفا",
                    "beta": "بتا"
                }

                st.session_state["نتیجه_صندوق"] = نتیجه
                st.session_state["نام_شاخص_ها"] = نام_شاخص_ها
                st.session_state["نمایش_نتیجه"] = True

        except Exception as خطا:
            st.error("هنگام دریافت یا تحلیل اطلاعات مشکلی پیش آمد: " + str(خطا))

if st.session_state.get("نمایش_نتیجه", False):
    نتیجه = st.session_state["نتیجه_صندوق"]
    نام_شاخص_ها = st.session_state["نام_شاخص_ها"]

    st.divider()
    st.subheader("پنج صندوق پیشنهادی برای شما")
    st.write(
        "صندوق ها بر اساس سطح ریسک شما مرتب شده اند. "
        "رتبه ۱ یعنی بالاترین امتیاز در مدل رتبه بندی این پروژه."
    )

    for شماره, ردیف in نتیجه.iterrows():
        with st.container(border=True):
            ستون_ها = st.columns([1, 5])
            ستون_ها[0].metric("رتبه", str(شماره + 1))
            ستون_ها[1].markdown("**" + str(ردیف["scheme_name"]) + "**")
            st.caption(
                "امتیاز متناسب با شما: "
                + str(round(ردیف[st.session_state["پروفایل"] + "_score"], 1))
                + " از ۱۰۰"
            )

    st.divider()
    st.subheader("مقایسه پنج صندوق پیشنهادی")
    st.write(
        "در نمودارهای زیر می توانید عملکرد هر پنج صندوق را کنار هم ببینید. "
        "برای هر شاخص، توضیح ساده هم نوشته شده است."
    )

    توضیح_شاخص_ها = {
        "return_1w": "درصد تغییر ارزش صندوق در یک هفته اخیر. برای شناخت وضعیت کوتاه مدت است و به تنهایی معیار تصمیم گیری نیست.",
        "return_1m": "درصد تغییر ارزش صندوق در یک ماه اخیر.",
        "return_3m": "درصد تغییر ارزش صندوق در سه ماه اخیر.",
        "return_6m": "درصد تغییر ارزش صندوق در شش ماه اخیر.",
        "return_1y": "درصد تغییر ارزش صندوق در یک سال اخیر.",
        "return_3y": "درصد رشد ارزش سرمایه در سه سال اخیر؛ فرض می شود سود در صندوق باقی مانده و دوباره سرمایه گذاری شده است.",
        "volatility": "نشان می دهد بازدهی صندوق چقدر بالا و پایین می شود. مقدار کمتر معمولاً به معنی نوسان کمتر است.",
        "max_drawdown": "بیشترین افت ارزش صندوق از یک قله قبلی تا کف بعدی. افت کمتر معمولاً بهتر است.",
        "sharpe": "نشان می دهد صندوق در برابر ریسکی که پذیرفته، چه میزان بازدهی داشته است. مقدار بالاتر معمولاً بهتر است.",
        "sortino": "مانند شارپ است، اما بیشتر روی نوسان های منفی تمرکز می کند. مقدار بالاتر معمولاً بهتر است.",
        "alpha": "بازدهی اضافه صندوق نسبت به بازدهی مورد انتظار بر اساس شاخص بازار. مقدار مثبت می تواند نشانه عملکرد بهتر باشد.",
        "beta": "میزان حساسیت صندوق به بالا و پایین رفتن شاخص بازار. بتای نزدیک ۱ یعنی حرکت تقریباً هم اندازه شاخص."
    }

    ستون_های_نمایش = [
        "return_1w", "return_1m", "return_3m",
        "return_6m", "return_1y", "return_3y",
        "volatility", "max_drawdown", "sharpe", "sortino",
        "alpha", "beta"
    ]

    for ستون in ستون_های_نمایش:
        if ستون not in نتیجه.columns:
            continue

        st.markdown("### " + نام_شاخص_ها[ستون])
        st.write(توضیح_شاخص_ها[ستون])

        if ستون in ["alpha", "beta"] and نتیجه[ستون].isna().all():
            st.warning(
                "داده معتبر این شاخص در حال حاضر از منبع بازار دریافت نشده است؛ "
                "برای جلوگیری از نمایش عدد نادرست، نمودار آن نشان داده نمی شود."
            )
            continue

        داده_نمودار = نتیجه[["scheme_name", ستون]].copy()
        داده_نمودار[ستون] = pd.to_numeric(داده_نمودار[ستون], errors="coerce")
        داده_نمودار = داده_نمودار.dropna()
        if داده_نمودار.empty:
            st.info("برای این شاخص هنوز داده قابل نمایش وجود ندارد.")
            continue

        if ستون in [
            "return_1w", "return_1m", "return_3m",
            "return_6m", "return_1y", "return_3y",
            "volatility", "max_drawdown", "alpha"
        ]:
            داده_نمودار[ستون] = داده_نمودار[ستون] * 100
            st.caption("مقادیر به درصد نمایش داده شده اند.")

        داده_نمودار = داده_نمودار.rename(columns={ستون: "value"})
        داده_نمودار["label"] = داده_نمودار["value"].map(
            lambda مقدار: "{:,.2f}".format(مقدار)
        )

        # نمودار افقی باعث می شود نام کامل صندوق و مقدار هر میله خوانا باشد
        ارتفاع = max(190, len(داده_نمودار) * 55)
        میله = alt.Chart(داده_نمودار).mark_bar(
            cornerRadiusEnd=5,
            height=25
        ).encode(
            x=alt.X("value:Q", title=نام_شاخص_ها[ستون]),
            y=alt.Y(
                "scheme_name:N",
                sort="-x",
                title=None,
                axis=alt.Axis(labelLimit=600, labelFontSize=11)
            ),
            tooltip=[
                alt.Tooltip("scheme_name:N", title="نام صندوق"),
                alt.Tooltip("value:Q", title=نام_شاخص_ها[ستون], format=".2f")
            ]
        )
        برچسب = alt.Chart(داده_نمودار).mark_text(
            align="left",
            baseline="middle",
            dx=5,
            fontSize=11
        ).encode(
            x="value:Q",
            y=alt.Y("scheme_name:N", sort="-x"),
            text="label:N"
        )
        نمودار = (میله + برچسب).properties(
            height=ارتفاع,
            padding={"left": 5, "right": 25}
        ).configure_view(
            strokeOpacity=0
        ).configure_axis(
            labelFont="Vazirmatn",
            titleFont="Vazirmatn"
        )
        st.altair_chart(نمودار, use_container_width=True)

    st.divider()
    st.subheader("جدول کامل مقایسه")
    جدول = نتیجه[
        ["scheme_name"] + ستون_های_نمایش
    ].copy()
    جدول = جدول.rename(columns={
        "scheme_name": "نام صندوق",
        **نام_شاخص_ها
    })
    st.dataframe(جدول, use_container_width=True, hide_index=True)

    خروجی = جدول.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        "دانلود جدول مقایسه",
        data=خروجی,
        file_name="fund_comparison.csv",
        mime="text/csv"
    )

st.divider()
st.caption(
    "این سامانه یک پروژه آموزشی برای مقایسه صندوق های سرمایه گذاری است "
    "و توصیه خرید یا فروش محسوب نمی شود. داده ها از API منبع ثالث دریافت می شوند."
)
