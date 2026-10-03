"""Sanity check for verify_round3.py's 50p threshold: booleans and £ magnitudes of noise only."""

import json, sys
import numpy as np, pandas as pd

R = sys.argv[1]
with pd.HDFStore(f"{R}/data-build/efrs_branch.h5", mode="r") as s:
    hh = s["/household"][["household_id", "household_is_spi_synthetic"]]
    person = s["/person"][["person_id", "person_household_id"]]
spi = pd.Series(
    person.person_household_id.isin(
        set(hh.household_id[hh.household_is_spi_synthetic])
    ).to_numpy(),
    index=person.person_id,
)
out = {}
for y in range(2025, 2031):
    b, p = (
        np.load(f"{R}/impact/{v}_{y}.npz", allow_pickle=True) for v in ("base", "pr")
    )
    units, pu, bw = (
        b["bu_benunit_id"],
        b["p_benunit_id_of_person"],
        b["bu_benunit_weight"],
    )
    d = p["bu_universal_credit"] - b["bu_universal_credit"]
    newly = ~b["p_uc_mif_applies"].astype(bool) & p["p_uc_mif_applies"].astype(bool)
    drv = np.isin(units, pu[newly])
    uspi = (
        pd.Series(spi.loc[b["p_person_id"]].to_numpy(), index=pu)
        .groupby(level=0)
        .first()
        .reindex(units)
        .to_numpy()
    )
    tiny = (d != 0) & (np.abs(d) <= 0.5)
    out[y] = {
        "any_tiny_nonzero": bool(tiny.any()),
        "max_abs_tiny_gbp": round(float(np.abs(d[tiny]).max()), 4)
        if tiny.any()
        else 0.0,
        "spi_tiny_outside_newly_floored_weighted_gbp_k": round(
            float(np.sum((d * bw)[tiny & uspi & ~drv]) / 1e3), 3
        ),
    }
print(json.dumps(out))
