# Danish Used-Car Demand Dashboard

Which brands and models have the highest recorded 90-day sell-through? The report is designed for dealers comparing sourcing options across brand, model, fuel type, transmission, and mileage.

## How it works

```mermaid
flowchart LR
    A[Monthly snapshots] --> B[Python vehicle table]
    B --> C[SQLite validation]
    B --> D[Power BI semantic model]
    D --> E[Interactive report]
```

The public demo uses simulated vehicle histories. Its figures illustrate the workflow.

![Static preview of brand rankings and eligible vehicle counts from the synthetic demo](power-bi/preview.svg)

## Run the demo

From the project folder, use a Python environment with pandas. The dependency is listed in `requirements.txt`. SQLite is included with Python.

```sh
python build_vehicles.py data/demo_snapshots.csv --output output/demo_vehicles.csv
python validate_sell_through.py output/demo_vehicles.csv
python -m unittest discover -s tests -v
```

The demo returns **179 of 290 eligible vehicles**, or **61.72%**. The validator compares Python and SQLite totals overall, by brand, and by brand and model. It also accepts the report filters as command-line arguments.

## How we count vehicles

- **One row per vehicle.** The same car appears across monthly snapshots, and a recorded exit can repeat. We use the latest `pricedate` so each car contributes once, with its most recent recorded status. If two rows share the latest `pricedate`, we prefer the newer export timestamp.
- **A full 90-day window.** The market entry date must fall on or after the first monthly snapshot. Day 90 must fall before the final monthly snapshot, whose observations reflect prior dates. The day of entry is day one.
- **Recorded sell-through.** The numerator counts eligible cars whose latest row is marked sold and whose recorded selling time is 90 days or less. The denominator includes all eligible cars, including cars whose latest status is unsold. The sale flag is a proxy based on listing activity.

## Power BI

Open [DanishUsedCarDemand.pbip](power-bi/DanishUsedCarDemand.pbip) in Power BI Desktop on Windows and select **Refresh** to load the embedded synthetic dataset. The [report guide](power-bi/report.md) describes the model, slicers, and expected results. The [DAX measures](power-bi/measures.dax) recalculate the counts and rate for the current selection.

The automated checks verify the embedded data, model field bindings, and configured slicers. Rendering and interaction checks in Power BI Desktop are pending.
