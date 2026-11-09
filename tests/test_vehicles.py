import tempfile
import unittest
from pathlib import Path

from build_vehicles import build_vehicle_table, read_snapshots


class VehicleTableTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.source = Path(directory.name) / "snapshots.csv"
        self.source.write_text(
            "vehicleid,country,pricedate,datasnapshotdate,marketentrydate,marketexitdate,"
            "sold,daystosell,makename,modelname,fueltype,transmissiontype,odometerkm,extra\n"
            "1,DK,2024-04-01,2025-01-02,2024-01-01,2024-03-30,1,90,Toyota,Corolla,Hybrid,Auto,45000,x\n"
            "2,DK,2024-04-01,2025-01-02,2024-01-01,2024-03-31,1,91,VW,Golf,Petrol,Manual,70000,x\n"
            "3,DK,2024-05-01,2025-01-02,2024-01-01,,0,,Toyota,Corolla,Hybrid,Auto,46000,x\n"
            "3,DK,2024-03-01,2025-01-02,2024-01-01,2024-02-15,1,46,Toyota,Corolla,Hybrid,Auto,45000,x\n"
            "4,DK,2025-01-01,2025-01-02,2024-10-03,,0,,VW,Polo,Petrol,Manual,-1,x\n"
            "5,DK,2025-01-01,2025-01-02,2024-10-04,,0,,VW,Polo,Petrol,Manual,,x\n"
            "6,DK,2024-01-01,2025-01-02,2023-12-31,,0,,VW,Polo,Petrol,Manual,50000,x\n"
            "7,SE,2024-01-01,2025-01-02,2024-01-01,,0,,VW,Polo,Petrol,Manual,50000,x\n",
            encoding="utf-8",
        )

    def test_reads_project_columns_and_keeps_danish_rows(self):
        snapshots = read_snapshots(self.source)
        self.assertEqual(len(snapshots), 7)
        self.assertNotIn("extra", snapshots.columns)
        self.assertEqual(snapshots["pricedate"].min().date().isoformat(), "2024-01-01")

    def test_keeps_latest_status_and_applies_90_day_boundaries(self):
        vehicles = build_vehicle_table(read_snapshots(self.source)).set_index("vehicleid")
        self.assertTrue(vehicles.index.is_unique)
        self.assertEqual(vehicles["eligible_90d"].to_dict(), {"1": 1, "2": 1, "3": 1, "4": 1, "5": 0, "6": 0})
        self.assertEqual(vehicles["sold_within_90d"].to_dict(), {"1": 1, "2": 0, "3": 0, "4": 0, "5": 0, "6": 0})
        self.assertEqual(vehicles.at["3", "sold"], 0)
        self.assertEqual(vehicles.at["3", "odometerkm"], 46000)
        self.assertTrue(vehicles["odometerkm"].isna().loc["4"])
