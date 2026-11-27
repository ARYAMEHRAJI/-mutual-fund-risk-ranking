import os
import tempfile
import unittest

import numpy as np
import pandas as pd

import simple_data
import simple_database
from simple_metrics import بازدهی_در_بازه, محاسبه_شاخص_ها
from simple_ranking import رتبه_بندی, تعدیل_نوع_دارایی, انتخاب_صندوق_های_متنوع, محاسبه_وزن_سبد


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



    def test_diversified_recommendations_for_all_profiles(self):
        rows = []
        groups = [
            ("Debt - Liquid", "Liquid Fund"),
            ("Debt - Corporate Bond", "Corporate Bond Fund"),
            ("Hybrid - Balanced", "Balanced Hybrid Fund"),
            ("Hybrid - Dynamic Allocation", "Balanced Advantage Fund"),
            ("Equity - Large Cap", "Large Cap Fund"),
            ("Equity - Flexi Cap", "Flexi Cap Fund"),
            ("Equity - Sectoral", "Healthcare Sectoral Fund"),
            ("Equity - Thematic", "Healthcare Pharma Thematic Fund"),
            ("Other - Gold", "Gold ETF"),
            ("Other - Silver", "Silver ETF"),
        ]
        for i, (group, name) in enumerate(groups):
            rows.append({
                "scheme_code": str(i), "scheme_name": name,
                "fund_group": group, "score": 95 - i
            })
        data = pd.DataFrame(rows)

        for profile in ["Conservative", "Moderate", "Growth", "Aggressive"]:
            selected = انتخاب_صندوق_های_متنوع(
                data, "score", تعداد=5, حداکثر_از_هر_گروه=1, پروفایل=profile
            )
            self.assertEqual(len(selected), 5)
            self.assertLessEqual(selected["fund_group"].value_counts().max(), 1)
            sector_count = selected["fund_group"].isin(
                ["Equity - Sectoral", "Equity - Thematic"]
            ).sum()
            self.assertLessEqual(sector_count, 1)
            if profile in ["Conservative", "Moderate"]:
                self.assertEqual(sector_count, 0)
            self.assertLessEqual(
                selected["fund_group"].apply(
                    lambda g: "debt" if g.startswith("Debt") or g == "Other - Debt Index"
                    else "hybrid" if g.startswith("Hybrid")
                    else "equity" if g.startswith("Equity") or g == "Other - Index"
                    else "alternative"
                ).value_counts().max(),
                3
            )

    def test_healthcare_concentration_is_limited(self):
        data = pd.DataFrame([
            {"scheme_code": "1", "scheme_name": "Healthcare Fund A", "fund_group": "Equity - Sectoral", "score": 99},
            {"scheme_code": "2", "scheme_name": "Pharma Healthcare Fund B", "fund_group": "Equity - Thematic", "score": 98},
            {"scheme_code": "3", "scheme_name": "Large Cap Fund", "fund_group": "Equity - Large Cap", "score": 97},
            {"scheme_code": "4", "scheme_name": "Liquid Fund", "fund_group": "Debt - Liquid", "score": 96},
            {"scheme_code": "5", "scheme_name": "Balanced Hybrid Fund", "fund_group": "Hybrid - Balanced", "score": 95},
            {"scheme_code": "6", "scheme_name": "Gold Fund", "fund_group": "Other - Gold", "score": 94},
            {"scheme_code": "7", "scheme_name": "Edelweiss MSCI India Domestic & World Healthcare 45 Index Fund", "fund_group": "Other - Index", "score": 100},
        ])
        selected = انتخاب_صندوق_های_متنوع(data, "score", تعداد=5, پروفایل="Moderate")
        self.assertFalse({"1", "2", "7"}.intersection(set(selected["scheme_code"])))


    def test_portfolio_weights_sum_to_100_for_all_profiles(self):
        data = pd.DataFrame([
            {"scheme_name": "Debt A", "fund_group": "Debt - Liquid"},
            {"scheme_name": "Debt B", "fund_group": "Other - Debt Index"},
            {"scheme_name": "Hybrid A", "fund_group": "Hybrid - Balanced"},
            {"scheme_name": "Equity A", "fund_group": "Equity - Large Cap"},
            {"scheme_name": "Equity B", "fund_group": "Other - Index"},
            {"scheme_name": "Gold", "fund_group": "Other - Gold"}
        ])
        for profile in ["Conservative", "Moderate", "Growth", "Aggressive"]:
            result = محاسبه_وزن_سبد(data, profile)
            self.assertAlmostEqual(result["portfolio_weight"].sum(), 100.0, places=1)
            self.assertTrue((result["portfolio_weight"] >= 0).all())

    def test_lower_volatility_gets_higher_weight_within_same_asset_group(self):
        data = pd.DataFrame([
            {"scheme_name": "Low volatility equity", "fund_group": "Equity - Large Cap", "volatility": 0.10},
            {"scheme_name": "High volatility equity", "fund_group": "Equity - Flexi Cap", "volatility": 0.20},
            {"scheme_name": "Gold", "fund_group": "Other - Gold", "volatility": 0.15}
        ])
        result = محاسبه_وزن_سبد(data, "Growth")
        self.assertGreater(result.loc[0, "portfolio_weight"], result.loc[1, "portfolio_weight"])
        self.assertAlmostEqual(result["portfolio_weight"].sum(), 100.0, places=1)

    def test_missing_volatility_uses_equal_weights_within_group(self):
        data = pd.DataFrame([
            {"scheme_name": "Equity A", "fund_group": "Equity - Large Cap", "volatility": 0.10},
            {"scheme_name": "Equity B", "fund_group": "Equity - Flexi Cap", "volatility": np.nan},
            {"scheme_name": "Gold", "fund_group": "Other - Gold", "volatility": 0.15}
        ])
        result = محاسبه_وزن_سبد(data, "Growth")
        self.assertAlmostEqual(
            result.loc[0, "portfolio_weight"],
            result.loc[1, "portfolio_weight"],
            places=1
        )
        self.assertAlmostEqual(result["portfolio_weight"].sum(), 100.0, places=1)

    def test_portfolio_weight_cap_is_40_and_preserves_group_total_when_possible(self):
        data = pd.DataFrame([
            {"scheme_name": "Debt A", "fund_group": "Debt - Liquid", "volatility": 0.20},
            {"scheme_name": "Debt B", "fund_group": "Debt - Corporate Bond", "volatility": 0.10},
            {"scheme_name": "Debt C", "fund_group": "Other - Debt Index", "volatility": 0.01},
            {"scheme_name": "Hybrid A", "fund_group": "Hybrid - Balanced", "volatility": 0.15},
            {"scheme_name": "Hybrid B", "fund_group": "Hybrid - Conservative", "volatility": 0.18}
        ])
        result = محاسبه_وزن_سبد(data, "Conservative")
        self.assertLessEqual(result["portfolio_weight"].max(), 40.0)
        self.assertAlmostEqual(result["portfolio_weight"].sum(), 100.0, places=1)
        debt_total = result.loc[
            result["fund_group"].str.startswith("Debt") |
            (result["fund_group"] == "Other - Debt Index"),
            "portfolio_weight"
        ].sum()
        self.assertAlmostEqual(debt_total, 68.4, places=1)

    def test_missing_asset_types_are_redistributed(self):
        data = pd.DataFrame([
            {"scheme_name": "Equity A", "fund_group": "Equity - Large Cap"},
            {"scheme_name": "Equity B", "fund_group": "Other - Index"},
            {"scheme_name": "Gold", "fund_group": "Other - Gold"}
        ])
        result = محاسبه_وزن_سبد(data, "Growth")
        self.assertAlmostEqual(result["portfolio_weight"].sum(), 100.0, places=1)
        self.assertGreater(result.loc[2, "portfolio_weight"], 0)
        self.assertAlmostEqual(
            result.loc[0, "portfolio_weight"],
            result.loc[1, "portfolio_weight"],
            places=1
        )


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
