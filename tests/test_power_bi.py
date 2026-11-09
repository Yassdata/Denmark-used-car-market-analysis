import base64
import io
import json
import re
import unittest
from pathlib import Path

import pandas as pd

from build_market_snapshot import build_market_snapshot, read_snapshots


ROOT = Path(__file__).resolve().parents[1]
POWER_BI = ROOT / "power-bi"


class PowerBIProjectTests(unittest.TestCase):
    def test_model_embeds_only_the_reproducible_demo(self):
        model = json.loads((POWER_BI / "DanishUsedCarDemand.SemanticModel/model.bim").read_text())
        table = model["model"]["tables"][0]
        expression = "\n".join(table["partitions"][0]["source"]["expression"])
        encoded = re.search(r'Binary\.FromText\("([\w+/=]+)"', expression).group(1)
        actual = pd.read_csv(io.BytesIO(base64.b64decode(encoded)))
        demo = build_market_snapshot(read_snapshots(ROOT / "data/demo_snapshots.csv"))
        expected = pd.read_csv(io.StringIO(demo.to_csv(index=False)))
        pd.testing.assert_frame_equal(actual, expected)

    def test_visuals_bind_to_the_model_and_brand_filters_model(self):
        shortcut = json.loads((POWER_BI / "DanishUsedCarDemand.pbip").read_text())
        report = POWER_BI / shortcut["artifacts"][0]["report"]["path"]
        report_definition = json.loads((report / "definition.pbir").read_text())
        model = report / report_definition["datasetReference"]["byPath"]["path"]
        table = json.loads((model / "model.bim").read_text())["model"]["tables"][0]
        bindings = {"Column": {c["name"] for c in table["columns"]},
                    "Measure": {m["name"] for m in table["measures"]}}

        page = next((report / "definition/pages").glob("*/page.json"))
        page_definition = json.loads(page.read_text())
        slicers = {}
        for path in page.parent.glob("visuals/*/visual.json"):
            visual = json.loads(path.read_text())
            config = visual["visual"]
            for role in config.get("query", {}).get("queryState", {}).values():
                for projection in role["projections"]:
                    kind, field = next(iter(projection["field"].items()))
                    self.assertEqual(field["Expression"]["SourceRef"]["Entity"], table["name"])
                    self.assertIn(field["Property"], bindings[kind])
                    if config["visualType"] == "slicer":
                        slicers[field["Property"]] = visual["name"]

        self.assertEqual(set(slicers), {"makename", "modelname", "fueltype", "transmissiontype", "odometerkm"})
        self.assertIn({"source": slicers["makename"], "target": slicers["modelname"], "type": "DataFilter"},
                      page_definition["visualInteractions"])
