"""Streamlit dashboard for mutual-fund risk and return analysis."""
from pathlib import Path
import sys

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from fundrank.dashboard_features import (
    add_standalone_risk_score,
    equal_weight_portfolio,
    make_pdf_report,
)
from fundrank.questionnaire import score_risk_questionnaire

DATA = ROOT / "data" / "processed" / "fund_rankings.parquet"
EVALUATION = ROOT / "data" / "processed" / "ranking_evaluation.csv"
OUT_OF_SAMPLE = ROOT / "data" / "processed" / "out_of_sample_evaluation.csv"
SENSITIVITY = ROOT / "data" / "processed" / "weight_sensitivity.csv"
HISTORY_DIR = ROOT / "ranking_snapshots"

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

df = add_standalone_risk_score(df)
profiles = {
    "محافظه‌کار": "conservative",
    "متعادل": "moderate",
    "رشدگرا": "growth",
    "تهاجمی": "aggressive",
}
profile_label = st.selectbox("پروفایل رتبه‌بندی", list(profiles))
profile = profiles[profile_label]
score_col = f"composite_{profile}"
rank_col = f"rank_{profile}"
coverage_col = f"coverage_{profile}"

a, b, c, d = st.columns(4)
a.metric("تعداد صندوق‌ها", f"{len(df):,}")
b.metric("آخرین تاریخ NAV", str(pd.to_datetime(df["last_date"]).max().date()))
c.metric("گروه‌های رتبه‌بندی", f"{df['ranking_group'].nunique():,}")
d.metric("میانگین امتیاز ریسک", f"{df['risk_score'].mean():.1f}/100")

tabs = st.tabs([
    "رتبه‌بندی اصلی", "مقایسه صندوق‌ها", "ترکیب پیشنهادی",
    "پرسش‌نامه ریسک", "تاریخچه رتبه‌ها", "گزارش PDF",
])

with tabs[0]:
    small_groups = (
        int(df.loc[df["ranking_group_status"] == "insufficient_peers", "ranking_group"].nunique())
        if "ranking_group_status" in df.columns else 0
    )
    if small_groups:
        st.info("گروه‌های دارای کمتر از ۵ صندوق رتبه نسبی دریافت نمی‌کنند؛ معیارهای خام آن‌ها همچنان نمایش داده می‌شود.")

    left, right = st.columns([1, 2])
    with left:
        groups = ["همه گروه‌ها"] + sorted(df["ranking_group"].dropna().unique().tolist())
        group = st.selectbox("گروه صندوق", groups)
        minimum = st.slider("حداقل پوشش وزن‌ها (%)", 0, 100, 70)
        search = st.text_input("جست‌وجوی نام یا کد صندوق")

    view = df.copy()
    if group != "همه گروه‌ها":
        view = view[view["ranking_group"] == group]
    view = view[view[coverage_col] >= minimum]
    if search:
        view = view[
            view["scheme_name"].astype(str).str.contains(search, case=False, na=False)
            | view["scheme_code"].astype(str).str.contains(search, na=False)
        ]
    view = view.sort_values(score_col, ascending=False)

    with right:
        st.subheader(f"رتبه‌بندی پروفایل {profile_label}")
        columns = [
            rank_col, "scheme_name", "scheme_code", "ranking_group",
            "ranking_group_size", "ranking_group_status", score_col,
            coverage_col, "return_1m", "return_3m", "return_6m",
            "return_12m", "volatility", "max_drawdown",
            "sharpe_ratio", "sortino_ratio", "risk_score",
        ]
        columns = [column for column in columns if column in view.columns]
        st.dataframe(view[columns], use_container_width=True, hide_index=True)

    if not view.empty:
        st.subheader("نقشه ریسک و بازده")
        st.scatter_chart(view, x="volatility", y="return_12m", color="ranking_group",
                         size=score_col, use_container_width=True)
        st.download_button(
            "دریافت نتایج CSV", view.to_csv(index=False).encode("utf-8-sig"),
            file_name=f"fund_rankings_{profile}.csv", mime="text/csv",
        )
    else:
        st.info("با فیلترهای انتخاب‌شده صندوقی پیدا نشد.")

    for file_path, heading, note in [
        (EVALUATION, "ارزیابی درون‌نمونه‌ای", "بازده ۱۲ماهه گذشته یکی از ورودی‌های مدل است؛ بنابراین این مقایسه، آزمون پیش‌بینی مستقل نیست."),
        (OUT_OF_SAMPLE, "ارزیابی برون‌نمونه‌ای", "رتبه‌ها با داده‌های قبل از تاریخ تشکیل ساخته شده و با بازده ۱۲ ماه بعد مقایسه می‌شوند. محدودیت‌های تاریخی فهرست صندوق‌ها همچنان باید در نظر گرفته شود."),
        (SENSITIVITY, "حساسیت رتبه به تغییر وزن معیارها", "انحراف معیار بالاتر یعنی رتبه در برابر تغییر وزن‌ها حساس‌تر است."),
    ]:
        if file_path.exists():
            st.subheader(heading)
            table = pd.read_csv(file_path)
            if "profile" in table.columns:
                table = table[table["profile"].str.lower() == profile]
            st.caption(note)
            st.dataframe(table, use_container_width=True, hide_index=True)

