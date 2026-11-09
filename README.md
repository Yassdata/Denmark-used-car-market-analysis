# Danish Used-Car Market Days Supply

How much competing stock is available relative to the recent sales pace? The report helps dealers compare sourcing options across brand, model, fuel type, transmission, and mileage.

## How it works

```mermaid
flowchart LR
    A[Monthly observations] --> B[Python market snapshot]
    B --> C[SQLite validation]
    B --> D[Power BI semantic model]
    D --> E[Interactive report]
```

The public demo uses simulated vehicle histories. Its figures illustrate the workflow.

![Static preview of Market Days Supply by brand using synthetic data](power-bi/preview.svg)

## Run the demo

From the project folder, use a Python environment with pandas. The dependency is listed in `requirements.txt`. SQLite is included with Python.

```sh
python build_market_snapshot.py data/demo_snapshots.csv --output output/demo_market_snapshot.csv
python validate_market_days_supply.py output/demo_market_snapshot.csv
python -m unittest discover -s tests -v
```

The synthetic snapshot dated **1 January 2025** has **102 active listings** and **47 vehicles recorded as sold** over the previous 45 days, giving **97.7 days of supply**. The validator compares Python and SQLite totals overall, by brand, and by brand and model. It also accepts the report filters as command-line arguments.

## How we calculate Market Days Supply

- **Active listings.** Count distinct Danish vehicles marked `forsale = 1` on the latest `pricedate`. When a vehicle has multiple exports for the same `pricedate`, keep the newest export.
- **Recent sales.** Count distinct Danish vehicles marked `sold = 1` with a recorded exit in the 45 calendar days before the snapshot. When a vehicle appears more than once in that window, use its latest qualifying exit. Recorded exits serve as a proxy for retail sales.
- **Days of supply.** Multiply active listings by 45 and divide by recent sales for the same selection. Leave MDS blank if there are zero recent sales. A lower MDS indicates less available stock relative to the recent sales pace. [Market Days Supply methodology](https://docs.marketcheck.com/docs/api/cars/market-insights/market-days-supply)

## Power BI

Open `power-bi/DanishUsedCarDemand.pbip` in Power BI Desktop on Windows and select **Refresh** to load the embedded synthetic dataset. The measures recalculate both counts and MDS for the current selection. [Power BI project](power-bi/DanishUsedCarDemand.pbip) · [Report guide](power-bi/report.md) · [DAX measures](power-bi/measures.dax)

The automated checks verify the embedded data, model field bindings, and configured slicers. Rendering and interaction checks in Power BI Desktop are pending.
