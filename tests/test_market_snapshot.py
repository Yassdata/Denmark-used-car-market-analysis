import tempfile
import unittest
from pathlib import Path

from build_market_snapshot import build_market_snapshot, read_snapshots


class MarketSnapshotTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.source = Path(directory.name) / "snapshots.csv"
        self.source.write_text(
            "vehicleid,country,pricedate,datasnapshotdate,marketexitdate,sold,forsale,"
            "makename,modelname,fueltype,transmissiontype,odometerkm,extra\n"
            "1,DK,2024-11-01,2025-01-02,,0,1,Toyota,Corolla,Hybrid,Auto,45000,x\n"
            "1,DK,2024-12-01,2025-01-02,2024-11-17,1,0,Toyota,Corolla,Hybrid,Auto,45000,x\n"
            "1,DK,2025-01-01,2025-01-02,2024-11-17,1,0,Toyota,Corolla,Hybrid,Auto,46000,x\n"
            "2,DK,2024-12-01,2025-01-02,2024-11-16,1,0,VW,Golf,Petrol,Manual,70000,x\n"
            "3,DK,2025-01-01,2025-01-02,2024-12-31,1,0,Toyota,Corolla,Hybrid,Auto,46000,x\n"
            "4,DK,2025-01-01,2025-01-02,,0,1,VW,Polo,Petrol,Manual,-1,x\n"
            "4,DK,2025-01-01,2025-01-01,,0,0,VW,Polo,Petrol,Manual,50000,x\n"
            "5,DK,2024-12-01,2025-01-02,,0,1,VW,Polo,Petrol,Manual,50000,x\n"
            "6,SE,2025-01-01,2025-01-02,,0,1,VW,Polo,Petrol,Manual,50000,x\n",
            encoding="utf-8",
        )

    def test_reads_project_columns_and_keeps_danish_rows(self):
        snapshots = read_snapshots(self.source)
        self.assertEqual(len(snapshots), 8)
        self.assertNotIn("extra", snapshots.columns)
        self.assertEqual(snapshots["pricedate"].min().date().isoformat(), "2024-11-01")

    def test_counts_current_stock_and_deduplicates_sales_in_the_45_day_window(self):
        market = build_market_snapshot(read_snapshots(self.source)).set_index("vehicleid")
        self.assertTrue(market.index.is_unique)
        self.assertEqual(market["active_inventory"].to_dict(), {"4": 1, "1": 0, "3": 0})
        self.assertEqual(market["sold_last_45d"].to_dict(), {"4": 0, "1": 1, "3": 1})
        self.assertEqual(market.at["1", "odometerkm"], 46000)
        self.assertTrue(market["odometerkm"].isna().loc["4"])