with tabs[1]:
    st.subheader("مقایسه مستقیم صندوق‌ها")
    fund_options = {
        f"{row.scheme_name} | {row.scheme_code}": row.scheme_code
        for row in df[["scheme_name", "scheme_code"]].drop_duplicates().itertuples(index=False)
    }
    selected_funds = st.multiselect(
        "۲ تا ۵ صندوق را انتخاب کنید", list(fund_options.keys()), max_selections=5,
    )
    if len(selected_funds) >= 2:
        codes = [fund_options[name] for name in selected_funds]
        compared = df[df["scheme_code"].isin(codes)].copy()
        comparison_columns = [
            "scheme_name", "scheme_code", "ranking_group", rank_col, score_col,
            "return_1m", "return_3m", "return_6m", "return_12m",
            "volatility", "max_drawdown", "sharpe_ratio", "sortino_ratio", "risk_score",
        ]
        st.dataframe(
            compared[[column for column in comparison_columns if column in compared.columns]],
            use_container_width=True, hide_index=True,
        )
        chart_data = compared.set_index("scheme_name")[[
            column for column in ["return_12m", "volatility", "max_drawdown"]
            if column in compared.columns
        ]]
        st.bar_chart(chart_data, use_container_width=True)
    else:
        st.info("برای نمایش مقایسه، حداقل دو صندوق انتخاب کنید.")

with tabs[2]:
    st.subheader("ترکیب ساده و پیشنهادی صندوق‌ها")
    st.caption("این ابزار از میان صندوق‌های موجود در رتبه‌بندی، چند گزینه برتر را انتخاب و وزن مساوی پیشنهاد می‌کند؛ تنوع بین کلاس‌های دارایی یا تضمین بازده ایجاد نمی‌کند.")
    portfolio_group = st.selectbox(
        "گروه مورد بررسی", ["همه گروه‌ها"] + sorted(df["ranking_group"].dropna().unique().tolist()),
        key="portfolio_group",
    )
    portfolio_count = st.slider("تعداد صندوق‌ها", 2, 10, 5, key="portfolio_count")
    candidates = df[df[coverage_col] >= 70].copy()
    if portfolio_group != "همه گروه‌ها":
        candidates = candidates[candidates["ranking_group"] == portfolio_group]
    portfolio = equal_weight_portfolio(candidates, score_col, portfolio_count)
    if not portfolio.empty:
        portfolio_columns = [
            "scheme_name", "scheme_code", "ranking_group", rank_col,
            score_col, "risk_score", "return_12m", "volatility", "max_drawdown",
            "portfolio_weight_pct",
        ]
        st.dataframe(
            portfolio[[column for column in portfolio_columns if column in portfolio.columns]],
            use_container_width=True, hide_index=True,
        )
        st.metric("تعداد صندوق‌های انتخاب‌شده", len(portfolio))
        st.metric("وزن هر صندوق", f"{100 / len(portfolio):.1f}%")
    else:
        st.warning("برای این گروه، صندوق واجد شرایط کافی وجود ندارد.")

