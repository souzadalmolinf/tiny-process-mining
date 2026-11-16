"""Load a small, synthetic online order event log with PM4Py."""

from pathlib import Path

import pandas as pd
import pm4py


DATA_FILE = Path(__file__).parent / "data" / "sample_orders.csv"


def load_log() -> pd.DataFrame:
    events = pd.read_csv(DATA_FILE)
    return pm4py.format_dataframe(
        events,
        case_id="case_id",
        activity_key="activity",
        timestamp_key="timestamp",
        timest_format="%Y-%m-%dT%H:%M:%S%z",
    )


def main() -> None:
    log = load_log()
    print(f"Loaded {len(log)} events across {log['case:concept:name'].nunique()} orders.")
    print(f"Activities: {log['concept:name'].nunique()}")
    print("\nFirst events:")
    print(
        log[["case:concept:name", "concept:name", "time:timestamp"]]
        .head(8)
        .to_string(index=False)
    )


if __name__ == "__main__":
    main()
