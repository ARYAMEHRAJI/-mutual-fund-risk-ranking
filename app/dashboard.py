"""Streamlit dashboard for fund rankings."""
from pathlib import Path
import sys
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
DATA = ROOT / "data" / "processed" / "fund_rankings.parquet"
EVALUATION = ROOT / "data" / "processed" / "ranking_evaluation.csv"
OUT_OF_SAMPLE = ROOT / "data" / "processed" / "out_of_sample_evaluation.csv"
SENSITIVITY = ROOT / "data" / "processed" / "weight_sensitivity.csv"

st.set_page_config(page_title="Mutual Fund Risk & Return Ranking", layout="wide")
st.title("Mutual Fund Risk & Return Ranking")
st.caption("Research dashboard • Indian mutual funds • quantitative analysis")

if not DATA.exists():
    st.warning("No processed dataset found. Run the pipeline first: python scripts/run_pipeline.py")
    st.stop()
df = pd.read_parquet(DATA)
if df.empty:
    st.error("The ranking dataset is empty.")
    st.stop()

profiles = {"محافظه‌کار": "conservative", "متعادل": "moderate", "رشدگرا": "growth", "تهاجمی": "aggressive"}
label = st.selectbox("پروفایل ریسک", list(profiles))
profile = profiles[label]
score, rank, coverage = f"composite_{profile}", f"rank_{profile}", f"coverage_{profile}"

a, b, c, d = st.columns(4)
a.metric("تعداد صندوق‌ها", f"{len(df):,}")
b.metric("آخرین تاریخ NAV", str(pd.to_datetime(df["last_date"]).max().date()))
c.metric("گروه‌های رتبه‌بندی", f"{df['ranking_group'].nunique():,}")
small_groups = (
    int(df.loc[df["ranking_group_status"] == "insufficient_peers", "ranking_group"].nunique())
    if "ranking_group_status" in df.columns else 0
)
d.metric("گروه‌های کم‌نمونه", f"{small_groups:,}")

if small_groups:
    st.info("گروه‌هایی با کمتر از ۵ صندوق در رتبه‌بندی نسبی وارد نشده‌اند؛ معیارهای خام آن‌ها همچنان در داده موجود است.")

left, right = st.columns([1, 2])
with left:
    groups = ["همه گروه‌ها"] + sorted(df["ranking_group"].dropna().unique().tolist())
    group = st.selectbox("گروه صندوق", groups)
    minimum = st.slider("حداقل پوشش وزن‌ها (%)", 0, 100, 70)
    search = st.text_input("جست‌وجوی نام یا کد صندوق")

view = df.copy()
if group != "همه گروه‌ها":
    view = view[view["ranking_group"] == group]
view = view[view[coverage] >= minimum]
if search:
    view = view[view["scheme_name"].astype(str).str.contains(search, case=False, na=False)
                | view["scheme_code"].astype(str).str.contains(search, na=False)]
view = view.sort_values(score, ascending=False)

with right:
    st.subheader(f"رتبه‌بندی پروفایل {label}")
    cols = [x for x in [
        rank, "scheme_name", "scheme_code", "ranking_group",
        "ranking_group_size", "ranking_group_status", score, coverage,
        "return_1m", "return_3m", "return_6m", "return_12m",
        "volatility", "max_drawdown", "sharpe_ratio", "sortino_ratio",
    ] if x in view.columns]
    st.dataframe(view[cols], use_container_width=True, hide_index=True)

if not view.empty:
    st.subheader("نقشه ریسک و بازده")
    st.scatter_chart(view, x="volatility", y="return_12m", color="ranking_group",
                     size=score, use_container_width=True)
    st.download_button("دریافت نتایج CSV", view.to_csv(index=False).encode("utf-8-sig"),
                       file_name=f"fund_rankings_{profile}.csv", mime="text/csv")
else:
    st.info("با فیلترهای انتخاب‌شده صندوقی پیدا نشد.")

if EVALUATION.exists():
    st.subheader("ارزیابی درون‌نمونه‌ای در مقایسه با بازده گذشته")
    evaluation = pd.read_csv(EVALUATION)
    evaluation = evaluation[evaluation["profile"].str.lower() == profile]
    st.caption("این مقایسه تشخیصی است؛ بازده ۱۲ماهه گذشته خودش یکی از ورودی‌های مدل است.")
    st.dataframe(evaluation, use_container_width=True, hide_index=True)

if OUT_OF_SAMPLE.exists():
    st.subheader("ارزیابی برون‌نمونه‌ای با بازده ۱۲ ماه آینده")
    oos = pd.read_csv(OUT_OF_SAMPLE)
    oos = oos[oos["profile"].str.lower() == profile]
    st.caption("رتبه‌ها با داده‌های قبل از تاریخ تشکیل ساخته شده‌اند و با بازده ۱۲ ماه بعد مقایسه می‌شوند. این نسخه هنوز از فهرست و طبقه‌بندی فعلی صندوق‌ها استفاده می‌کند.")
    st.dataframe(oos, use_container_width=True, hide_index=True)

if SENSITIVITY.exists():
    st.subheader("حساسیت رتبه به تغییر وزن معیارها")
    sensitivity = pd.read_csv(SENSITIVITY)
    sensitivity = sensitivity[sensitivity["profile"].str.lower() == profile]
    if not sensitivity.empty:
        st.caption("انحراف معیار رتبه در شبیه‌سازی تغییر وزن‌ها؛ مقدار بالاتر یعنی رتبه حساس‌تر است.")
        unstable = sensitivity.sort_values("rank_std", ascending=False).head(15)
        st.dataframe(unstable, use_container_width=True, hide_index=True)

st.caption("این رتبه‌بندی ابزار پژوهشی است و توصیه سرمایه‌گذاری محسوب نمی‌شود.")
