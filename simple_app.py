# این فایل صفحه ساده پروژه را اجرا می کند.

import streamlit as st
import pandas as pd

from simple_data import دریافت_صندوق_ها, انتخاب_صندوق_ها, دریافت_nav
from simple_metrics import محاسبه_شاخص_ها, محاسبه_آلفا_بتا, دریافت_شاخص_بازار
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

# شاخص مرجع متناسب با گروه صندوق به صورت خودکار انتخاب می شود
شاخص_های_مرجع = {
    "Large Cap": "NIFTY 50",
    "Mid Cap": "NIFTY MIDCAP 150",
    "Small Cap": "NIFTY SMALLCAP 250",
    "Flexi Cap": "NIFTY 500",
    "Multi Cap": "NIFTY 500",
    "Focused": "NIFTY 500"
}
نام_شاخص = شاخص_های_مرجع[گروه]
st.info("شاخص مرجع خودکار: " + نام_شاخص + " TRI")

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

                # شاخص بازار را خودکار و به اندازه تاریخ NAV صندوق ها دریافت می کنیم
                with st.spinner("در حال دریافت شاخص مرجع بازار..."):
                    داده_شاخص = دریافت_شاخص_بازار(
                        نام_شاخص,
                        nav["date"].min(),
                        nav["date"].max()
                    )

                # آلفا و بتا را برای هر صندوق محاسبه می کنیم
                آلفا_بتا = محاسبه_آلفا_بتا(nav, داده_شاخص)
                شاخص_ها = شاخص_ها.merge(آلفا_بتا, on="scheme_code", how="left")

                رتبه_ها = رتبه_بندی(شاخص_ها)

            st.success("تحلیل با موفقیت انجام شد.")
            st.caption("آلفا و بتا با شاخص مرجع " + نام_شاخص + " TRI محاسبه شده اند.")
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
