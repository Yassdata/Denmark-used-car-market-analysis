import unittest

import pandas as pd

from validate_sell_through import validate


class SellThroughTests(unittest.TestCase):
    def setUp(self):
        self.vehicles = pd.DataFrame(
            [
                ("Toyota", "Corolla", "Hybrid", "Auto", 45000, 1, 1),
                ("Toyota", "Corolla", "Hybrid", "Auto", 55000, 1, 0),
                ("Toyota", "Corolla", "Hybrid", "Auto", 50000, 0, 0),
                ("Toyota", "Yaris", "Petrol", "Manual", 40000, 1, 1),
                ("VW", "Golf", "Petrol", "Manual", 65000, 1, 0),
            ],
            columns=["makename", "modelname", "fueltype", "transmissiontype", "odometerkm", "eligible_90d", "sold_within_90d"],
        )

    def test_compares_totals_and_brand_and_model_rates(self):
        summary = validate(self.vehicles)
        overall = summary.loc[summary["scope"].eq("overall")].iloc[0]
        self.assertEqual((overall["eligible"], overall["sold_within_90d"], overall["rate"]), (4, 2, 0.5))
        toyota = summary.loc[summary["scope"].eq("brand") & summary["makename"].eq("Toyota")].iloc[0]
        self.assertAlmostEqual(toyota["rate"], 2 / 3)
        corolla = summary.loc[summary["modelname"].eq("Corolla")].iloc[0]
        self.assertEqual(corolla["rate"], 0.5)

    def test_combines_filters_and_leaves_empty_rate_blank(self):
        summary = validate(self.vehicles, makename="Toyota", modelname="Corolla", fueltype="Hybrid",
                           transmissiontype="Auto", min_mileage=45000, max_mileage=50000)
        overall = summary.loc[summary["scope"].eq("overall")].iloc[0]
        self.assertEqual((overall["eligible"], overall["sold_within_90d"], overall["rate"]), (1, 1, 1.0))
        empty = validate(self.vehicles, makename="Missing")
        self.assertEqual(empty["eligible"].tolist(), [0])
        self.assertTrue(pd.isna(empty["rate"].iloc[0]))
