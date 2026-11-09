import unittest

import pandas as pd

from validate_market_days_supply import validate


class MarketDaysSupplyTests(unittest.TestCase):
    def setUp(self):
        self.vehicles = pd.DataFrame(
            [
                ("Toyota", "Corolla", "Hybrid", "Auto", 45000, 1, 0),
                ("Toyota", "Corolla", "Hybrid", "Auto", 45000, 0, 1),
                ("Toyota", "Corolla", "Hybrid", "Auto", 55000, 1, 0),
                ("Toyota", "Yaris", "Petrol", "Manual", 40000, 0, 1),
                ("VW", "Golf", "Petrol", "Manual", 65000, 1, 0),
            ],
            columns=["makename", "modelname", "fueltype", "transmissiontype", "odometerkm", "active_inventory", "sold_last_45d"],
        )

    def test_compares_totals_and_brand_and_model_rates(self):
        summary = validate(self.vehicles)
        overall = summary.loc[summary["scope"].eq("overall")].iloc[0]
        self.assertEqual((overall["active_inventory"], overall["sold_last_45d"], overall["market_days_supply"]), (3, 2, 67.5))
        toyota = summary.loc[summary["scope"].eq("brand") & summary["makename"].eq("Toyota")].iloc[0]
        self.assertEqual(toyota["market_days_supply"], 45)
        corolla = summary.loc[summary["modelname"].eq("Corolla")].iloc[0]
        self.assertEqual(corolla["market_days_supply"], 90)

    def test_combines_filters_and_leaves_mds_blank_when_no_cars_sold(self):
        summary = validate(self.vehicles, makename="Toyota", modelname="Corolla", fueltype="Hybrid",
                           transmissiontype="Auto", min_mileage=45000, max_mileage=50000)
        overall = summary.loc[summary["scope"].eq("overall")].iloc[0]
        self.assertEqual((overall["active_inventory"], overall["sold_last_45d"], overall["market_days_supply"]), (1, 1, 45.0))
        no_sales = validate(self.vehicles, makename="VW")
        self.assertTrue(no_sales["market_days_supply"].isna().all())
