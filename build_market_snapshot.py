import argparse
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd


SPECIFICATIONS = ["makename", "modelname", "fueltype", "transmissiontype"]
DATES = ["pricedate", "datasnapshotdate", "marketexitdate"]
LOOKBACK_DAYS = 45
DTYPES = {
    "vehicleid": "string",
    "country": "category",
    "sold": "Int8",
    "forsale": "Int8",
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
    if not snapshots[["sold", "forsale"]].isin([0, 1]).all().all():
        raise ValueError("The sold and forsale flags must be 0 or 1.")
    sold = snapshots.loc[snapshots["sold"].eq(1)]
    if not sold["marketexitdate"].lt(sold["pricedate"]).all():
        raise ValueError("Recorded sales need an exit date before their observation date.")
    return snapshots


def build_market_snapshot(snapshots: pd.DataFrame) -> pd.DataFrame:
    as_of = snapshots["pricedate"].max()
    window_start = as_of - pd.Timedelta(days=LOOKBACK_DAYS)
    if window_start < snapshots["pricedate"].min():
        raise ValueError("The latest snapshot needs 45 days of prior data coverage.")

    # I keep one version of each monthly observation before counting stock or sales.
    recent = snapshots.loc[snapshots["pricedate"].ge(window_start)]
    recent = recent.sort_values("datasnapshotdate", kind="stable").drop_duplicates(
        ["vehicleid", "pricedate"], keep="last"
    )
    fields = ["vehicleid", *SPECIFICATIONS, "odometerkm"]
    active = recent.loc[recent["pricedate"].eq(as_of) & recent["forsale"].eq(1), fields]

    # I count each sold vehicle once, using its latest qualifying recorded exit.
    sold = recent.loc[
        recent["sold"].eq(1) & recent["marketexitdate"].between(window_start, as_of, inclusive="left")
    ].sort_values(["marketexitdate", "pricedate"])
    sold = sold.drop_duplicates("vehicleid", keep="last")[fields]
    market = pd.concat([
        active.assign(active_inventory=1, sold_last_45d=0),
        sold.assign(active_inventory=0, sold_last_45d=1),
    ], ignore_index=True)
    market.insert(0, "as_of_date", as_of)
    market["odometerkm"] = market["odometerkm"].where(market["odometerkm"].ge(0))
    return market


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the latest Danish market snapshot for Power BI.")
    parser.add_argument("source", type=Path)
    parser.add_argument("--output", type=Path, default=Path("output/market_snapshot.csv"))
    args = parser.parse_args()
    if args.source.resolve() == args.output.resolve():
        parser.error("Choose an output path separate from the source CSV.")

    snapshots = read_snapshots(args.source)
    market = build_market_snapshot(snapshots)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(dir=args.output.parent) as directory:
        staged = Path(directory) / args.output.name
        market.to_csv(staged, index=False)
        staged.replace(args.output)
    print(f"Snapshot date: {snapshots['pricedate'].max():%Y-%m-%d}. Wrote {len(market):,} market rows to {args.output}.")


if __name__ == "__main__":
    main()
