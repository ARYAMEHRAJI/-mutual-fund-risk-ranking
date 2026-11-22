# این فایل صفحه ساده پروژه را اجرا می کند.

import streamlit as st
import pandas as pd

from simple_data import دریافت_صندوق_ها, انتخاب_صندوق_ها, دریافت_nav
from simple_metrics import محاسبه_شاخص_ها, محاسبه_آلفا_بتا
from simple_ranking import رتبه_بندی

st.set_page_config(page_title="رتبه بندی صندوق های سرمایه گذاری", layout="wide")
st.title("سامانه ساده رتبه بندی صندوق های سرمایه گذاری هند")
st.write("این برنامه صندوق ها را بر اساس بازدهی، ریسک و نوع سرمایه گذار مقایسه می کند.")

# گروه صندوق را از کاربر می پرسیم
گروه = st.selectbox(
    "گروه صندوق را انتخاب کنید",
    ["Large Cap", "Mid Cap", "Small Cap", "Flexi Cap", "Multi Cap", "Focused"]
)

# برای شروع تعداد کمی صندوق می گیریم تا دریافت اطلاعات طولانی نشود
تعداد = st.slider("تعداد صندوق ها برای بررسی", 5, 50, 10)

# فایل شاخص بازار برای آلفا و بتا
فایل_شاخص = st.file_uploader(
    "فایل CSV شاخص مرجع را وارد کنید (ستون های date و close)",
    type=["csv"]
)

if st.button("شروع تحلیل"):
    try:
        with st.spinner("در حال دریافت فهرست صندوق ها..."):
            همه_صندوق_ها = دریافت_صندوق_ها()
            صندوق_های_انتخابی = انتخاب_صندوق_ها(همه_صندوق_ها, گروه)
            صندوق_های_انتخابی = صندوق_های_انتخابی.head(تعداد)

        if صندوق_های_انتخابی.empty:
            st.error("برای این گروه صندوقی پیدا نشد.")
        else:
            with st.spinner("در حال دریافت اطلاعات NAV..."):
                کدها = صندوق_های_انتخابی["scheme_code"].tolist()
                nav = دریافت_nav(کدها)

            with st.spinner("در حال محاسبه شاخص ها..."):
                شاخص_ها = محاسبه_شاخص_ها(nav)

                # آلفا و بتا فقط وقتی محاسبه می شوند که فایل شاخص وارد شده باشد
                if فایل_شاخص is not None:
                    داده_شاخص = pd.read_csv(فایل_شاخص)
                    آلفا_بتا = محاسبه_آلفا_بتا(nav, داده_شاخص)
                    شاخص_ها = شاخص_ها.merge(آلفا_بتا, on="scheme_code", how="left")
                else:
                    شاخص_ها["alpha"] = float("nan")
                    شاخص_ها["beta"] = float("nan")

                رتبه_ها = رتبه_بندی(شاخص_ها)

            st.success("تحلیل با موفقیت انجام شد.")
            st.subheader("نتیجه رتبه بندی")
            st.dataframe(رتبه_ها, use_container_width=True)

            # فایل خروجی را برای دانلود آماده می کنیم
            خروجی = رتبه_ها.to_csv(index=False).encode("utf-8-sig")
            st.download_button(
                "دانلود نتیجه به صورت CSV",
                data=خروجی,
                file_name="fund_ranking.csv",
                mime="text/csv"
            )

    except Exception as خطا:
        st.error("مشکلی پیش آمد: " + str(خطا))
