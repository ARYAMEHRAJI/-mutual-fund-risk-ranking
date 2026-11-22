# داشبورد فارسی پیشنهاد صندوق بر اساس میزان ریسک پذیری کاربر

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from simple_data import دریافت_صندوق_ها, انتخاب_صندوق_ها, دریافت_nav
from simple_metrics import محاسبه_شاخص_ها, دریافت_آلفا_بتا_از_سرویس
from simple_ranking import رتبه_بندی

st.set_page_config(
    page_title="صندوق‌یار | پیشنهاد هوشمند صندوق",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ظاهر جدید: پس زمینه روشن، کارت های سفید، رنگ سرمه ای و فیروزه ای
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Vazirmatn:wght@300;400;500;600;700;800;900&display=swap');

:root {
    --ink: #17233b;
    --muted: #6b7890;
    --primary: #3157d5;
    --teal: #10a99a;
    --line: #e8edf5;
    --surface: #ffffff;
}
html, body, [class*="css"], button, input, textarea, select {
    font-family: 'Vazirmatn', sans-serif !important;
}
[data-testid="stAppViewContainer"] {
    background: #f4f7fb;
    direction: rtl;
}
[data-testid="stHeader"] { background: rgba(244,247,251,.88); }
.block-container {
    max-width: 1440px;
    padding-top: 1.4rem;
    padding-bottom: 3rem;
}
h1, h2, h3, h4, p, label, li { font-family: 'Vazirmatn', sans-serif !important; }
h1, h2, h3 { color: var(--ink); letter-spacing: -.35px; }
[data-testid="stMarkdownContainer"] p { color: #526078; line-height: 1.9; }
.hero {
    background: linear-gradient(120deg, #17233b 0%, #263f78 58%, #236e80 100%);
    border-radius: 26px;
    padding: 34px 38px;
    color: white;
    margin: 4px 0 26px 0;
    box-shadow: 0 18px 40px rgba(31,54,103,.16);
}
.hero-kicker { color: #9fe8e0; font-size: 13px; font-weight: 700; letter-spacing: .5px; }
.hero h1 { color: white !important; font-size: 32px !important; font-weight: 850 !important; margin: 8px 0 6px 0; }
.hero p { color: #e2eaf8 !important; font-size: 15px; margin: 0; }
.section-title {
    color: #17233b; font-size: 21px; font-weight: 800;
    margin: 12px 0 5px 0;
}
.section-subtitle { color: #758198; font-size: 13px; margin-bottom: 16px; }
div[data-testid="stVerticalBlockBorderWrapper"] {
    border: 1px solid #e7edf5 !important;
    border-radius: 18px !important;
    background: white;
    box-shadow: 0 5px 18px rgba(25,45,80,.035);
}
div.stButton > button {
    border-radius: 12px;
    border: 0;
    min-height: 48px;
    font-weight: 750;
    background: linear-gradient(100deg, #3157d5, #277d9b);
    color: white;
    box-shadow: 0 7px 18px rgba(49,87,213,.18);
}
div.stButton > button:hover { color: white; border: 0; filter: brightness(1.06); }
[data-testid="stRadio"] > label { font-weight: 700; color: #25334d; }
[data-testid="stRadio"] div[role="radiogroup"] { gap: 7px; }
[data-testid="stRadio"] div[role="radiogroup"] label {
    background: #f8faff; border: 1px solid #e8edf5;
    border-radius: 11px; padding: 9px 13px; margin: 0;
}
[data-testid="stRadio"] div[role="radiogroup"] label:hover { border-color: #9aafea; }
div[data-testid="stMetric"] {
    background: white; border: 1px solid #e7edf5;
    padding: 15px 18px; border-radius: 16px;
}
div[data-testid="stMetricLabel"] { color: #758198; }
div[data-testid="stMetricValue"] { color: #1b315b; font-weight: 800; }
.fund-card {
    background: white; border: 1px solid #e7edf5;
    border-radius: 17px; padding: 17px 19px; margin: 9px 0;
}
.fund-rank {
    display: inline-flex; width: 34px; height: 34px;
    border-radius: 11px; align-items: center; justify-content: center;
    color: #fff; font-weight: 800;
    background: linear-gradient(135deg,#3157d5,#10a99a);
}
.fund-name { color: #1d2c49; font-size: 14px; font-weight: 750; line-height: 1.8; }
.fund-score { color: #3157d5; font-weight: 800; font-size: 14px; }
.chart-card {
    background: white; border: 1px solid #e7edf5;
    border-radius: 18px; padding: 15px 15px 4px 15px;
}
div[data-testid="stTabs"] button { font-family: 'Vazirmatn', sans-serif !important; font-weight: 700; }
[data-testid="stDataFrame"] { border: 1px solid #e7edf5; border-radius: 14px; overflow: hidden; }
hr { border-color: #e7edf5; }
.small-note { color: #8994a8; font-size: 12px; line-height: 1.8; }
footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
  <div class="hero-kicker">SMART MUTUAL FUND FINDER</div>
  <h1>صندوق مناسب خودت رو پیدا کن</h1>
  <p>چند سؤال کوتاه جواب بده؛ صندوق‌ها رو بر اساس میزان ریسک‌پذیریت بررسی و مقایسه می‌کنیم.</p>
</div>
""", unsafe_allow_html=True)

سوال_ها = [
    {
        "سوال": "۱. اگر ارزش سرمایه‌ات در یک ماه ۱۵ درصد کم شود، چه واکنشی نشان می‌دهی؟",
        "گزینه": [
            "احتمالاً سرمایه‌ام را می‌فروشم تا ضرر بیشتری نکنم.",
            "نگران می‌شوم و شاید بخشی از سرمایه را خارج کنم.",
            "صبر می‌کنم تا شرایط بازار بهتر شود.",
            "اگر پول اضافه داشته باشم، ممکن است بیشتر سرمایه‌گذاری کنم."
        ]
    },
    {
        "سوال": "۲. چه مدت می‌توانی پولت را سرمایه‌گذاری کنی؟",
        "گزینه": ["کمتر از یک سال", "بین یک تا سه سال", "بین سه تا پنج سال", "بیشتر از پنج سال"]
    },
    {
        "سوال": "۳. کدام مورد برایت مهم‌تر است؟",
        "گزینه": [
            "حفظ اصل پول و دوری از نوسان",
            "تعادل بین حفظ سرمایه و کسب سود",
            "کسب سود بیشتر با پذیرش مقداری ریسک",
            "بیشترین بازده ممکن، حتی با نوسان زیاد"
        ]
    },
    {
        "سوال": "۴. اگر سرمایه‌گذاری‌ات برای مدتی وارد ضرر شود، چه می‌کنی؟",
        "گزینه": [
            "ترجیح می‌دهم سریع از آن خارج شوم.",
            "بخشی را نگه می‌دارم و بخشی را می‌فروشم.",
            "برای مدتی صبر می‌کنم.",
            "اگر به آینده آن اطمینان داشته باشم، ممکن است بیشتر بخرم."
        ]
    }
]

st.markdown('<div class="section-title">آزمون شناخت ریسک‌پذیری</div>', unsafe_allow_html=True)
st.markdown('<div class="section-subtitle">پاسخی را انتخاب کن که به رفتار واقعی تو نزدیک‌تر است؛ دانش بورسی لازم نیست.</div>', unsafe_allow_html=True)

پاسخ_ها = []
ستون_سوال = st.columns(2)
for شماره, سوال in enumerate(سوال_ها):
    with ستون_سوال[شماره % 2]:
        with st.container(border=True):
            پاسخ = st.radio(
                سوال["سوال"], سوال["گزینه"],
                key="سوال_ریسک_" + str(شماره),
                index=None
            )
            پاسخ_ها.append(
                سوال["گزینه"].index(پاسخ) if پاسخ is not None else None
            )

if st.button("تحلیل پاسخ‌ها و نمایش صندوق‌های پیشنهادی", type="primary", use_container_width=True):
    if any(پاسخ is None for پاسخ in پاسخ_ها):
        st.warning("برای مشخص شدن سطح ریسک‌پذیری، لطفاً به هر چهار سؤال پاسخ بده.")
    else:
        امتیاز = sum(پاسخ_ها) / len(پاسخ_ها)
        if امتیاز <= 0.75:
            سطح, پروفایل = "محافظه‌کار", "Conservative"
            توضیح = "حفظ سرمایه و کاهش نوسان برای شما اهمیت بیشتری دارد."
        elif امتیاز <= 1.5:
            سطح, پروفایل = "متوسط", "Moderate"
            توضیح = "به دنبال تعادل بین بازدهی و ریسک هستید و نوسان محدود را می‌پذیرید."
        elif امتیاز <= 2.25:
            سطح, پروفایل = "رشدگرا", "Growth"
            توضیح = "برای کسب بازدهی بیشتر، پذیرای نوسان و افت مقطعی سرمایه هستید."
        else:
            سطح, پروفایل = "ریسک‌پذیر", "Aggressive"
            توضیح = "نوسان‌های بیشتر را تحمل می‌کنید و به دنبال بازدهی بالاتر در بلندمدت هستید."
        st.session_state["سطح_ریسک"] = سطح
        st.session_state["پروفایل"] = پروفایل
        st.session_state["توضیح_ریسک"] = توضیح
        st.session_state["شروع_تحلیل"] = True
        st.session_state["نمایش_نتیجه"] = False

if st.session_state.get("شروع_تحلیل", False):
    st.markdown("---")
    st.markdown('<div class="section-title">نتیجه ارزیابی شما</div>', unsafe_allow_html=True)
    c1, c2 = st.columns([1, 3])
    with c1:
        st.metric("سطح ریسک‌پذیری", st.session_state["سطح_ریسک"])
    with c2:
        st.info(st.session_state["توضیح_ریسک"])
    st.caption("این آزمون صرفاً آموزشی است و جایگزین مشاوره مالی یا بررسی شرایط شخصی شما نیست.")

    if st.button("پیدا کردن ۵ صندوق مناسب من", type="primary", use_container_width=True):
        try:
            with st.spinner("در حال دریافت داده‌ها و تحلیل صندوق‌ها..."):
                همه_صندوق_ها = دریافت_صندوق_ها()
                گروه_ها = ["Large Cap", "Mid Cap", "Small Cap", "Flexi Cap", "Multi Cap", "Focused"]
                انتخاب_ها = []
                for گروه in گروه_ها:
                    انتخاب_ها.append(انتخاب_صندوق_ها(همه_صندوق_ها, گروه).head(5))
                صندوق_های_انتخابی = pd.concat(انتخاب_ها, ignore_index=True).drop_duplicates("scheme_code")

                if صندوق_های_انتخابی.empty:
                    raise RuntimeError("صندوق واجد شرایطی در داده دریافتی پیدا نشد.")

                # شمارش کل فهرست و صندوق های واجد شرایط در شش گروه
                تعداد_کل_دریافتی = int(همه_صندوق_ها["scheme_code"].nunique())
                صندوق_های_واجد_شرایط = pd.concat(
                    [انتخاب_صندوق_ها(همه_صندوق_ها, گروه) for گروه in گروه_ها],
                    ignore_index=True
                ).drop_duplicates("scheme_code")

                # برای کنترل زمان دریافت NAV، پنج صندوق از هر گروه وارد بررسی عمیق می شوند.
                صندوق_های_انتخابی["benchmark"] = ""
                نگاشت_گروه = {
                    "Large Cap": "NIFTY 50",
                    "Mid Cap": "NIFTY MIDCAP 150",
                    "Small Cap": "NIFTY SMALLCAP 250",
                    "Flexi Cap": "NIFTY 500",
                    "Multi Cap": "NIFTY 500",
                    "Focused": "NIFTY 500"
                }
                for گروه in گروه_ها:
                    کدها = انتخاب_صندوق_ها(همه_صندوق_ها, گروه).head(5)["scheme_code"]
                    صندوق_های_انتخابی.loc[
                        صندوق_های_انتخابی["scheme_code"].isin(کدها), "benchmark"
                    ] = نگاشت_گروه[گروه]

                nav = دریافت_nav(صندوق_های_انتخابی["scheme_code"].tolist())
                تعداد_دارای_nav = int(nav["scheme_code"].nunique())
                شاخص_ها = محاسبه_شاخص_ها(nav)

                # آلفا و بتا از سرویس مستقل دریافت می شوند؛ دیگر به دریافت Nifty/Yahoo وابسته نیستند.
                جدول_آلفا_بتا = دریافت_آلفا_بتا_از_سرویس(
                    شاخص_ها["scheme_code"].astype(str).tolist(),
                    افق="3Y"
                )
                شاخص_ها["scheme_code"] = شاخص_ها["scheme_code"].astype(str)
                جدول_آلفا_بتا["scheme_code"] = جدول_آلفا_بتا["scheme_code"].astype(str)
                شاخص_ها = شاخص_ها.merge(جدول_آلفا_بتا, on="scheme_code", how="left")

                خطاهای_آلفا_بتا = [
                    str(ردیف["scheme_code"]) + ": " + str(ردیف["alpha_beta_error"])
                    for _, ردیف in جدول_آلفا_بتا.iterrows()
                    if str(ردیف.get("alpha_beta_error", "")).strip()
                ]
                منابع_شاخص = [{
                    "source": "Charlie Alpha API",
                    "horizon": "3Y",
                    "benchmark": "شاخص مرجع اختصاصی هر صندوق",
                    "data_as_of": (
                        جدول_آلفا_بتا["alpha_beta_as_of"].dropna().iloc[0]
                        if not جدول_آلفا_بتا["alpha_beta_as_of"].dropna().empty else "نامشخص"
                    )
                }]
                تعداد_تحلیل_شده = int(شاخص_ها["scheme_code"].nunique())
                تعداد_آلفا_کل = int(شاخص_ها["alpha"].notna().sum())
                تعداد_بتا_کل = int(شاخص_ها["beta"].notna().sum())
                تعداد_واجد_شرایط = int(صندوق_های_واجد_شرایط["scheme_code"].nunique())

                نتیجه = رتبه_بندی(شاخص_ها)
                ستون_رتبه = st.session_state["پروفایل"] + "_rank"
                نتیجه = نتیجه.sort_values(ستون_رتبه).head(5).reset_index(drop=True)
                st.session_state["نتیجه_صندوق"] = نتیجه
                st.session_state["خطاهای_آلفا_بتا"] = خطاهای_آلفا_بتا
                st.session_state["منابع_شاخص"] = منابع_شاخص
                st.session_state["تعداد_کل_دریافتی"] = تعداد_کل_دریافتی
                st.session_state["تعداد_واجد_شرایط"] = تعداد_واجد_شرایط
                st.session_state["تعداد_بررسی_شده"] = تعداد_تحلیل_شده
                st.session_state["تعداد_دارای_nav"] = تعداد_دارای_nav
                st.session_state["تعداد_آلفا_کل"] = تعداد_آلفا_کل
                st.session_state["تعداد_بتا_کل"] = تعداد_بتا_کل
                st.session_state["نمایش_نتیجه"] = True
        except Exception as خطا:
            st.error("در تحلیل داده‌ها مشکلی پیش آمد: " + str(خطا))

if st.session_state.get("نمایش_نتیجه", False):
    نتیجه = st.session_state["نتیجه_صندوق"].copy()
    پروفایل = st.session_state["پروفایل"]

    st.markdown("---")
    st.markdown('<div class="section-title">۵ صندوق برتر متناسب با شما</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-subtitle">رتبه‌ها بر اساس امتیاز مدل آموزشی پروژه محاسبه شده‌اند.</div>', unsafe_allow_html=True)

    تعداد_دارای_آلفا = int(نتیجه["alpha"].notna().sum()) if "alpha" in نتیجه.columns else 0
    تعداد_دارای_بتا = int(نتیجه["beta"].notna().sum()) if "beta" in نتیجه.columns else 0
    # آمار شفاف از کل داده تا انتخاب پنج صندوق نهایی
    st.markdown("**آمار فرایند انتخاب صندوق‌ها**")
    آمار_۱, آمار_۲, آمار_۳ = st.columns(3)
    آمار_۱.metric("صندوق دریافت‌شده از منبع", st.session_state.get("تعداد_کل_دریافتی", "—"))
    آمار_۲.metric("صندوق واجد شرایط در گروه‌ها", st.session_state.get("تعداد_واجد_شرایط", "—"))
    آمار_۳.metric("صندوق بررسی عمیق‌شده", st.session_state.get("تعداد_بررسی_شده", "—"))
    آمار_۴, آمار_۵, آمار_۶ = st.columns(3)
    آمار_۴.metric("صندوق دارای NAV", st.session_state.get("تعداد_دارای_nav", "—"))
    آمار_۵.metric("آلفای دریافت‌شده در بررسی", st.session_state.get("تعداد_آلفا_کل", "—"))
    آمار_۶.metric("بتای دریافت‌شده در بررسی", st.session_state.get("تعداد_بتا_کل", "—"))
    st.caption(
        "در ۵ صندوق نهایی: آلفا برای " + str(تعداد_دارای_آلفا) + " صندوق و بتا برای "
        + str(تعداد_دارای_بتا) + " صندوق دریافت شده است. برای کنترل زمان دریافت NAV، "
        "حداکثر ۵ صندوق از هر یک از ۶ گروه (تا ۳۰ صندوق) وارد بررسی عمیق می‌شوند."
    )

    for شماره, ردیف in نتیجه.iterrows():
        امتیاز_صندوق = ردیف.get(پروفایل + "_score", float("nan"))
        st.markdown(
            '<div class="fund-card"><span class="fund-rank">' + str(شماره + 1)
            + '</span> <span class="fund-name">' + str(ردیف["scheme_name"])
            + '</span><div class="fund-score">امتیاز تناسب: '
            + (("{:.1f}".format(امتیاز_صندوق)) if pd.notna(امتیاز_صندوق) else "—")
            + ' از ۱۰۰</div></div>',
            unsafe_allow_html=True
        )

    if تعداد_دارای_آلفا == 0 or تعداد_دارای_بتا == 0:
        st.warning("برای بخشی از صندوق‌ها آلفا یا بتا از سرویس دریافت نشده است. جزئیات خطا و منبع را در بخش «اطلاعات داده‌ها» ببینید.")

    st.markdown("---")
    st.markdown('<div class="section-title">مقایسه عملکرد صندوق‌ها</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-subtitle">نمودارهای افقی با نام کامل صندوق و عدد دقیق؛ برای مقایسه راحت‌تر می‌توانید شاخص‌ها را از تب‌های زیر انتخاب کنید.</div>', unsafe_allow_html=True)

    نام_شاخص_ها = {
        "return_1w": ("بازدهی ۱ هفته", "درصد تغییر ارزش صندوق طی یک هفته اخیر.", True, "%"),
        "return_1m": ("بازدهی ۱ ماه", "درصد تغییر ارزش صندوق طی یک ماه اخیر.", True, "%"),
        "return_3m": ("بازدهی ۳ ماه", "درصد تغییر ارزش صندوق طی سه ماه اخیر.", True, "%"),
        "return_6m": ("بازدهی ۶ ماه", "درصد تغییر ارزش صندوق طی شش ماه اخیر.", True, "%"),
        "return_1y": ("بازدهی ۱ سال", "درصد تغییر ارزش صندوق طی یک سال اخیر.", True, "%"),
        "return_3y": ("بازدهی ۳ سال", "بازدهی تجمعی سه‌ساله با فرض سرمایه‌گذاری مجدد سود.", True, "%"),
        "volatility": ("نوسان‌پذیری", "نوسان سالانه بازدهی روزانه؛ مقدار کمتر یعنی نوسان کمتر.", True, "%"),
        "max_drawdown": ("بیشترین افت سرمایه", "بزرگ‌ترین افت از قله قبلی تا کف بعدی؛ عدد نزدیک‌تر به صفر بهتر است.", True, "%"),
        "sharpe": ("نسبت شارپ", "بازدهی مازاد به ازای هر واحد نوسان؛ مقدار بالاتر معمولاً بهتر است.", False, ""),
        "sortino": ("نسبت سورتینو", "مانند شارپ است، اما ریسک نزولی را در نظر می‌گیرد.", False, ""),
        "alpha": ("آلفا", "آلفای سالانه سه‌ساله نسبت به شاخص مرجع همان صندوق؛ از Charlie Alpha API دریافت شده است.", True, "%"),
        "beta": ("بتا", "بتای سه‌ساله نسبت به شاخص مرجع همان صندوق؛ نزدیک ۱ یعنی حرکت تقریباً هم‌اندازه شاخص.", False, "")
    }

    def نمایش_نمودار(ستون):
        عنوان, توضیح, درصدی, پسوند = نام_شاخص_ها[ستون]
        داده = نتیجه[["scheme_name", ستون]].copy()
        داده[ستون] = pd.to_numeric(داده[ستون], errors="coerce")
        داده = داده.dropna().sort_values(ستون, ascending=True)
        if داده.empty:
            st.info("برای این شاخص داده قابل نمایش در دسترس نیست.")
            return
        if درصدی:
            داده[ستون] = داده[ستون] * 100
        اعداد = داده[ستون].round(2)
        رنگ‌ها = ["#a8b6d8", "#879bd0", "#6883c8", "#4770bd", "#18a999"]
        شکل = go.Figure()
        شکل.add_trace(go.Bar(
            x=داده[ستون],
            y=داده["scheme_name"],
            orientation="h",
            marker=dict(color=رنگ‌ها[-len(داده):], line=dict(width=0)),
            text=[("{:,.2f}".format(x) + پسوند) for x in اعداد],
            textposition="outside",
            cliponaxis=False,
            hovertemplate="<b>%{y}</b><br>" + عنوان + ": %{x:,.2f}" + پسوند + "<extra></extra>"
        ))
        شکل.update_layout(
            height=max(300, 74 * len(داده) + 90),
            margin=dict(l=12, r=85, t=18, b=48),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Vazirmatn, sans-serif", size=12, color="#526078"),
            showlegend=False,
            bargap=.42,
            xaxis=dict(
                title=عنوان + (" (" + پسوند + ")" if پسوند else ""),
                showgrid=True, gridcolor="#edf1f7", zerolinecolor="#dce3ef",
                tickfont=dict(size=11)
            ),
            yaxis=dict(
                title="", automargin=True, tickfont=dict(size=11, color="#293954"),
                showgrid=False
            )
        )
        with st.container(border=True):
            st.markdown("**" + عنوان + "**")
            st.caption(توضیح)
            st.plotly_chart(
                شکل,
                use_container_width=True,
                config={"displayModeBar": False}
            )

    تب_بازدهی, تب_ریسک, تب_کیفیت, تب_بازار = st.tabs(["بازدهی", "ریسک", "کیفیت عملکرد", "آلفا و بتا"])
    with تب_بازدهی:
        for ستون in ["return_1w", "return_1m", "return_3m", "return_6m", "return_1y", "return_3y"]:
            نمایش_نمودار(ستون)
    with تب_ریسک:
        نمایش_نمودار("volatility")
        نمایش_نمودار("max_drawdown")
    with تب_کیفیت:
        نمایش_نمودار("sharpe")
        نمایش_نمودار("sortino")
    with تب_بازار:
        st.info("آلفا و بتا برای بازه سه‌ساله از Charlie Alpha API دریافت می‌شوند. این سرویس برای هر صندوق، شاخص مرجع مرتبط با همان طرح را در محاسبات خود لحاظ می‌کند.")
        نمایش_نمودار("alpha")
        نمایش_نمودار("beta")

    st.markdown("---")
    تب_جدول, تب_منابع = st.tabs(["جدول مقایسه", "اطلاعات داده‌ها"])
    with تب_جدول:
        ستون_های_جدول = ["scheme_name"] + list(نام_شاخص_ها.keys())
        جدول = نتیجه[[x for x in ستون_های_جدول if x in نتیجه.columns]].copy()
        جدول = جدول.rename(columns={"scheme_name": "نام صندوق", **{k: v[0] for k, v in نام_شاخص_ها.items()}})
        st.dataframe(جدول, use_container_width=True, hide_index=True)
        st.download_button(
            "دانلود جدول مقایسه (CSV)",
            data=جدول.to_csv(index=False).encode("utf-8-sig"),
            file_name="fund_comparison.csv",
            mime="text/csv"
        )
    with تب_منابع:
        st.markdown("**منبع آلفا و بتا**")
        st.write("Charlie Alpha API — محاسبه سه‌ساله با شاخص مرجع مرتبط با هر صندوق.")
        st.markdown("[مشاهده مستندات و API منبع](https://api.charliealpha.in/)")
        تاریخ_داده = (
            نتیجه["alpha_beta_as_of"].dropna().iloc[0]
            if "alpha_beta_as_of" in نتیجه.columns and not نتیجه["alpha_beta_as_of"].dropna().empty
            else "در دسترس نیست"
        )
        st.write("تاریخ داده آلفا و بتا: " + str(تاریخ_داده))
        if "alpha_beta_benchmark" in نتیجه.columns:
            جدول_منبع = نتیجه[[
                "scheme_name", "alpha_beta_benchmark", "alpha", "beta"
            ]].copy()
            جدول_منبع = جدول_منبع.rename(columns={
                "scheme_name": "نام صندوق",
                "alpha_beta_benchmark": "شاخص مرجع",
                "alpha": "آلفای سالانه سه‌ساله (درصد)",
                "beta": "بتای سه‌ساله"
            })
            جدول_منبع["آلفای سالانه سه‌ساله (درصد)"] = (
                جدول_منبع["آلفای سالانه سه‌ساله (درصد)"] * 100
            )
            st.dataframe(جدول_منبع, use_container_width=True, hide_index=True)
        for خطا in st.session_state.get("خطاهای_آلفا_بتا", []):
            st.warning("دریافت آلفا/بتا برای یک صندوق ناموفق بود: " + خطا)

st.markdown("---")
st.markdown(
    '<div class="small-note">این سامانه یک پروژه آموزشی برای مقایسه صندوق‌های سرمایه‌گذاری است و توصیه خرید یا فروش محسوب نمی‌شود. داده‌های صندوق از Tigzig و آلفا و بتا از Charlie Alpha API دریافت می‌شوند.</div>',
    unsafe_allow_html=True
)
