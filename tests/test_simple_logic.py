import os
import tempfile
import unittest

import numpy as np
import pandas as pd

import simple_data
import simple_database
from simple_metrics import بازدهی_در_بازه, محاسبه_شاخص_ها
from simple_ranking import رتبه_بندی, تعدیل_نوع_دارایی


class TestFundRanking(unittest.TestCase):
    def make_data(self):
        rows = []
        for group in ["Debt - Liquid", "Equity - Large Cap"]:
            for i in range(4):
                rows.append({
                    "scheme_code": group + str(i),
                    "scheme_name": "Fund " + str(i),
                    "fund_group": group,
                    "return_1w": 0.01 + i * 0.001,
                    "return_1m": 0.02 + i * 0.002,
                    "return_3m": 0.04 + i * 0.003,
                    "return_6m": 0.06 + i * 0.004,
                    "return_1y": 0.10 + i * 0.01,
                    "return_3y": 0.30 + i * 0.02,
                    "volatility": 0.20 - i * 0.01,
                    "max_drawdown": -0.30 + i * 0.02,
                    "sharpe": 0.5 + i * 0.1,
                    "sortino": 0.7 + i * 0.1,
                    "metrics_as_of": "2026-11-27"
                })
        return pd.DataFrame(rows)

    def test_conservative_prefers_debt_and_aggressive_prefers_equity(self):
        result = رتبه_بندی(self.make_data())
        debt = result[result["fund_group"].str.startswith("Debt")].iloc[0]
        equity = result[result["fund_group"].str.startswith("Equity")].iloc[0]
        self.assertGreater(debt["Conservative_score"], equity["Conservative_score"])
        self.assertGreater(equity["Aggressive_score"], debt["Aggressive_score"])

    def test_conservative_profile_penalizes_aggressive_hybrid(self):
        self.assertGreater(
            تعدیل_نوع_دارایی("Hybrid - Conservative", "Conservative"),
            تعدیل_نوع_دارایی("Hybrid - Aggressive", "Conservative")
        )

    def test_small_group_scores_stay_near_middle(self):
        data = self.make_data().query("fund_group == 'Debt - Liquid'").head(2)
        result = رتبه_بندی(data)
        self.assertLess(result["return_score"].max(), 60)

    def test_missing_long_term_return_is_not_ranked(self):
        data = self.make_data()
        data.loc[0, "return_3y"] = np.nan
        result = رتبه_بندی(data)
        missing = result[result["scheme_code"] == "Debt - Liquid0"].iloc[0]
        self.assertFalse(bool(missing["eligible_for_ranking"]))
        self.assertTrue(pd.isna(missing["Conservative_rank"]))