with tabs[3]:
    st.subheader("پرسش‌نامه سنجش ریسک‌پذیری")
    st.write("به هر پرسش از ۰ تا ۱۰ امتیاز بدهید. این پرسش‌نامه فقط یک برآورد آموزشی از پروفایل ریسک است.")
    questions = [
        "چه میزان افت موقت سرمایه را می‌توانید تحمل کنید؟",
        "اگر ارزش سرمایه در یک ماه ۱۰٪ کاهش یابد، چه می‌کنید؟",
        "افق زمانی سرمایه‌گذاری شما چقدر بلندمدت است؟",
        "چه میزان تجربه سرمایه‌گذاری دارید؟",
        "چه مقدار از سرمایه شما برای هزینه‌های ضروری لازم نیست؟",
        "تا چه اندازه با نوسان روزانه بازار کنار می‌آیید؟",
        "برای بازده بالاتر، چه میزان ریسک اضافه می‌پذیرید؟",
        "در تصمیم‌گیری سرمایه‌گذاری چقدر مستقل و مطمئن هستید؟",
        "اگر بازار چند ماه منفی باشد، چقدر می‌توانید صبر کنید؟",
        "چه میزان از سرمایه‌تان را می‌توانید برای چند سال نگه دارید؟",
    ]
    answers = []
    left, right = st.columns(2)
    for index, question in enumerate(questions):
        with (left if index % 2 == 0 else right):
            answers.append(st.slider(question, 0, 10, 5, key=f"risk_q_{index}"))
    questionnaire_score, questionnaire_profile = score_risk_questionnaire(answers)
    st.metric("امتیاز پرسش‌نامه", f"{questionnaire_score:.1f}/100")
    st.success(f"پروفایل تخمینی شما: {questionnaire_profile}")
    st.caption("این نتیجه جایگزین ارزیابی مالی، نیاز نقدینگی یا مشاوره تخصصی نیست.")

with tabs[4]:
    st.subheader("تاریخچه تغییر رتبه صندوق‌ها")
    snapshots = sorted(HISTORY_DIR.glob("*.csv")) if HISTORY_DIR.exists() else []
    if len(snapshots) < 2:
        st.info("برای نمایش روند تاریخی، حداقل دو اجرای جدید لازم است. سامانه از این نسخه به بعد در هر اجرای موفق، رتبه‌ها را ذخیره می‌کند؛ داده تاریخی قبل از فعال‌سازی این قابلیت قابل بازسازی نیست.")
    else:
        history_frames = []
        for snapshot_file in snapshots:
            frame = pd.read_csv(snapshot_file)
            frame["snapshot_date"] = snapshot_file.stem
            history_frames.append(frame)
        history = pd.concat(history_frames, ignore_index=True)
        history_funds = history[["scheme_name", "scheme_code"]].drop_duplicates()
        history_options = {
            f"{row.scheme_name} | {row.scheme_code}": row.scheme_code
            for row in history_funds.itertuples(index=False)
        }
        chosen_history_fund = st.selectbox("صندوق", list(history_options.keys()))
        history_code = history_options[chosen_history_fund]
        history_column = f"rank_{profile}"
        if history_column in history.columns:
            trend = history[history["scheme_code"] == history_code].dropna(subset=[history_column])
            trend = trend.sort_values("snapshot_date")
            if not trend.empty:
                st.line_chart(trend.set_index("snapshot_date")[history_column], y_label="رتبه (عدد کمتر بهتر)")
                st.dataframe(trend[["snapshot_date", "scheme_name", history_column]], use_container_width=True, hide_index=True)
            else:
                st.info("برای این صندوق هنوز رتبه‌ای در تاریخچه ثبت نشده است.")

with tabs[5]:
    st.subheader("دریافت گزارش PDF")
    st.write("گزارش شامل حداکثر ۳۰ صندوق برتر در پروفایل انتخاب‌شده و شاخص‌های اصلی آن‌هاست.")
    report_data = df.sort_values(score_col, ascending=False)
    latest_date = str(pd.to_datetime(df["last_date"]).max().date())
    pdf_bytes = make_pdf_report(report_data, profile.title(), latest_date)
    st.download_button(
        "دانلود گزارش PDF", data=pdf_bytes,
        file_name=f"fund_ranking_report_{profile}.pdf", mime="application/pdf",
    )

st.caption("این رتبه‌بندی و ابزارهای تکمیلی پژوهشی و آموزشی هستند و توصیه سرمایه‌گذاری شخصی محسوب نمی‌شوند.")
