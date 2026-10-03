"""Round-4 check of the three edited passages in the live #525 body.

Usage: python verify_round4.py REVIEW_ROOT RAW_FRS_DIR > round4-results.json

Prints aggregates and pass/fail flags only. Survey support is a threshold
flag (at least 10 distinct survey households), never a count; groups that
may be small are reported as existence flags. No survey record is read out.
"""

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT, RAW = Path(sys.argv[1]), Path(sys.argv[2])
SE = ["FT_SELF_EMPLOYED", "PT_SELF_EMPLOYED"]
out = {}


def ge10(households):
    return int(pd.Series(households).nunique()) >= 10


def tab(name, cols):
    df = pd.read_csv(
        RAW / f"{name}.tab", sep="\t", low_memory=False, usecols=lambda c: c.lower() in cols
    )
    df.columns = df.columns.str.lower()
    return df.apply(pd.to_numeric, errors="coerce")


# --- Edit 3: side trades (raw FRS 2024-25) ------------------------------------
hh = tab("househol", {"sernum", "gross4"})
ad = tab("adult", {"sernum", "empstati", "seincam2", "inearns"}).merge(hh, on="sernum")
not_se = ~ad.empstati.isin([3, 4])
profit = not_se & (ad.seincam2 > 0)
nonzero = not_se & (ad.seincam2 != 0)
above = profit & (ad.seincam2 > ad.inearns.clip(lower=0))
w = ad.gross4
out["side_trades"] = {
    "profit_adults": int(profit.sum()),
    "profit_weighted_m": round(float(w[profit].sum() / 1e6), 4),
    "profit_households_ge_10": ge10(ad.sernum[profit]),
    # The loss group may be small: only its existence and the rounding of the
    # all-non-zero total are reported, never its size.
    "loss_group_exists": bool((not_se & (ad.seincam2 < 0)).any()),
    "nonzero_weighted_rounds_to_same_2dp": round(float(w[nonzero].sum() / 1e6), 2)
    == round(float(w[profit].sum() / 1e6), 2),
    "above_pay_adults": int(above.sum()),
    "above_pay_weighted_m": round(float(w[above].sum() / 1e6), 4),
    "above_pay_subset_of_profit": bool((above <= profit).all()),
    "above_pay_all_employees": bool(ad.empstati[above].isin([1, 2]).all()),
    "above_pay_households_ge_10": ge10(ad.sernum[above]),
    "profit_not_above_households_ge_10": ge10(ad.sernum[profit & ~above]),
}

# --- Map enhanced-FRS rows to survey households --------------------------------
# Build order (create_datasets.py): impute_income stacks the SPI copy with
# household ids offset by FRS max + 1; impute_capital_gains stacks a clone of
# everything offset by the then max + 1; stack_cgt_band_donors stacks donors
# offset by the then max + 1; clone_and_assign with one clone keeps ids.
with pd.HDFStore(ROOT / "data-build/efrs_branch.h5", mode="r") as s:
    H = s["/household"]
    P = s["/person"][
        ["person_id", "person_household_id", "employment_status", "self_employment_income", "age"]
    ]
spi, cg, don = (
    H.household_is_spi_synthetic.to_numpy(),
    H.household_is_capital_gains_clone.to_numpy(),
    H.household_is_cgt_band_donor.to_numpy(),
)
hid = H.household_id.to_numpy(np.int64)
m2 = hid[~don].max()  # max id before the donor stack
m1 = hid[~don & ~cg].max()  # max id before the capital-gains clone
m0 = hid[~don & ~cg & ~spi].max()  # max FRS id before the SPI copy
src = hid.copy()
src = np.where(don, src - (m2 + 1), src)
is_cg_after = src > m1
src = np.where(is_cg_after, src - (m1 + 1), src)
is_spi_after = src > m0
src = np.where(is_spi_after, src - (m0 + 1), src)
# Donors copy existing (possibly clone or SPI) households, so their flags
# carry over; the arithmetic must agree with the flags for every household.
out["mapping"] = {
    "frs_ids_are_sernums": bool(set(hid[~don & ~cg & ~spi]) <= set(hh.sernum)),
    "all_sources_are_frs_sernums": bool(set(src) <= set(hid[~don & ~cg & ~spi])),
    "cg_flag_matches_offset": bool(np.array_equal(is_cg_after, cg)),
    "spi_flag_matches_offset": bool(np.array_equal(is_spi_after, spi)),
}
size = P.groupby("person_household_id").size()
src_of = pd.Series(src, index=hid)
out["mapping"]["household_sizes_match_source"] = bool(
    np.array_equal(size.reindex(hid).to_numpy(), size.reindex(src).to_numpy())
)

