import argparse
import sqlite3
from contextlib import closing
from pathlib import Path

import pandas as pd


SPECIFICATIONS = ["makename", "modelname", "fueltype", "transmissiontype"]
FLAGS = ["eligible_90d", "sold_within_90d"]
KEYS = ["scope", "makename", "modelname"]
SQL = Path(__file__).with_suffix(".sql")


def python_summary(vehicles: pd.DataFrame, filters: dict) -> pd.DataFrame:
    # I apply the same selections in pandas so I can check the SQL result independently.
    for column in SPECIFICATIONS:
        if filters[column] is not None:
            vehicles = vehicles.loc[vehicles[column].eq(filters[column])]
    if filters["min_mileage"] is not None:
        vehicles = vehicles.loc[vehicles["odometerkm"].ge(filters["min_mileage"])]
    if filters["max_mileage"] is not None:
        vehicles = vehicles.loc[vehicles["odometerkm"].le(filters["max_mileage"])]

    overall = pd.DataFrame([vehicles[FLAGS].sum()]).assign(scope="overall")
    brands = vehicles.groupby("makename", dropna=False)[FLAGS].sum().reset_index().assign(scope="brand")
    models = vehicles.groupby(["makename", "modelname"], dropna=False)[FLAGS].sum().reset_index().assign(scope="model")
    totals = pd.concat([overall, brands, models], ignore_index=True).rename(columns={"eligible_90d": "eligible"})
    totals["rate"] = totals["sold_within_90d"].div(totals["eligible"].where(totals["eligible"].ne(0)))
    return totals


def validate(vehicles: pd.DataFrame, **filters) -> pd.DataFrame:
    selections = dict.fromkeys([*SPECIFICATIONS, "min_mileage", "max_mileage"])
    selections.update(filters)
    with closing(sqlite3.connect(":memory:")) as database:
        vehicles.to_sql("vehicles", database, index=False)
        actual = pd.read_sql_query(SQL.read_text(encoding="utf-8"), database, params=selections)

    expected = python_summary(vehicles, selections)
    for summary in (actual, expected):
        summary[KEYS] = summary[KEYS].astype("string")
        summary["rate"] = summary["rate"].astype(float)
    actual = actual.sort_values(KEYS, na_position="first", ignore_index=True)
    expected = expected[actual.columns].sort_values(KEYS, na_position="first", ignore_index=True)
    pd.testing.assert_frame_equal(actual, expected, check_dtype=False, check_exact=False)
    return actual


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare the SQLite and pandas sell-through results.")
    parser.add_argument("source", type=Path)
    parser.add_argument("--brand", dest="makename")
    parser.add_argument("--model", dest="modelname")
    parser.add_argument("--fuel", dest="fueltype")
    parser.add_argument("--transmission", dest="transmissiontype")
    parser.add_argument("--min-mileage", type=float)
    parser.add_argument("--max-mileage", type=float)
    selections = vars(parser.parse_args())
    vehicles = pd.read_csv(
        selections.pop("source"), usecols=[*SPECIFICATIONS, "odometerkm", *FLAGS],
        dtype=dict.fromkeys(SPECIFICATIONS, "string"),
    )
    summary = validate(vehicles, **selections)
    print(f"Pandas and SQLite match across {len(summary):,} summary rows.")
    print(summary.loc[summary["scope"].eq("overall"), ["eligible", "sold_within_90d", "rate"]].to_string(index=False))


if __name__ == "__main__":
    main()
