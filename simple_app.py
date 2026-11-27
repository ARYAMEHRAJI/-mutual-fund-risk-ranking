# داشبورد فارسی پیشنهاد صندوق بر اساس میزان ریسک پذیری کاربر
# آلفا و بتا از سرویس Charlie Alpha دریافت می شوند.

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import html

from simple_data import دریافت_صندوق_ها, انتخاب_صندوق_ها, دریافت_nav, دریافت_دارایی_تحت_مدیریت
from simple_metrics import محاسبه_شاخص_ها, دریافت_آلفا_بتا_از_سرویس
from simple_ranking import رتبه_بندی
from simple_database import ذخیره_نتایج, آمار_پایگاه_داده


st.set_page_config(
    page_title="صندوق‌یار | پیشنهاد هوشمند صندوق",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed"
)


نام_فارسی_گروه_ها = {
    "Equity - Large Cap": "سهامی - شرکت‌های بزرگ",
    "Equity - Mid Cap": "سهامی - شرکت‌های متوسط",
    "Equity - Small Cap": "سهامی - شرکت‌های کوچک",
    "Equity - Flexi Cap": "سهامی - انعطاف‌پذیر",
    "Equity - Multi Cap": "سهامی - چندبخشی",
    "Equity - Focused": "سهامی - متمرکز",
    "Equity - Sectoral": "سهامی - بخشی",
    "Equity - Thematic": "سهامی - موضوعی",
    "Debt - Overnight": "درآمد ثابت - شب‌شمار",
    "Debt - Liquid": "درآمد ثابت - نقدشونده",
    "Debt - Ultra Short Duration": "درآمد ثابت - سررسید بسیار کوتاه",
    "Debt - Low Duration": "درآمد ثابت - سررسید کوتاه",
    "Debt - Money Market": "درآمد ثابت - بازار پول",
    "Debt - Short Duration": "درآمد ثابت - سررسید کوتاه‌مدت",
    "Debt - Medium Duration": "درآمد ثابت - سررسید متوسط",
    "Debt - Medium to Long Duration": "درآمد ثابت - سررسید متوسط تا بلند",
    "Debt - Long Duration": "درآمد ثابت - سررسید بلند",
    "Debt - Dynamic Bond": "درآمد ثابت - اوراق با مدیریت پویا",
    "Debt - Corporate Bond": "درآمد ثابت - اوراق شرکتی",
    "Debt - Credit Risk": "درآمد ثابت - ریسک اعتباری",
    "Debt - Banking and PSU": "درآمد ثابت - بانکی و دولتی",
    "Debt - Gilt": "درآمد ثابت - اوراق دولتی",
    "Debt - Gilt 10Y": "درآمد ثابت - اوراق دولتی با سررسید ۱۰ سال",
    "Debt - Floater": "درآمد ثابت - نرخ شناور",
    "Hybrid - Conservative": "مختلط - محافظه‌کارانه",
    "Hybrid - Balanced": "مختلط - متعادل",
    "Hybrid - Aggressive": "مختلط - تهاجمی",
    "Hybrid - Dynamic Allocation": "مختلط - تخصیص دارایی پویا",
    "Hybrid - Multi Asset": "مختلط - چنددارایی",
    "Hybrid - Equity Savings": "مختلط - پس‌انداز سهامی",
    "Hybrid - Arbitrage": "مختلط - آربیتراژ",
    "Other - Index": "شاخصی و ETF - دنبال‌کننده شاخص",
    "Other - Gold": "طلا - صندوق‌ها و ETFهای طلا",
    "Other - Silver": "نقره - صندوق‌ها و ETFهای نقره"
}

@st.cache_data(ttl=3600, show_spinner=False)
def دریافت_فهرست_ذخیره_شده():
    return دریافت_صندوق_ها()


@st.cache_data(ttl=3600, show_spinner=False)
def دریافت_nav_ذخیره_شده(کدها):
    return دریافت_nav(list(کدها))


@st.cache_data(ttl=86400, show_spinner=False)
def دریافت_آلفا_بتا_مقایسه_ذخیره_شده(کدها):
    return دریافت_آلفا_بتا_از_سرویس(list(کدها), افق="3Y")


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
[data-testid="stMarkdownContainer"],
[data-testid="stCaptionContainer"],
[data-testid="stAlert"],
[data-testid="stExpander"],
[data-testid="stWidgetLabel"],
[data-testid="stSelectbox"],
[data-testid="stRadio"],
[data-testid="stCheckbox"],
[data-testid="stMetric"],
[data-testid="stDataFrame"] {
    direction: rtl !important;
    text-align: right !important;
}
[data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] li,
[data-testid="stMarkdownContainer"] h1,
[data-testid="stMarkdownContainer"] h2,
[data-testid="stMarkdownContainer"] h3,
[data-testid="stMarkdownContainer"] h4,
[data-testid="stCaptionContainer"],
[data-testid="stAlert"] p,
[data-testid="stExpander"] p,
[data-testid="stWidgetLabel"] label {
    direction: rtl !important;
    text-align: right !important;
}
.fund-card { direction: rtl; text-align: right; }
.hero, .section-title, .section-subtitle { direction: rtl; text-align: right; }
[data-testid="stTabs"] [role="tab"] { direction: rtl !important; }
[data-testid="stExpander"] summary { direction: rtl !important; text-align: right !important; }
[data-testid="stDataFrame"] div[role="gridcell"],
[data-testid="stDataFrame"] div[role="columnheader"] {
    direction: rtl !important;
    text-align: right !important;
}
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


# منوی اصلی سامانه
صفحه_فعال = st.radio(
    "بخش موردنظر",
    ["پیشنهاد هوشمند صندوق", "مقایسه صندوق‌ها"],
    horizontal=True,
    key="انتخاب_بخش_اصلی",
    label_visibility="collapsed"
)