# --- Edit 2: SPI-copy shares ----------------------------------------------------
P = P.merge(
    H[["household_id", "household_weight", "household_is_spi_synthetic", "household_is_capital_gains_clone"]],
    left_on="person_household_id",
    right_on="household_id",
)
P["survey"] = src_of.reindex(P.person_household_id).to_numpy()
sestat = P.employment_status.astype(str).isin(SE)
prof = P.self_employment_income > 0
copy = P.household_is_spi_synthetic
shares = {}
for scope, base in {
    "copy_rows": copy,
    "copy_rows_excl_cg_clone": copy & ~P.household_is_capital_gains_clone,
}.items():
    for age_lab, age_ok in {"16_plus": P.age >= 16, "18_plus": P.age >= 18, "all_ages": P.age >= 0}.items():
        for grp, g in {"se_status": sestat, "other": ~sestat}.items():
            m = base & age_ok & g
            shares[f"{scope}|{age_lab}|{grp}"] = {
                "rows_share_pct": round(float((m & prof).sum() / m.sum() * 100), 3),
                "weighted_share_pct": round(
                    float(P.household_weight[m & prof].sum() / P.household_weight[m].sum() * 100), 3
                )
                if P.household_weight[m].sum() > 0
                else None,
                "numerator_households_ge_10": ge10(P.survey[m & prof]),
                "complement_households_ge_10": ge10(P.survey[m & ~prof]),
            }
out["spi_shares"] = shares
out["se_status_copy_rows_all_16_plus"] = bool((P.age[copy & sestat] >= 16).all())

# --- Edit 1: "Smaller offsetting changes" in the SPI-copy net fall ---------------
pid_spi = pd.Series(P.household_is_spi_synthetic.to_numpy(), index=P.person_id)
pid_src = pd.Series(P.survey.to_numpy(), index=P.person_id)
imp = {}
for year in range(2025, 2031):
    b = np.load(ROOT / f"impact/base_{year}.npz", allow_pickle=True)
    p = np.load(ROOT / f"impact/pr_{year}.npz", allow_pickle=True)
    assert np.array_equal(b["bu_benunit_id"], p["bu_benunit_id"])
    assert np.array_equal(b["p_person_id"], p["p_person_id"])
    units, pu, bw = b["bu_benunit_id"], b["p_benunit_id_of_person"], b["bu_benunit_weight"]
    pspi = pid_spi.reindex(b["p_person_id"]).to_numpy()
    psrc = pid_src.reindex(b["p_person_id"]).to_numpy()
    uspi = pd.Series(pspi).groupby(pu).first().reindex(units).to_numpy()
    d = p["bu_universal_credit"] - b["bu_universal_credit"]
    newly = ~b["p_uc_mif_applies"].astype(bool) & p["p_uc_mif_applies"].astype(bool)
    removed = b["p_uc_mif_applies"].astype(bool) & ~p["p_uc_mif_applies"].astype(bool)
    u_new = np.isin(units, pu[newly])
    u_rem = np.isin(units, pu[removed])

    def sup(mask):
        return psrc[np.isin(pu, units[mask])]

    m = uspi
    fall, rise, tiny = m & (d < -0.5), m & (d > 0.5), m & (d != 0) & (np.abs(d) <= 0.5)
    net = float((d * bw)[m].sum() / 1e9)
    gross_fall = float((d * bw)[fall].sum() / 1e9)
    imp[str(year)] = {
        "spi_net_bn": round(net, 3),
        "spi_rises_exist": bool(rise.any()),
        "spi_rises_under_10_households": not ge10(sup(rise)),
        "spi_rises_smaller_than_falls": float((d * bw)[rise].sum()) < -gross_fall * 1e9,
        "spi_gross_fall_exceeds_net": gross_fall < net,
        "spi_falls_ge_10_households": ge10(sup(fall)),
        "spi_all_falls_in_newly_floored_units": not bool((fall & ~u_new).any()),
        "spi_rises_all_outside_newly_floored_units": not bool((rise & u_new).any()),
        "spi_rises_all_in_floor_removed_units": bool((~rise | u_rem).all()),
        "spi_tiny_changes_are_not_falls_outside_new": not bool((tiny & (d < 0) & ~u_new).any()),
        "spi_tiny_changes_under_1gbp": bool((np.abs(d[tiny]) < 1).all()),
    }
out["impact_spi"] = imp
print(json.dumps(out, indent=1))
