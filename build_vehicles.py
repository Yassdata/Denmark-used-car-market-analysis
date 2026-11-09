import argparse
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd


SPECIFICATIONS = ["makename", "modelname", "fueltype", "transmissiontype"]
DATES = ["pricedate", "datasnapshotdate", "marketentrydate", "marketexitdate"]
DTYPES = {
    "vehicleid": "string",
    "country": "category",
    "sold": "Int8",
    "daystosell": "float64",
    "odometerkm": "float64",
    **dict.fromkeys(SPECIFICATIONS, "category"),
}


def read_snapshots(source: Path) -> pd.DataFrame:
    # I only need Danish snapshots and the fields used in the report.
    snapshots = pd.read_csv(source, usecols=[*DTYPES, *DATES], dtype=DTYPES)
    snapshots = snapshots.loc[snapshots["country"].eq("DK")].copy()
    for column in DATES:
        snapshots[column] = pd.to_datetime(snapshots[column], format="ISO8601")
    if snapshots.empty or snapshots[["vehicleid", "pricedate", "datasnapshotdate"]].isna().any().any():
        raise ValueError("Danish snapshots need a vehicle ID, observation date, and export timestamp.")
    if not snapshots["sold"].isin([0, 1]).all():
        raise ValueError("The sold flag must be 0 or 1.")
    return snapshots


def build_vehicle_table(snapshots: pd.DataFrame) -> pd.DataFrame:
    # I use the latest observation so each car contributes once to the comparison.
    first_snapshot = snapshots["pricedate"].min()
    last_snapshot = snapshots["pricedate"].max()
    vehicles = (
        snapshots.sort_values(["pricedate", "datasnapshotdate"])
        .drop_duplicates("vehicleid", keep="last")
        .copy()
    )

    sold = vehicles["sold"].eq(1)
    sold_vehicles = vehicles.loc[sold]
    inclusive_days = (sold_vehicles["marketexitdate"] - sold_vehicles["marketentrydate"]).dt.days + 1
    if not (inclusive_days.ge(1) & inclusive_days.eq(sold_vehicles["daystosell"])).all():
        raise ValueError("A latest sold record has an inconsistent entry date, exit date, or duration.")

    # I count the entry day and use the day before the final snapshot as the coverage end.
    last_eligible_entry = last_snapshot - pd.Timedelta(days=90)
    eligible = vehicles["marketentrydate"].between(first_snapshot, last_eligible_entry)
    vehicles["eligible_90d"] = eligible.astype("int8")
    vehicles["sold_within_90d"] = (eligible & sold & vehicles["daystosell"].le(90)).astype("int8")
    vehicles["odometerkm"] = vehicles["odometerkm"].where(vehicles["odometerkm"].ge(0))
    return vehicles


def main() -> None:
    parser = argparse.ArgumentParser(description="Build one Danish record per vehicle for Power BI.")
    parser.add_argument("source", type=Path)
    parser.add_argument("--output", type=Path, default=Path("output/vehicles.csv"))
    args = parser.parse_args()
    if args.source.resolve() == args.output.resolve():
        parser.error("Choose an output path separate from the source CSV.")

    snapshots = read_snapshots(args.source)
    vehicles = build_vehicle_table(snapshots)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(dir=args.output.parent) as directory:
        staged = Path(directory) / args.output.name
        vehicles.to_csv(staged, index=False)
        staged.replace(args.output)
    print(f"{len(snapshots):,} snapshots → {len(vehicles):,} vehicles → {args.output}")


if __name__ == "__main__":
    main()
