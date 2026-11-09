# Power BI report setup

Open `DanishUsedCarDemand.pbip` in Power BI Desktop and select **Refresh** to load the synthetic market snapshot. [Power BI project](DanishUsedCarDemand.pbip)

## Semantic model

1. For a manual build, import `output/demo_market_snapshot.csv` as `MarketSnapshot`.
2. Set `vehicleid`, `makename`, `modelname`, `fueltype`, and `transmissiontype` to Text. Set `active_inventory` and `sold_last_45d` to Whole number, `odometerkm` to Decimal number, and `as_of_date` to Date.
3. Create the measures individually. Format the counts as whole numbers, Market Days Supply as a decimal with one digit after the decimal point, and Snapshot Date as a date. [DAX measures](measures.dax)

## Report page

- **Cards** for active listings, recorded sales over 45 days, Market Days Supply, and snapshot date.
- **Brand ranking** using `makename` and Market Days Supply, sorted from lowest to highest. Add both counts and the sales coverage note to the tooltip.
- **Model table** with brand, model, both counts, Market Days Supply, and the sales coverage note.
- **Slicers** for brand, model, fuel type, transmission, and mileage in km. Set the brand slicer to filter the model slicer and verify that Toyota displays Corolla and Yaris. Test that the slicers filter the cards, ranking, and table.
- **Subtitle** that labels the data as a synthetic demo. Add a metric tooltip that explains that a recorded sale is inferred from listing activity.

Market Days Supply stays blank when there are zero recent sales. The snapshot date stays fixed as users change filters.

## Verify the demo

| Selection | Active listings | Recorded sales in 45 days | MDS |
|---|---:|---:|---:|
| All vehicles | 102 | 47 | 97.7 days |
| Toyota, Corolla, Hybrid, Automatic, 40,000–120,000 km | 7 | 2 | 157.5 days |

Cross-check the filtered result in SQLite and Python.

```sh
python validate_market_days_supply.py output/demo_market_snapshot.csv \
  --brand Toyota --model Corolla --fuel Hybrid --transmission Automatic \
  --min-mileage 40000 --max-mileage 120000
```