if صفحه_فعال == "مقایسه صندوق‌ها":
    st.markdown('<div class="section-title">مقایسه صندوق‌ها</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-subtitle">ابتدا دسته‌بندی را انتخاب کن و سپس صندوق موردنظرت را مشخص کن. '
        'امکان مقایسه حداکثر چهار صندوق وجود دارد.</div>',
        unsafe_allow_html=True
    )

    import json
    from pathlib import Path

    مسیر_داده_مقایسه = Path("data/latest_snapshot.json")
    if not مسیر_داده_مقایسه.exists():
        st.warning("هنوز داده روزانه‌ای برای مقایسه در دسترس نیست. پس از اجرای موفق به‌روزرسانی روزانه، این بخش فعال می‌شود.")
        st.stop()

    try:
        تصویر_مقایسه = json.loads(مسیر_داده_مقایسه.read_text(encoding="utf-8"))
        همه_صندوق_های_مقایسه = pd.DataFrame(تصویر_مقایسه.get("results", []))
    except Exception as خطای_خواندن:
        st.error("خواندن اطلاعات صندوق‌ها با مشکل روبه‌رو شد: " + str(خطای_خواندن))
        st.stop()

    if همه_صندوق_های_مقایسه.empty or "fund_group" not in همه_صندوق_های_مقایسه.columns:
        st.warning("اطلاعات دسته‌بندی صندوق‌ها در فایل داده موجود نیست.")
        st.stop()

    نام_فارسی_دسته_ها = نام_فارسی_گروه_ها

    گروه_های_موجود = sorted(
        [گروه for گروه in همه_صندوق_های_مقایسه["fund_group"].dropna().unique()],
        key=lambda گروه: نام_فارسی_دسته_ها.get(گروه, گروه)
    )
    گزینه_های_دسته = ["انتخاب دسته‌بندی"] + [
        نام_فارسی_دسته_ها.get(گروه, گروه) for گروه in گروه_های_موجود
    ]
    نگاشت_دسته_به_انگلیسی = {
        نام_فارسی_دسته_ها.get(گروه, گروه): گروه for گروه in گروه_های_موجود
    }

    # توضیح ساده انواع دسته‌بندی صندوق‌ها برای کاربران
    توضیح_دسته_ها = {
        "Equity - Large Cap": "سهامی شرکت‌های بزرگ: طبق دسته‌بندی هند، عمدتاً در ۱۰۰ شرکت اول بازار از نظر ارزش کل بازار سرمایه‌گذاری می‌کنند. این شرکت‌ها معمولاً بزرگ‌تر و شناخته‌شده‌ترند؛ اما صندوق همچنان در برابر افت بازار سهام ریسک دارد.",
        "Equity - Mid Cap": "سهامی شرکت‌های متوسط: عمدتاً در شرکت‌های رتبه ۱۰۱ تا ۲۵۰ بازار از نظر ارزش کل بازار سرمایه‌گذاری می‌کنند. ظرفیت رشد می‌تواند بیشتر باشد، اما معمولاً نوسان و ریسک آن‌ها نیز از شرکت‌های بزرگ بالاتر است.",
        "Equity - Small Cap": "سهامی شرکت‌های کوچک: عمدتاً در شرکت‌های رتبه ۲۵۱ به بعد بازار از نظر ارزش کل بازار سرمایه‌گذاری می‌کنند. امکان رشد زیاد است، اما این شرکت‌ها معمولاً در افت بازار آسیب‌پذیرتر و کم‌نقدشونده‌ترند.",
        "Equity - Flexi Cap": "سهامی با انعطاف در اندازه شرکت: مدیر صندوق می‌تواند بین شرکت‌های بزرگ، متوسط و کوچک جابه‌جا شود و محدود به یک اندازه خاص نیست. ترکیب دارایی با تشخیص مدیر تغییر می‌کند.",
        "Equity - Multi Cap": "سهامی چندبخشی: طبق قواعد این گروه، در شرکت‌های بزرگ، متوسط و کوچک سرمایه‌گذاری می‌کند. بنابراین سرمایه بین اندازه‌های مختلف شرکت‌ها پخش می‌شود.",
        "Equity - Focused": "سهامی متمرکز: تعداد محدودتری سهم (معمولاً حداکثر ۳۰ شرکت) در سبد دارد. تمرکز می‌تواند بازده را تقویت کند، اما ریسک وابستگی به چند شرکت را هم بالا می‌برد.",
        "Debt - Overnight": "درآمد ثابت شب‌شمار: عمدتاً در ابزارهای بدهی با سررسید یک‌روزه سرمایه‌گذاری می‌کند. برای نگهداری کوتاه‌مدت پول طراحی شده و معمولاً نوسان کمی دارد؛ اما بازده آن تضمین‌شده نیست.",
        "Debt - Liquid": "درآمد ثابت نقدشونده: در ابزارهای بدهی کوتاه‌مدت با سررسید بسیار نزدیک سرمایه‌گذاری می‌کند. هدف اصلی، نقدشوندگی بالا و نوسان پایین است.",
        "Debt - Ultra Short Duration": "درآمد ثابت با سررسید بسیار کوتاه: میانگین زمان دریافت جریان‌های نقدی دارایی‌ها کوتاه است. برای افق کوتاه‌مدت طراحی شده، اما ممکن است با تغییر نرخ بهره یا ریسک اعتباری نوسان کند.",
        "Debt - Low Duration": "درآمد ثابت با سررسید کوتاه: دارایی‌ها نسبت به گروه‌های بسیار کوتاه‌مدت، زمان بیشتری تا سررسید دارند. معمولاً ریسک نرخ بهره و بازده بالقوه آن کمی بالاتر است.",
        "Debt - Money Market": "درآمد ثابت بازار پول: در ابزارهای بازار پول مانند اوراق و سپرده‌های کوتاه‌مدت سرمایه‌گذاری می‌کند. هدف، حفظ نقدشوندگی و کسب درآمد نسبتاً باثبات است.",
        "Debt - Short Duration": "درآمد ثابت کوتاه‌مدت: در اوراق بدهی با مدت‌زمان کوتاه سرمایه‌گذاری می‌کند. نسبت به صندوق‌های شب‌شمار ممکن است نوسان بیشتری داشته باشد.",
        "Debt - Medium Duration": "درآمد ثابت با سررسید متوسط: ترکیبی از اوراق با مدت‌زمان متوسط نگهداری می‌کند. حساسیت آن به تغییر نرخ بهره از گروه‌های کوتاه‌مدت بیشتر است.",
        "Debt - Medium to Long Duration": "درآمد ثابت با سررسید متوسط تا بلند: در اوراقی با مدت‌زمان طولانی‌تر سرمایه‌گذاری می‌کند؛ بنابراین تغییر نرخ بهره می‌تواند اثر بیشتری بر قیمت اوراق و ارزش صندوق بگذارد.",
        "Debt - Long Duration": "درآمد ثابت بلندمدت: عمدتاً اوراق با سررسید بلند نگهداری می‌کند. ممکن است از کاهش نرخ بهره بیشتر منتفع شود، اما در صورت افزایش نرخ بهره نیز افت بیشتری تجربه کند.",
        "Debt - Dynamic Bond": "درآمد ثابت با مدیریت پویا: مدیر صندوق می‌تواند با توجه به شرایط بازار، سررسید اوراق را تغییر دهد. عملکرد آن به تصمیم‌های مدیر درباره نرخ بهره و بازار بدهی وابسته است.",
        "Debt - Corporate Bond": "درآمد ثابت اوراق شرکتی: بخش عمده دارایی را در اوراق بدهی شرکت‌ها با کیفیت اعتباری بالا سرمایه‌گذاری می‌کند. علاوه بر ریسک نرخ بهره، ریسک اعتباری ناشر نیز اهمیت دارد.",
        "Debt - Credit Risk": "درآمد ثابت با ریسک اعتباری: برای دستیابی به بازده بالاتر، ممکن است سهم بیشتری از اوراق با رتبه اعتباری پایین‌تر داشته باشد. احتمال نکول یا دشواری بازپرداخت در این گروه مهم‌تر است.",
        "Debt - Banking and PSU": "درآمد ثابت بانکی و نهادهای دولتی: عمدتاً در اوراق و ابزارهای منتشرشده توسط بانک‌ها، شرکت‌های دولتی و نهادهای عمومی سرمایه‌گذاری می‌کند.",
        "Debt - Gilt": "درآمد ثابت اوراق دولتی: دارایی اصلی آن اوراق قرضه دولت است. ریسک نکول دولت معمولاً پایین‌تر است، اما قیمت اوراق همچنان با تغییر نرخ بهره بالا و پایین می‌شود.",
        "Debt - Gilt 10Y": "درآمد ثابت اوراق دولتی ده‌ساله: عمدتاً روی اوراق دولتی با سررسید نزدیک به ۱۰ سال تمرکز دارد. به تغییر نرخ بهره حساسیت بالایی دارد و برای پولی که ممکن است زود لازم شود مناسب نیست.",
        "Debt - Floater": "درآمد ثابت با نرخ شناور: در اوراقی سرمایه‌گذاری می‌کند که نرخ سود آن‌ها با یک نرخ مرجع تغییر می‌کند. به همین دلیل حساسیت نرخ بهره آن می‌تواند با اوراق دارای سود ثابت متفاوت باشد.",
        "Hybrid - Conservative": "مختلط محافظه‌کارانه: ترکیبی از اوراق درآمد ثابت و مقدار محدودتری سهام دارد. هدف، ایجاد تعادل با تأکید بیشتر بر ثبات است؛ بااین‌حال بدون ریسک نیست.",
        "Hybrid - Balanced": "مختلط متعادل: بین سهام و اوراق درآمد ثابت تعادل برقرار می‌کند. هم از رشد بازار سهام بهره می‌گیرد و هم بخشی از دارایی را در ابزارهای کم‌نوسان‌تر نگه می‌دارد.",
        "Hybrid - Aggressive": "مختلط تهاجمی: سهم سهام آن بیشتر از بخش درآمد ثابت است. ظرفیت رشد بالاتری دارد، اما معمولاً در افت بازار سهام آسیب بیشتری می‌بیند.",
        "Hybrid - Dynamic Allocation": "مختلط با تخصیص دارایی پویا: مدیر با توجه به شرایط بازار، وزن سهام و درآمد ثابت را تغییر می‌دهد. میزان ریسک آن می‌تواند در طول زمان تغییر کند.",
        "Hybrid - Multi Asset": "مختلط چنددارایی: حداقل در چند گروه دارایی مختلف مانند سهام، اوراق بدهی و طلا سرمایه‌گذاری می‌کند. هدف، متنوع‌سازی منابع بازده و کاهش وابستگی به یک بازار است.",
        "Hybrid - Equity Savings": "مختلط پس‌انداز سهامی: ترکیبی از سهام، اوراق بدهی و موقعیت‌های پوشش ریسک دارد. معمولاً تلاش می‌کند بخشی از ریسک نوسان سهام را کنترل کند.",
        "Hybrid - Arbitrage": "مختلط آربیتراژ: از اختلاف قیمت یک دارایی در بازارهای مختلف یا معاملات نقدی و آتی استفاده می‌کند. ریسک سهامی خالص آن معمولاً محدودتر است، اما بازده به فرصت‌های آربیتراژ و شرایط بازار بستگی دارد.",
        "Equity - Sectoral": "سهامی بخشی: دست‌کم بخش عمده دارایی را در سهام یک صنعت مشخص مانند بانک، فناوری، دارو یا انرژی سرمایه‌گذاری می‌کند. چون سرمایه به یک بخش محدود است، عملکرد آن به وضعیت همان صنعت وابستگی زیادی دارد و تنوع کمتری دارد.",
        "Equity - Thematic": "سهامی موضوعی: روی یک موضوع اقتصادی یا سرمایه‌گذاری مانند زیرساخت، مصرف، تولید یا شرکت‌های دولتی تمرکز می‌کند. ممکن است از چند صنعت مختلف سهم داشته باشد، اما همه آن‌ها به یک موضوع مشترک وابسته‌اند.",
        "Other - Index": "صندوق شاخصی و ETF: تلاش می‌کند عملکرد یک شاخص مشخص مانند Nifty 50 یا Sensex را دنبال کند، نه اینکه با انتخاب فعال سهم حتماً از شاخص بهتر عمل کند. اختلاف بازده با شاخص، هزینه‌ها و خطای تعقیب شاخص اهمیت دارد. ETF در بورس معامله می‌شود و قیمت معاملاتی آن ممکن است با NAV تفاوت داشته باشد.",
        "Other - Gold": "صندوق طلا و ETF طلا: برای ایجاد دسترسی به قیمت طلا، معمولاً در طلای فیزیکی یا ابزارهای مرتبط با طلا سرمایه‌گذاری می‌کند. بازده آن به قیمت طلا و نرخ روپیه در برابر ارزهای خارجی وابسته است و سود تضمین‌شده ندارد.",
        "Other - Silver": "صندوق نقره و ETF نقره: عمدتاً برای دنبال‌کردن قیمت نقره طراحی شده است. نقره علاوه بر نقش فلز گران‌بها، مصرف صنعتی هم دارد و به همین دلیل ممکن است نوسان زیادی داشته باشد."
    }

    with st.expander("📘 راهنمای آشنایی با انواع صندوق‌ها و دسته‌بندی‌ها", expanded=False):
        st.markdown(
            "این توضیحات کمک می‌کند بدانید هر دسته معمولاً پول سرمایه‌گذاران را کجا به کار می‌گیرد. "
            "عنوان یک دسته به‌تنهایی به معنی تضمین سود یا مناسب‌بودن آن برای شما نیست؛ "
            "ریسک واقعی هر صندوق به ترکیب دارایی، مدیر و شرایط بازار بستگی دارد."
        )
        st.info(
            "درباره صندوق اهرمی: در دسته‌بندی رسمی صندوق‌های داخلی هند، گروه مستقلی با عنوان صندوق اهرمی یا معکوس وجود ندارد. "
            "استفاده از ابزار مشتقه در بعضی صندوق‌ها به‌تنهایی به معنی صندوق اهرمی ۲ برابری نیست؛ "
            "بنابراین این نوع را به‌عنوان یک دسته مستقل وارد رتبه‌بندی نکرده‌ایم."
        )
        for عنوان_گروه, پیشوند_گروه in [
            ("صندوق‌های سهامی؛ سرمایه‌گذاری در سهام شرکت‌ها", "Equity - "),
            ("صندوق‌های درآمد ثابت؛ سرمایه‌گذاری در اوراق و ابزارهای بدهی", "Debt - "),
            ("صندوق‌های مختلط؛ ترکیبی از چند نوع دارایی", "Hybrid - ")
        ]:
            موارد_راهنما = [
                (کلید, توضیح) for کلید, توضیح in توضیح_دسته_ها.items()
                if کلید.startswith(پیشوند_گروه) and کلید in گروه_های_موجود
            ]
            if موارد_راهنما:
                st.markdown("#### " + عنوان_گروه)
                for کلید, توضیح in موارد_راهنما:
                    st.markdown("**" + نام_فارسی_دسته_ها.get(کلید, کلید) + "**")
                    st.write(توضیح)
        گروه_های_بدون_راهنما = [
            گروه for گروه in گروه_های_موجود
            if گروه not in توضیح_دسته_ها
        ]
        if گروه_های_بدون_راهنما:
            st.caption("برای برخی دسته‌های خاص هنوز توضیح اختصاصی ثبت نشده است: " +
                       "، ".join(نام_فارسی_دسته_ها.get(گروه, گروه) for گروه in گروه_های_بدون_راهنما))

    انتخاب_های_مقایسه = []
    ستون_های_انتخاب = st.columns(2)
    for شماره in range(4):
        with ستون_های_انتخاب[شماره % 2]:
            with st.container(border=True):
                st.markdown("**صندوق شماره " + str(شماره + 1) + "**")
                دسته_انتخابی = st.selectbox(
                    "دسته‌بندی صندوق",
                    گزینه_های_دسته,
                    key="مقایسه_دسته_" + str(شماره),
                    accept_new_options=False,
                    filter_mode=None
                )
                if دسته_انتخابی == "انتخاب دسته‌بندی":
                    st.selectbox(
                        "نام صندوق",
                        ["ابتدا دسته‌بندی را انتخاب کن"],
                        key="مقایسه_نام_خالی_" + str(شماره),
                        disabled=True,
                        accept_new_options=False,
                    filter_mode=None
                    )
                else:
                    گروه_انگلیسی = نگاشت_دسته_به_انگلیسی[دسته_انتخابی]
                    صندوق_های_این_دسته = همه_صندوق_های_مقایسه[
                        همه_صندوق_های_مقایسه["fund_group"] == گروه_انگلیسی
                    ].drop_duplicates("scheme_code")
                    صندوق_های_این_دسته = صندوق_های_این_دسته.sort_values("scheme_name")
                    نگاشت_نام_صندوق = {
                        str(ردیف["scheme_code"]): str(ردیف["scheme_name"])
                        for _, ردیف in صندوق_های_این_دسته.iterrows()
                    }
                    کد_انتخابی = st.selectbox(
                        "نام صندوق",
                        list(نگاشت_نام_صندوق.keys()),
                        format_func=lambda کد, نگاشت=نگاشت_نام_صندوق: نگاشت.get(کد, کد),
                        key="مقایسه_صندوق_" + str(شماره),
                        accept_new_options=False,
                    filter_mode=None
                    )
                    ردیف_صندوق = صندوق_های_این_دسته[
                        صندوق_های_این_دسته["scheme_code"].astype(str) == str(کد_انتخابی)
                    ].iloc[0]
                    انتخاب_های_مقایسه.append(ردیف_صندوق.to_dict())

    کدهای_انتخاب_شده = [str(ردیف["scheme_code"]) for ردیف in انتخاب_های_مقایسه]
    if len(کدهای_انتخاب_شده) != len(set(کدهای_انتخاب_شده)):
        st.warning("یک صندوق را بیش از یک بار انتخاب کرده‌ای. لطفاً صندوق‌های متفاوتی انتخاب کن.")
        st.stop()

    if انتخاب_های_مقایسه:
        نتیجه_مقایسه = pd.DataFrame(انتخاب_های_مقایسه)
        with st.spinner("در حال دریافت آلفا و بتای صندوق‌های انتخاب‌شده..."):
            جدول_آلفا_بتا_مقایسه = دریافت_آلفا_بتا_مقایسه_ذخیره_شده(
                tuple(نتیجه_مقایسه["scheme_code"].astype(str))
            )
        نتیجه_مقایسه = نتیجه_مقایسه.drop(
            columns=["alpha", "beta"], errors="ignore"
        ).merge(
            جدول_آلفا_بتا_مقایسه[["scheme_code", "alpha", "beta"]],
            on="scheme_code",
            how="left"
        )
        خطاهای_آلفا_بتا_مقایسه = جدول_آلفا_بتا_مقایسه[
            جدول_آلفا_بتا_مقایسه["alpha_beta_error"].astype(str).str.strip().ne("")
        ]
        for _, خطای_صندوق in خطاهای_آلفا_بتا_مقایسه.iterrows():
            st.caption(
                "آلفا/بتای " + str(خطای_صندوق["scheme_code"])
                + " دریافت نشد: " + str(خطای_صندوق["alpha_beta_error"])
            )
        st.markdown("---")
        st.markdown("**صندوق‌های انتخاب‌شده برای مقایسه**")
        for _, ردیف in نتیجه_مقایسه.iterrows():
            st.caption("• " + str(ردیف["scheme_name"]) + " — " +
                       نام_فارسی_دسته_ها.get(str(ردیف["fund_group"]), str(ردیف["fund_group"])))

        نام_شاخص_های_مقایسه = {
            "return_1w": ("بازدهی ۱ هفته", "%", True),
            "return_1m": ("بازدهی ۱ ماه", "%", True),
            "return_3m": ("بازدهی ۳ ماه", "%", True),
            "return_6m": ("بازدهی ۶ ماه", "%", True),
            "return_1y": ("بازدهی ۱ سال", "%", True),
            "return_3y": ("بازدهی ۳ سال", "%", True),
            "volatility": ("نوسان‌پذیری", "%", True),
            "max_drawdown": ("بیشترین افت سرمایه", "%", True),
            "sharpe": ("نسبت شارپ", "", False),
            "sortino": ("نسبت سورتینو", "", False),
            "alpha": ("آلفا", "%", True),
            "beta": ("بتا", "", False),
            "aum_cr": ("دارایی تحت مدیریت", "کرور روپیه هند", False)
        }

        def رسم_نمودار_مقایسه(ستون):
            عنوان, پسوند, درصدی = نام_شاخص_های_مقایسه[ستون]
            if ستون not in نتیجه_مقایسه.columns:
                st.info("این شاخص در نسخه فعلی داده‌ها موجود نیست. پس از به‌روزرسانی روزانه دوباره بررسی کن.")
                return
            داده_نمودار = نتیجه_مقایسه[["scheme_name", ستون]].copy()
            داده_نمودار[ستون] = pd.to_numeric(داده_نمودار[ستون], errors="coerce")
            داده_نمودار = داده_نمودار.dropna()
            if داده_نمودار.empty:
                st.info("برای این شاخص، داده‌ای برای صندوق‌های انتخاب‌شده موجود نیست.")
                return
            if درصدی:
                داده_نمودار[ستون] = داده_نمودار[ستون] * 100
            داده_نمودار = داده_نمودار.sort_values(ستون)
            شکل_مقایسه = go.Figure()
            شکل_مقایسه.add_trace(go.Bar(
                x=داده_نمودار[ستون],
                y=داده_نمودار["scheme_name"],
                orientation="h",
                marker=dict(color=["#a8b6d8", "#879bd0", "#6883c8", "#18a999"][-len(داده_نمودار):]),
                text=[("{:,.2f}".format(مقدار).rstrip("0").rstrip(".") + پسوند)
                      for مقدار in داده_نمودار[ستون]],
                textposition="outside",
                cliponaxis=False,
                hovertemplate="<b>%{y}</b><br>" + عنوان + ": %{x:,.2f}" + پسوند + "<extra></extra>"
            ))
            شکل_مقایسه.update_layout(
                height=max(300, 82 * len(داده_نمودار) + 80),
                margin=dict(l=12, r=85, t=18, b=48),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(family="Vazirmatn, sans-serif", size=12, color="#526078"),
                showlegend=False,
                bargap=.42,
                xaxis=dict(title=عنوان + (" (" + پسوند + ")" if پسوند else ""),
                           showgrid=True, gridcolor="#edf1f7", zerolinecolor="#dce3ef"),
                yaxis=dict(title="", automargin=True, tickfont=dict(size=11, color="#293954"))
            )
            st.plotly_chart(شکل_مقایسه, use_container_width=True,
                            config={"displayModeBar": False})

        st.markdown("**نمودارهای مقایسه**")
        st.caption("در هر نمودار، مقدار هر صندوق در کنار صندوق‌های انتخاب‌شده دیگر نمایش داده می‌شود.")
        تب_مقایسه_بازدهی, تب_مقایسه_ریسک, تب_مقایسه_کیفیت, تب_مقایسه_بازار, تب_مقایسه_دارایی = st.tabs(
            ["بازدهی", "ریسک", "کیفیت عملکرد", "آلفا و بتا", "دارایی تحت مدیریت"]
        )
        with تب_مقایسه_بازدهی:
            for ستون in ["return_1w", "return_1m", "return_3m", "return_6m", "return_1y", "return_3y"]:
                st.markdown("**" + نام_شاخص_های_مقایسه[ستون][0] + "**")
                رسم_نمودار_مقایسه(ستون)
        with تب_مقایسه_ریسک:
            for ستون in ["volatility", "max_drawdown"]:
                st.markdown("**" + نام_شاخص_های_مقایسه[ستون][0] + "**")
                رسم_نمودار_مقایسه(ستون)
        with تب_مقایسه_کیفیت:
            for ستون in ["sharpe", "sortino"]:
                st.markdown("**" + نام_شاخص_های_مقایسه[ستون][0] + "**")
                رسم_نمودار_مقایسه(ستون)
        with تب_مقایسه_بازار:
            for ستون in ["alpha", "beta"]:
                st.markdown("**" + نام_شاخص_های_مقایسه[ستون][0] + "**")
                رسم_نمودار_مقایسه(ستون)

        with تب_مقایسه_دارایی:
            st.caption("AUM اندازه کل دارایی صندوق در گزارش AMFI است و همه طرح‌ها و گزینه‌های همان صندوق را در بر می‌گیرد.")
            رسم_نمودار_مقایسه("aum_cr")

        جدول_مقایسه = نتیجه_مقایسه[
            ["scheme_name", "fund_group"] +
            [ستون for ستون in نام_شاخص_های_مقایسه if ستون in نتیجه_مقایسه.columns]
        ].copy()
        جدول_مقایسه["fund_group"] = جدول_مقایسه["fund_group"].map(
            نام_فارسی_دسته_ها
        ).fillna(جدول_مقایسه["fund_group"])
        جدول_مقایسه = جدول_مقایسه.rename(columns={
            "scheme_name": "نام صندوق",
            "fund_group": "دسته‌بندی",
            **{ستون: مقدار[0] for ستون, مقدار in نام_شاخص_های_مقایسه.items()}
        })
        st.markdown("**جدول کامل مقایسه**")
        st.dataframe(جدول_مقایسه, use_container_width=True, hide_index=True)
        st.caption("تاریخ آخرین به‌روزرسانی داده‌ها: " + str(تصویر_مقایسه.get("updated_at_utc", "نامشخص")))
        st.caption("تاریخ گزارش دارایی تحت مدیریت: " + str(تصویر_مقایسه.get("aum_as_of", "نامشخص")) + " | واحد: کرور روپیه هند")
    else:
        st.info("برای شروع، حداقل یک دسته‌بندی و یک صندوق انتخاب کن.")

    st.stop()

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
    with ستون_سوال[شماره // 2]:
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
            مسیر_تصویر_روزانه = "data/latest_snapshot.json"
            try:
                import json
                from pathlib import Path
                فایل_تصویر = Path(مسیر_تصویر_روزانه)
                if فایل_تصویر.exists():
                    تصویر = json.loads(فایل_تصویر.read_text(encoding="utf-8"))
                    نتیجه_کامل = pd.DataFrame(تصویر["results"])
                    if نتیجه_کامل.empty:
                        raise RuntimeError("فایل آخرین به‌روزرسانی خالی است.")
                    ستون_امتیاز = st.session_state["پروفایل"] + "_score"
                    نتیجه_قابل_رتبه = نتیجه_کامل.dropna(subset=[ستون_امتیاز])
                    نتیجه = نتیجه_قابل_رتبه.sort_values(ستون_امتیاز, ascending=False).head(5).reset_index(drop=True)
                    if نتیجه.empty:
                        raise RuntimeError("برای این پروفایل صندوق رتبه‌بندی‌شده‌ای در فایل روزانه وجود ندارد.")
                    تعداد_کل_دریافتی = int(تصویر.get("source_funds", 0))
                    تعداد_واجد_شرایط = int(تصویر.get("eligible_funds", 0))
                    تعداد_تحلیل_شده = int(تصویر.get("analyzed_funds", len(نتیجه_کامل)))
                    تعداد_دارای_nav = int(تصویر.get("funds_with_nav", تعداد_تحلیل_شده))
                    تعداد_هر_گروه = تصویر.get("group_counts", {})
                    تعداد_آلفا_کل = int(نتیجه["alpha"].notna().sum()) if "alpha" in نتیجه.columns else 0
                    تعداد_بتا_کل = int(نتیجه["beta"].notna().sum()) if "beta" in نتیجه.columns else 0
                    خطاهای_آلفا_بتا = []
                    if "alpha_beta_error" in نتیجه.columns:
                        خطاهای_آلفا_بتا = [
                            str(ردیف["scheme_code"]) + ": " + str(ردیف["alpha_beta_error"])
                            for _, ردیف in نتیجه.iterrows()
                            if str(ردیف.get("alpha_beta_error", "")).strip()
                        ]
                    منابع_شاخص = [{
                        "source": "Charlie Alpha API",
                        "horizon": "3Y",
                        "benchmark": "شاخص مرجع اختصاصی هر صندوق",
                        "data_as_of": (
                            نتیجه["alpha_beta_as_of"].dropna().iloc[0]
                            if "alpha_beta_as_of" in نتیجه.columns and not نتیجه["alpha_beta_as_of"].dropna().empty else "نامشخص"
                        )
                    }]
                    try:
                        ذخیره_نتایج(نتیجه_کامل)
                        ذخیره_نتایج(نتیجه)
                        st.session_state["خطای_پایگاه"] = ""
                    except Exception as خطای_پایگاه:
                        st.session_state["خطای_پایگاه"] = str(خطای_پایگاه)
                    st.session_state["آخرین_به_روزرسانی"] = تصویر.get("updated_at_utc", "نامشخص")
                    st.session_state["نتیجه_صندوق"] = نتیجه
                    st.session_state["خطاهای_آلفا_بتا"] = خطاهای_آلفا_بتا
                    st.session_state["منابع_شاخص"] = منابع_شاخص
                    st.session_state["تعداد_کل_دریافتی"] = تعداد_کل_دریافتی
                    st.session_state["تعداد_واجد_شرایط"] = تعداد_واجد_شرایط
                    st.session_state["تعداد_هر_گروه"] = تعداد_هر_گروه
                    st.session_state["تعداد_بررسی_شده"] = تعداد_تحلیل_شده
                    st.session_state["تعداد_دارای_nav"] = تعداد_دارای_nav
                    st.session_state["تعداد_آلفا_کل"] = تعداد_آلفا_کل
                    st.session_state["تعداد_بتا_کل"] = تعداد_بتا_کل
                    st.session_state["نمایش_نتیجه"] = True
                else:
                    st.info("هنوز نسخه روزانه‌ای از داده‌ها ساخته نشده است؛ تحلیل مستقیم از منابع داده انجام می‌شود.")
                    st.session_state["آخرین_به_روزرسانی"] = "تحلیل مستقیم"
                    with st.spinner("در حال دریافت داده‌ها و تحلیل صندوق‌ها..."):
                        همه_صندوق_ها = دریافت_فهرست_ذخیره_شده()
                        # صندوق‌های سهامی و درآمد ثابت با دسته‌بندی دقیق جدا می‌شوند.
                        صندوق_های_واجد_شرایط = انتخاب_صندوق_ها(همه_صندوق_ها)
                        صندوق_های_انتخابی = صندوق_های_واجد_شرایط.copy()
        
                        if صندوق_های_انتخابی.empty:
                            raise RuntimeError("صندوق واجد شرایطی در گروه‌های تعریف‌شده پیدا نشد.")
        
                        تعداد_کل_دریافتی = int(همه_صندوق_ها["scheme_code"].nunique())
                        تعداد_واجد_شرایط = int(صندوق_های_واجد_شرایط["scheme_code"].nunique())
                        تعداد_هر_گروه = (
                            صندوق_های_واجد_شرایط.groupby("fund_group")["scheme_code"]
                            .nunique().to_dict()
                        )
        
                        nav = دریافت_nav_ذخیره_شده(
                            tuple(صندوق_های_انتخابی["scheme_code"].astype(str))
                        )
                        تعداد_دارای_nav = int(nav["scheme_code"].nunique())
                        شاخص_ها = محاسبه_شاخص_ها(nav)
        
                        if شاخص_ها.empty:
                            raise RuntimeError("تاریخچه NAV معتبر و کافی برای محاسبه شاخص‌ها دریافت نشد.")
        
                        # گروه هر صندوق را به شاخص‌های محاسبه‌شده اضافه می‌کنیم.
                        شاخص_ها["scheme_code"] = (
                            شاخص_ها["scheme_code"].astype(str).str.replace(r"\.0$", "", regex=True)
                        )
                        اطلاعات_گروه = صندوق_های_انتخابی[["scheme_code", "fund_group"]].copy()
                        اطلاعات_گروه["scheme_code"] = (
                            اطلاعات_گروه["scheme_code"].astype(str).str.replace(r"\.0$", "", regex=True)
                        )
                        شاخص_ها = شاخص_ها.merge(
                            اطلاعات_گروه.drop_duplicates("scheme_code"),
                            on="scheme_code",
                            how="left"
                        )
        
                        try:
                            جدول_دارایی = دریافت_دارایی_تحت_مدیریت(
                                صندوق_های_انتخابی["scheme_code"].astype(str).tolist()
                            )
                        except Exception as خطای_دارایی:
                            st.warning("اطلاعات دارایی تحت مدیریت موقتاً دریافت نشد: " + str(خطای_دارایی))
                            جدول_دارایی = pd.DataFrame(columns=["scheme_code", "aum_cr", "aum_as_of"])
                        شاخص_ها = شاخص_ها.merge(جدول_دارایی, on="scheme_code", how="left")

                        # آلفا و بتا فقط برای پنج صندوق نهایی دریافت می‌شوند.
                        شاخص_ها["alpha"] = float("nan")
                        شاخص_ها["beta"] = float("nan")
        
                        تعداد_تحلیل_شده = int(شاخص_ها["scheme_code"].nunique())
                        نتیجه_کامل = رتبه_بندی(شاخص_ها, ستون_گروه="fund_group")
        
                        # تمام صندوق‌های دارای شاخص، حتی اگر واجد شرایط رتبه‌بندی نباشند، ذخیره می‌شوند.
                        try:
                            ذخیره_نتایج(نتیجه_کامل)
                            st.session_state["خطای_پایگاه"] = ""
                        except Exception as خطای_پایگاه:
                            st.session_state["خطای_پایگاه"] = str(خطای_پایگاه)
        
                        ستون_امتیاز = st.session_state["پروفایل"] + "_score"
                        نتیجه_قابل_رتبه = نتیجه_کامل.dropna(subset=[ستون_امتیاز])
                        if نتیجه_قابل_رتبه.empty:
                            raise RuntimeError("هیچ صندوقی حداقل شرایط لازم برای رتبه‌بندی را نداشت.")
        
                        نتیجه = (
                            نتیجه_قابل_رتبه.sort_values(ستون_امتیاز, ascending=False)
                            .head(5).reset_index(drop=True)
                        )
        
                        # دریافت آلفا و بتا فقط برای پنج گزینه نهایی، برای جلوگیری از انتظار طولانی
                        جدول_آلفا_بتا = دریافت_آلفا_بتا_از_سرویس(
                            نتیجه["scheme_code"].astype(str).tolist(), افق="3Y"
                        )
                        جدول_آلفا_بتا["scheme_code"] = (
                            جدول_آلفا_بتا["scheme_code"].astype(str).str.replace(r"\.0$", "", regex=True)
                        )
                        نتیجه = نتیجه.drop(columns=["alpha", "beta"], errors="ignore").merge(جدول_آلفا_بتا, on="scheme_code", how="left")
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
                        تعداد_آلفا_کل = int(نتیجه["alpha"].notna().sum())
                        تعداد_بتا_کل = int(نتیجه["beta"].notna().sum())
        
                        # آلفا و بتای پنج صندوق نهایی نیز به رکوردهای قبلی اضافه می‌شوند.
                        try:
                            ذخیره_نتایج(نتیجه)
                        except Exception as خطای_پایگاه:
                            st.session_state["خطای_پایگاه"] = str(خطای_پایگاه)
                        st.session_state["نتیجه_صندوق"] = نتیجه
                        st.session_state["خطاهای_آلفا_بتا"] = خطاهای_آلفا_بتا
                        st.session_state["منابع_شاخص"] = منابع_شاخص
                        st.session_state["تعداد_کل_دریافتی"] = تعداد_کل_دریافتی
                        st.session_state["تعداد_واجد_شرایط"] = تعداد_واجد_شرایط
                        st.session_state["تعداد_هر_گروه"] = تعداد_هر_گروه
                        st.session_state["تعداد_بررسی_شده"] = تعداد_تحلیل_شده
                        st.session_state["تعداد_دارای_nav"] = تعداد_دارای_nav
                        st.session_state["تعداد_آلفا_کل"] = تعداد_آلفا_کل
                        st.session_state["تعداد_بتا_کل"] = تعداد_بتا_کل
                        st.session_state["نمایش_نتیجه"] = True
            except Exception:
                raise
        except Exception as خطا:
            st.error("در تحلیل داده‌ها مشکلی پیش آمد: " + str(خطا))

if st.session_state.get("نمایش_نتیجه", False):
    نتیجه = st.session_state["نتیجه_صندوق"].copy()
    پروفایل = st.session_state["پروفایل"]

    st.markdown("---")
    st.markdown('<div class="section-title">۵ صندوق پیشنهادی متناسب با شما</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-subtitle">رتبه‌ها بر اساس مقایسه درون‌گروهی و متناسب‌سازی آموزشی با سطح ریسک شما محاسبه شده‌اند.</div>', unsafe_allow_html=True)

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
    آمار_۵.metric("آلفای دریافت‌شده برای ۵ صندوق", st.session_state.get("تعداد_آلفا_کل", "—"))
    آمار_۶.metric("بتای دریافت‌شده برای ۵ صندوق", st.session_state.get("تعداد_بتا_کل", "—"))
    st.caption("آخرین به‌روزرسانی خودکار داده‌ها: " + str(st.session_state.get("آخرین_به_روزرسانی", "در دسترس نیست")))
    تاریخ_گزارش_AUM = (
        نتیجه["aum_as_of"].dropna().max()
        if "aum_as_of" in نتیجه.columns and not نتیجه["aum_as_of"].dropna().empty
        else "در دسترس نیست"
    )
    st.caption("تاریخ گزارش دارایی تحت مدیریت: " + str(تاریخ_گزارش_AUM) + " | واحد: کرور روپیه هند")
    st.caption(
        "آلفا برای " + str(تعداد_دارای_آلفا) + " و بتا برای " + str(تعداد_دارای_بتا)
        + " صندوق نهایی دریافت شده است. صندوق‌ها در گروه‌های سهامی، درآمد ثابت، مختلط، بخشی، موضوعی، شاخصی، طلا و نقره "
        "به‌صورت جداگانه بررسی می‌شوند. امتیاز صدکی به‌تنهایی معیار ریسک مطلق نیست؛ نوع دارایی نیز با توجه "
        "به پروفایل کاربر در امتیاز نهایی اثر داده می‌شود."
    )
    with st.expander("تعداد صندوق‌ها در هر گروه"):
        جدول_تعداد_گروه = pd.DataFrame(
            list(st.session_state.get("تعداد_هر_گروه", {}).items()),
            columns=["گروه صندوق", "تعداد صندوق"]
        )
        جدول_تعداد_گروه["گروه صندوق"] = جدول_تعداد_گروه["گروه صندوق"].map(
            نام_فارسی_گروه_ها
        ).fillna(جدول_تعداد_گروه["گروه صندوق"])
        st.dataframe(جدول_تعداد_گروه, use_container_width=True, hide_index=True)

    for شماره, ردیف in نتیجه.iterrows():
        امتیاز_صندوق = ردیف.get(پروفایل + "_score", float("nan"))
        نام_نمایشی = html.escape(str(ردیف["scheme_name"]))
        گروه_خام = str(ردیف.get("fund_group", "نامشخص"))
        گروه_نمایشی = html.escape(نام_فارسی_گروه_ها.get(گروه_خام, گروه_خام))
        دارایی_خام = pd.to_numeric(pd.Series([ردیف.get("aum_cr")]), errors="coerce").iloc[0]
        دارایی_نمایشی = (
            "{:,.2f} کرور روپیه هند".format(دارایی_خام)
            if pd.notna(دارایی_خام) else "در دسترس نیست"
        )
        st.markdown(
            '<div class="fund-card"><span class="fund-rank">' + str(شماره + 1)
            + '</span> <span class="fund-name">' + نام_نمایشی
            + '</span><div class="small-note">گروه: ' + گروه_نمایشی
            + '</div><div class="small-note">دارایی تحت مدیریت: ' + دارایی_نمایشی
            + '</div><div class="fund-score">امتیاز تناسب: '
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
        "beta": ("بتا", "بتای سه‌ساله نسبت به شاخص مرجع همان صندوق؛ نزدیک ۱ یعنی حرکت تقریباً هم‌اندازه شاخص.", False, ""),
        "aum_cr": ("دارایی تحت مدیریت", "اندازه کل دارایی صندوق در گزارش AMFI، برای همه طرح‌ها و گزینه‌های همان صندوق؛ واحد کرور روپیه هند.", False, " کرور روپیه هند")
    }

    def نمایش_نمودار(ستون):
        عنوان, توضیح, درصدی, پسوند = نام_شاخص_ها[ستون]
        if ستون not in نتیجه.columns:
            st.info("این شاخص در نسخه فعلی داده‌ها موجود نیست. پس از به‌روزرسانی روزانه دوباره بررسی کن.")
            return
        داده = نتیجه[["scheme_name", ستون]].copy()
        داده[ستون] = pd.to_numeric(داده[ستون], errors="coerce")
        داده = داده.dropna().sort_values(ستون, ascending=True)
        if داده.empty:
            st.info("برای این شاخص داده قابل نمایش در دسترس نیست.")
            return
        if درصدی:
            داده[ستون] = داده[ستون] * 100
        اعداد = داده[ستون].round(2)
        رنگ_ها = ["#a8b6d8", "#879bd0", "#6883c8", "#4770bd", "#18a999"]
        شکل = go.Figure()
        شکل.add_trace(go.Bar(
            x=داده[ستون],
            y=داده["scheme_name"],
            orientation="h",
            marker=dict(color=رنگ_ها[-len(داده):], line=dict(width=0)),
            text=[("{:,.2f}".format(x).rstrip("0").rstrip(".") + پسوند) for x in اعداد],
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

    تب_بازدهی, تب_ریسک, تب_کیفیت, تب_بازار, تب_اندازه = st.tabs(["بازدهی", "ریسک", "کیفیت عملکرد", "آلفا و بتا", "دارایی تحت مدیریت"])
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

    with تب_اندازه:
        st.caption("AUM اندازه کل دارایی صندوق است و به‌تنهایی نشانه بازدهی یا کیفیت بهتر نیست.")
        نمایش_نمودار("aum_cr")

    st.markdown("---")
    تب_جدول, تب_منابع, تب_پایگاه = st.tabs(["جدول مقایسه", "اطلاعات داده‌ها", "پایگاه داده"])
    with تب_جدول:
        ستون_های_جدول = ["scheme_name", "fund_group", "data_coverage", پروفایل + "_score"] + list(نام_شاخص_ها.keys())
        جدول = نتیجه[[x for x in ستون_های_جدول if x in نتیجه.columns]].copy()
        if "fund_group" in جدول.columns:
            جدول["fund_group"] = جدول["fund_group"].map(
                نام_فارسی_گروه_ها
            ).fillna(جدول["fund_group"])
        جدول = جدول.rename(columns={"scheme_name": "نام صندوق", "fund_group": "گروه صندوق", "data_coverage": "پوشش داده (درصد)", پروفایل + "_score": "امتیاز تناسب", **{k: v[0] for k, v in نام_شاخص_ها.items()}})
        st.dataframe(جدول, use_container_width=True, hide_index=True)
        st.download_button(
            "دانلود جدول مقایسه (CSV)",
            data=جدول.to_csv(index=False).encode("utf-8-sig"),
            file_name="fund_comparison.csv",
            mime="text/csv"
        )
    with تب_منابع:
        st.markdown("**روش رتبه‌بندی**")
        st.write(
            "صندوق‌ها ابتدا فقط با هم‌گروهی‌های خود مقایسه می‌شوند. "
            "امتیاز بازدهی از بازدهی یک‌ساله و سه‌ساله، امتیاز ریسک از نوسان و بیشترین افت، "
            "و کیفیت عملکرد از شارپ و سورتینو ساخته می‌شود. ۱۰ درصد امتیاز نیز به اندازه صندوق (AUM) اختصاص دارد. "
            "AUM درون همان گروه رتبه‌بندی می‌شود و در صورت نبود داده، وزن آن بین معیارهای موجود بازتوزیع می‌شود. "
            "برای گروه‌های کم‌تعداد، امتیاز صدکی به عدد ۵۰ نزدیک می‌شود."
        )
        جدول_وزن = pd.DataFrame([
            ["محافظه‌کار", 18, 45, 27, 10],
            ["متوسط", 36, 27, 27, 10],
            ["رشدگرا", 49.5, 18, 22.5, 10],
            ["ریسک‌پذیر", 58.5, 9, 22.5, 10]
        ], columns=["پروفایل", "بازدهی (درصد)", "ریسک (درصد)", "کیفیت (درصد)", "اندازه صندوق / AUM (درصد)"])
        st.dataframe(جدول_وزن, use_container_width=True, hide_index=True)
        جدول_تناسب_دارایی = pd.DataFrame([
            ["محافظه‌کار", 10, 5, -10],
            ["متوسط", 5, 5, 0],
            ["رشدگرا", -5, 0, 5],
            ["ریسک‌پذیر", -10, -5, 10]
        ], columns=["پروفایل", "درآمد ثابت", "ترکیبی", "سهامی"])
        st.markdown("**تعدیل امتیاز بر اساس نوع دارایی**")
        st.dataframe(جدول_تناسب_دارایی, use_container_width=True, hide_index=True)
        st.caption(
            "نوع دارایی نیز در امتیاز تناسب اثر دارد: درآمد ثابت برای محافظه‌کار، "
            "گروه ترکیبی برای سطح متوسط و سهام برای پروفایل‌های ریسک‌پذیرتر امتیاز بیشتری می‌گیرد. "
            "برای صندوق‌های شاخصی و کالایی، تعدیل جداگانه نوع دارایی اعمال نشده است. "
            "این تعدیل یک فرض آموزشی است و امتیاز، ریسک مطلق صندوق را نشان نمی‌دهد."
        )
        تاریخ_شاخص_ها = (
            نتیجه["metrics_as_of"].dropna().iloc[0]
            if "metrics_as_of" in نتیجه.columns and not نتیجه["metrics_as_of"].dropna().empty
            else "نامشخص"
        )
        st.write("تاریخ پایان مشترک محاسبه شاخص‌ها: " + str(تاریخ_شاخص_ها))
        st.markdown("**منبع آلفا و بتا**")
        st.write("Charlie Alpha API — محاسبه سه‌ساله با شاخص مرجع مرتبط با هر صندوق.")
        st.markdown("**منبع دارایی تحت مدیریت (AUM)**")
        st.write("AMFI Daily Fund Performance Data از طریق فایل scheme_details_latest در Tigzig؛ مقدار AUM کل صندوق و همه طرح‌ها و گزینه‌ها را پوشش می‌دهد و بر حسب کرور روپیه هند است.")
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
    with تب_پایگاه:
        st.markdown("**ذخیره سازی اطلاعات با SQLite**")
        st.write("اطلاعات صندوق ها و شاخص های محاسبه شده در یک پایگاه داده رابطه ای ذخیره می شوند.")
        آمار_پایگاه = آمار_پایگاه_داده()
        if st.session_state.get("خطای_پایگاه"):
            st.warning("ذخیره سازی پایگاه داده با خطا روبه رو شد: " + st.session_state["خطای_پایگاه"])
        پ۱, پ۲ = st.columns(2)
        پ۱.metric("تعداد صندوق های ذخیره شده", آمار_پایگاه["funds"])
        پ۲.metric("تعداد رکوردهای شاخص", آمار_پایگاه["metrics"])
        st.caption("اطلاعات تمام صندوق‌های دارای شاخص محاسبه‌شده ذخیره می‌شوند؛ هر صندوق با کد یکتا شناسایی شده و می‌تواند در تاریخ‌های مختلف چند رکورد شاخص داشته باشد. فایل SQLite در فضای ابری دائمی نیست و ممکن است با بازسازی محیط پاک شود.")

st.markdown("---")
st.markdown(
    '<div class="small-note">این سامانه یک پروژه آموزشی برای مقایسه صندوق‌های سهامی، درآمد ثابت، مختلط، شاخصی، بخشی، موضوعی و صندوق‌های طلا و نقره است و توصیه خرید یا فروش محسوب نمی‌شود. فهرست و NAV از داده‌های AMFI از طریق Tigzig و آلفا و بتا از Charlie Alpha API دریافت می‌شوند.</div>',
    unsafe_allow_html=True
)