class TestFundData(unittest.TestCase):
    def test_category_matching_is_exact(self):
        self.assertEqual(
            simple_data.پیدا_کردن_گروه("Large Cap Fund"),
            "Equity - Large Cap"
        )
        self.assertIsNone(
            simple_data.پیدا_کردن_گروه("Large & Mid Cap Fund")
        )
        self.assertEqual(
            simple_data.پیدا_کردن_گروه("Liquid Fund"),
            "Debt - Liquid"
        )
        self.assertEqual(
            simple_data.پیدا_کردن_گروه("Balanced Hybrid Fund"),
            "Hybrid - Balanced"
        )
        self.assertEqual(
            simple_data.پیدا_کردن_گروه(
                "Index Funds",
                "Nippon India Nifty AAA CPSE Bond Plus SDL Index Fund"
            ),
            "Other - Debt Index"
        )
        self.assertTrue(simple_data.تشخیص_ETF("Nippon India Nifty Pharma ETF"))
        self.assertFalse(simple_data.تشخیص_ETF("Mirae Asset NYSE FANG ETF Fund of Fund"))

    def test_fund_filters_keep_only_supported_open_direct_growth_schemes(self):
        data = pd.DataFrame([
            {
                "scheme_code": "1", "scheme_name": "Large fund",
                "is_active": True, "scheme_plan": "Direct",
                "scheme_option": "Growth", "scheme_type": "Open Ended Schemes",
                "first_date": "2020-01-01", "scheme_sub_category": "Large Cap Fund"
            },
            {
                "scheme_code": "2", "scheme_name": "Large and Mid fund",
                "is_active": True, "scheme_plan": "Direct",
                "scheme_option": "Growth", "scheme_type": "Open Ended Schemes",
                "first_date": "2020-01-01", "scheme_sub_category": "Large & Mid Cap Fund"
            },
            {
                "scheme_code": "3", "scheme_name": "Liquid fund",
                "is_active": True, "scheme_plan": "Direct",
                "scheme_option": "Growth", "scheme_type": "Open Ended Schemes",
                "first_date": "2020-01-01", "scheme_sub_category": "Liquid Fund"
            },
            {
                "scheme_code": "4", "scheme_name": "Inactive fund",
                "is_active": False, "scheme_plan": "Direct",
                "scheme_option": "Growth", "scheme_type": "Open Ended Schemes",
                "first_date": "2020-01-01", "scheme_sub_category": "Liquid Fund"
            }
        ])
        selected = simple_data.انتخاب_صندوق_ها(data)
        self.assertEqual(set(selected["scheme_code"]), {"1", "3"})
        self.assertEqual(
            selected.set_index("scheme_code").loc["3", "fund_group"],
            "Debt - Liquid"
        )

    def test_metrics_calculate_three_year_returns_from_daily_nav(self):
        dates = pd.date_range("2023-11-27", "2026-11-27", freq="B")
        nav = 100 * (1.0005 ** np.arange(len(dates)))
        data = pd.DataFrame({
            "scheme_code": "900",
            "scheme_name": "Sample Fund",
            "date": dates,
            "nav": nav
        })
        result = محاسبه_شاخص_ها(data)
        self.assertEqual(len(result), 1)
        self.assertTrue(pd.notna(result.loc[0, "return_1y"]))
        self.assertTrue(pd.notna(result.loc[0, "return_3y"]))
        self.assertGreater(result.loc[0, "volatility"], 0)

    def test_return_uses_nearby_dates_only(self):
        data = pd.DataFrame({
            "date": pd.to_datetime(["2026-01-05", "2026-01-10"]),
            "nav": [100.0, 110.0]
        })
        value = بازدهی_در_بازه(
            data, 5, pd.Timestamp("2026-01-10"), 2
        )
        self.assertAlmostEqual(value, 0.10, places=6)

        old_data = pd.DataFrame({
            "date": pd.to_datetime(["2026-01-01", "2026-01-10"]),
            "nav": [100.0, 110.0]
        })
        old_value = بازدهی_در_بازه(
            old_data, 5, pd.Timestamp("2026-01-10"), 2
        )
        self.assertTrue(pd.isna(old_value))


class TestDatabase(unittest.TestCase):
    def test_saves_all_rows_and_updates_existing_record(self):
        with tempfile.TemporaryDirectory() as folder:
            old_path = simple_database.مسیر_پایگاه
            simple_database.مسیر_پایگاه = os.path.join(folder, "test.db")
            try:
                rows = pd.DataFrame([
                    {
                        "scheme_code": "101",
                        "scheme_name": "Fund A",
                        "fund_group": "Debt - Liquid",
                        "metrics_as_of": "2026-11-27",
                        "return_1y": 0.12,
                        "return_3y": 0.35,
                        "Conservative_score": 80
                    },
                    {
                        "scheme_code": "102",
                        "scheme_name": "Fund B",
                        "fund_group": "Equity - Large Cap",
                        "metrics_as_of": "2026-11-27",
                        "return_1y": 0.20,
                        "return_3y": 0.50,
                        "Aggressive_score": 90
                    }
                ])
                simple_database.ذخیره_نتایج(rows)
                stats = simple_database.آمار_پایگاه_داده()
                self.assertEqual(stats["funds"], 2)
                self.assertEqual(stats["metrics"], 2)

                simple_database.ذخیره_نتایج(rows.iloc[[0]])
                stats = simple_database.آمار_پایگاه_داده()
                self.assertEqual(stats["funds"], 2)
                self.assertEqual(stats["metrics"], 2)
            finally:
                simple_database.مسیر_پایگاه = old_path


if __name__ == "__main__":
    unittest.main()
