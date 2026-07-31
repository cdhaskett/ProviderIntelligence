"""Create a deliberately messy version of providers.csv for the cleaning demo.

This takes the clean synthetic providers and injects the kinds of problems you
meet in real municipal / field-service data: inconsistent casing, stray
whitespace, mixed delimiters, type-mangled numbers, malformed ZIPs, missing
values, and duplicate rows. `notebooks/cleaning.ipynb` puts it back together.

Run:  python make_dirty_data.py
Output: data_raw/providers_dirty.csv
"""

from __future__ import annotations

import random
from pathlib import Path

import numpy as np
import pandas as pd

SEED = 7
HERE = Path(__file__).parent

STATE_FULL = {"IN": "Indiana", "OH": "Ohio", "KY": "Kentucky", "IL": "Illinois", "MI": "Michigan", "WI": "Wisconsin"}


def dirty(df: pd.DataFrame) -> pd.DataFrame:
    rng = random.Random(SEED)
    df = df.copy()
    df["rating"] = df["rating"].astype(object)
    df["utilization_pct"] = df["utilization_pct"].astype(object)
    df["zip_code"] = df["zip_code"].astype(str)

    for i in df.index:
        # 1. Stray whitespace on names
        if rng.random() < 0.25:
            df.at[i, "provider_name"] = f"  {df.at[i, 'provider_name']} "
        # 2. Inconsistent city casing / whitespace
        if rng.random() < 0.20:
            df.at[i, "city"] = df.at[i, "city"].upper()
        elif rng.random() < 0.15:
            df.at[i, "city"] = f"{df.at[i, 'city']} "
        # 3. Inconsistent state encoding
        r = rng.random()
        if r < 0.15:
            df.at[i, "state"] = df.at[i, "state"].lower()
        elif r < 0.25:
            df.at[i, "state"] = STATE_FULL.get(df.at[i, "state"], df.at[i, "state"])
        # 4. Mixed service delimiters
        if rng.random() < 0.35 and " | " in str(df.at[i, "services"]):
            df.at[i, "services"] = str(df.at[i, "services"]).replace(" | ", rng.choice([", ", ",", " / "]))
        # 5. rating as text with units
        if rng.random() < 0.20:
            df.at[i, "rating"] = f"{df.at[i, 'rating']} stars"
        # 6. utilization with a % sign
        if rng.random() < 0.20:
            df.at[i, "utilization_pct"] = f"{df.at[i, 'utilization_pct']}%"
        # 7. malformed ZIPs (float-like, spaces)
        r = rng.random()
        if r < 0.12:
            df.at[i, "zip_code"] = f"{df.at[i, 'zip_code']}.0"
        elif r < 0.20:
            df.at[i, "zip_code"] = f" {df.at[i, 'zip_code']} "
        # 8. agreement status casing
        if rng.random() < 0.25:
            df.at[i, "agreement_status"] = rng.choice(
                [df.at[i, "agreement_status"].lower(), df.at[i, "agreement_status"].upper()]
            )
        # 9. sprinkle missing values
        if rng.random() < 0.05:
            df.at[i, "rating"] = ""
        if rng.random() < 0.05:
            df.at[i, "zip_code"] = ""
        if rng.random() < 0.02:
            df.at[i, "latitude"] = np.nan
            df.at[i, "longitude"] = np.nan

    # 10. duplicate a handful of rows
    dupes = df.sample(6, random_state=SEED)
    df = pd.concat([df, dupes], ignore_index=True)

    # 11. one fully blank row
    blank = {c: "" for c in df.columns}
    df = pd.concat([df, pd.DataFrame([blank])], ignore_index=True)

    return df.sample(frac=1, random_state=SEED).reset_index(drop=True)


def main() -> None:
    clean = pd.read_csv(HERE / "data" / "providers.csv", dtype={"zip_code": str})
    messy = dirty(clean)
    out_dir = HERE / "data_raw"
    out_dir.mkdir(exist_ok=True)
    messy.to_csv(out_dir / "providers_dirty.csv", index=False)
    print(f"Wrote {len(messy)} rows to {out_dir / 'providers_dirty.csv'} "
          f"({len(messy) - len(clean)} extra from duplicates/blank row)")


if __name__ == "__main__":
    main()
