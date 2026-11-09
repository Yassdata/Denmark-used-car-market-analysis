# Power BI report setup

Open [DanishUsedCarDemand.pbip](DanishUsedCarDemand.pbip) in Power BI Desktop and select **Refresh**. The model contains the synthetic demo vehicle table. For a manual build, use the model and page settings below.

## Semantic model

1. Import `output/demo_vehicles.csv` as one table named `Vehicles`.
2. Set `vehicleid`, `makename`, `modelname`, `fueltype`, and `transmissiontype` to Text. Set the two 90-day flags to Whole number and mileage to Decimal number. Set `pricedate`, `marketentrydate`, and `marketexitdate` to Date and `datasnapshotdate` to Date/time.
3. Create the measures in [measures.dax](measures.dax) individually. Format the two counts as whole numbers and **Recorded 90-Day Sell-Through** as a percentage with two decimals.

## Report page

- **Cards** for eligible cars, sold within 90 days, and recorded sell-through.
- **Brand ranking** using `makename` and the rate, sorted descending. Add eligible cars and the sample size note to the tooltip. Show brands with an eligible count above zero.
- **Model table** with brand, model, eligible cars, sold within 90 days, the rate, and the sample size note.
- **Slicers** for brand, model, fuel type, transmission, and mileage in km. Set the brand slicer to filter the model slicer and verify that Toyota displays Corolla and Yaris. Test that the slicers filter the cards, ranking, and table.
- **Subtitle** that labels the data as a synthetic demo. Add a metric tooltip that explains that a recorded sale is inferred from listing activity.

The small-sample note flags 1–29 eligible cars so readers can see when a rate rests on a small group. An empty selection has a blank rate.

## Verify the demo

| Selection | Eligible | Sold within 90 days | Rate |
|---|---:|---:|---:|
| All vehicles | 290 | 179 | 61.72% |
| Toyota, Corolla, Hybrid, Automatic, 40,000–100,000 km | 12 | 7 | 58.33% |

Cross-check the filtered result in SQLite and Python.

```sh
python validate_sell_through.py output/demo_vehicles.csv \
  --brand Toyota --model Corolla --fuel Hybrid --transmission Automatic \
  --min-mileage 40000 --max-mileage 100000
```
