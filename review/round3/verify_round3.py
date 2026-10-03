"""Round-3 check of every figure in the live #525 body, and its disclosure.

Usage: python verify_round3.py REVIEW_ROOT RAW_FRS_DIR > round3-results.json

Aggregate output only. Support is reported as a threshold boolean (at least 10
distinct survey households), never as an exact count, and money or people are
printed only for cells that pass it. No survey record is read out.
"""

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT, RAW = Path(sys.argv[1]), Path(sys.argv[2])
IMPACT = ROOT / "impact"
SE = ("FT_SELF_EMPLOYED", "PT_SELF_EMPLOYED")
T = 10
out = {}


def ok(households):
    return len(set(households)) >= T


# ---------------------------------------------------------------- raw FRS
def load(name, cols):
    df = pd.read_csv(
        RAW / f"{name}.tab",
        sep="\t",
        low_memory=False,
        usecols=lambda c: c.lower() in cols,
    )
    df.columns = df.columns.str.lower()
    return df.apply(pd.to_numeric, errors="coerce")


hh = load("househol", {"sernum", "gross4"})
ad = load(
    "adult", {"sernum", "benunit", "person", "empstati", "seincam2", "inearns"}
).merge(hh, on="sernum")
job = load("job", {"sernum", "benunit", "person", "jobtype", "profit1", "seincamt"})
main = job[job.jobtype == 1].drop_duplicates(["sernum", "benunit", "person"])
ad = ad.merge(main, on=["sernum", "benunit", "person"], how="left")
w = ad.gross4
se = ad.empstati.isin([3, 4])
side = ~se & (ad.seincam2 > 0)
over = side & (ad.seincam2 > ad.inearns.clip(lower=0))
cells = {
    "se_main_job": se,
    "se_positive": se & (ad.seincam2 > 0),
    "se_zero": se & (ad.seincam2 == 0),
    "se_negative": se & (ad.seincam2 < 0),
    "se_zero_or_negative": se & (ad.seincam2 <= 0),
    "side_trade_profit": side,
    "side_trade_above_pay": over,
    "side_trade_not_above_pay": side & ~over,
}
frs = {
    k: {
        "adults": int(m.sum()),
        "weighted_m": round(float(w[m].sum() / 1e6), 4),
        "households_ge_10": ok(ad.sernum[m]),
    }
    for k, m in cells.items()
}
frs["se_main_job_seincam2_missing"] = int((se & ad.seincam2.isna()).sum())
frs["side_trade_above_pay_all_employees"] = bool(ad.empstati[over].isin([1, 2]).all())
zero = cells["se_zero"]
for lab, cond in [
    ("profit1_eq_0", ad.profit1 == 0),
    ("seincamt_eq_0", ad.seincamt == 0),
]:
    frs[lab] = {
        "weighted_share_pct": round(
            float(w[zero & cond].sum() / w[zero].sum() * 100), 2
        ),
        "unweighted_share_pct": round(float((zero & cond).sum() / zero.sum() * 100), 2),
        "numerator_households_ge_10": ok(ad.sernum[zero & cond]),
        "complement_households_ge_10": ok(ad.sernum[zero & ~cond]),
    }
frs["side_trade_negative_seincam2_any"] = bool((~se & (ad.seincam2 < 0)).any())
out["frs_section"] = frs


# ---------------------------------------------------- enhanced FRS mapping
def survey_ids(hht):
    original = (
        ~hht.household_is_spi_synthetic
        & ~hht.household_is_capital_gains_clone
        & ~hht.household_is_cgt_band_donor
    )
    frs_max = int(hht.loc[original, "household_id"].max())
    cg = (
        int(
            hht.loc[
                hht.household_is_capital_gains_clone & ~hht.household_is_cgt_band_donor,
                "household_id",
            ].min()
        )
        - 1
    )
    donor = int(hht.loc[~hht.household_is_cgt_band_donor, "household_id"].max()) + 1

    def f(ids):
        i = np.asarray(ids, dtype=np.int64)
        i = np.where(i >= donor, i - donor, i)
        i = np.where(i > cg, i - cg, i)
        return np.where(i > frs_max, i - frs_max - 1, i)

    return f


child = load("child", {"sernum", "person"})


def frs_adult_flag(per):
    """Mark persons whose FRS donor row is an adult row (not a dependent child)."""
    people = pd.concat(
        [ad[["sernum", "person"]].assign(adult=True), child.assign(adult=False)]
    )
    people["pidx"] = people.groupby("sernum").person.rank(method="first").astype(int)
    per = per.copy()
    per["pidx"] = (
        per.groupby("person_household_id").person_id.rank(method="first").astype(int)
    )
    return (
        per.merge(
            people[["sernum", "pidx", "adult"]],
            left_on=["survey", "pidx"],
            right_on=["sernum", "pidx"],
            how="left",
        )
        .adult.fillna(False)
        .to_numpy(dtype=bool)
    )


def spi_shares(path):
    with pd.HDFStore(path, mode="r") as s:
        hht = s["/household"]
        per = s["/person"][
            [
                "person_id",
                "person_household_id",
                "employment_status",
                "self_employment_income",
                "age",
            ]
        ]
    f = survey_ids(hht)
    per = per.merge(
        hht[
            [
                "household_id",
                "household_is_spi_synthetic",
                "household_is_capital_gains_clone",
                "household_is_cgt_band_donor",
            ]
        ],
        left_on="person_household_id",
        right_on="household_id",
    )
    per["survey"] = f(per.person_household_id)
    per = per.sort_values(["person_household_id", "person_id"]).reset_index(drop=True)
    per["frs_adult"] = frs_adult_flag(per)
    res = {
        "original_ids_are_sernums": bool(
            set(
                hht.loc[
                    ~hht.household_is_spi_synthetic
                    & ~hht.household_is_capital_gains_clone
                    & ~hht.household_is_cgt_band_donor,
                    "household_id",
                ]
            )
            <= set(hh.sernum)
        ),
        "se_status_rows_all_frs_adults": bool(
            per.frs_adult[per.employment_status.astype(str).isin(SE)].all()
        ),
    }
    for scope, m0 in [
        ("all_spi_rows", per.household_is_spi_synthetic),
        (
            "spi_rows_excl_cg_clones",
            per.household_is_spi_synthetic
            & ~per.household_is_capital_gains_clone
            & ~per.household_is_cgt_band_donor,
        ),
    ]:
        sestat = per.employment_status.astype(str).isin(SE)
        prof = per.self_employment_income > 0
        r = {}
        for lab, m in [
            ("se_status", m0 & sestat),
            ("other_all_ages", m0 & ~sestat),
            ("other_age_16_plus", m0 & ~sestat & (per.age >= 16)),
            ("other_frs_adult_rows", m0 & ~sestat & per.frs_adult),
        ]:
            r[lab] = {
                "share_with_profit_pct": round(
                    float((m & prof).sum() / m.sum() * 100), 3
                ),
                "numerator_households_ge_10": ok(per.survey[m & prof]),
                "complement_households_ge_10": ok(per.survey[m & ~prof]),
            }
        res[scope] = r
    return res


out["spi_copy_shares"] = {
    "branch_build": spi_shares(ROOT / "data-build/efrs_branch.h5"),
    "snapshot_efrs_copy": spi_shares(ROOT / "data/efrs_copy.h5"),
}

# ----------------------------------------------------------------- impact
with pd.HDFStore(ROOT / "data-build/efrs_branch.h5", mode="r") as s:
    hht = s["/household"]
    person = s["/person"][["person_id", "person_household_id"]]
f = survey_ids(hht)
survey_of = pd.Series(f(person.person_household_id), index=person.person_id)
spi_hh = set(hht.loc[hht.household_is_spi_synthetic, "household_id"])
spi_of = pd.Series(
    person.person_household_id.isin(spi_hh).to_numpy(), index=person.person_id
)


def run(name, year):
    return dict(np.load(IMPACT / f"{name}_{year}.npz", allow_pickle=True))


def wsum(x, wt, scale):
    return float(np.sum(np.asarray(x, dtype=float) * wt.astype(float)) / scale)


impact = {}
for year in range(2025, 2031):
    b, p, st, lit = (run(v, year) for v in ("base", "pr", "status", "literal"))
    for r in (p, st, lit):
        assert np.array_equal(b["p_person_id"], r["p_person_id"]) and np.array_equal(
            b["bu_benunit_id"], r["bu_benunit_id"]
        )
    units, pu, bw, pw = (
        b["bu_benunit_id"],
        b["p_benunit_id_of_person"],
        b["bu_benunit_weight"],
        b["p_person_weight"],
    )
    psurvey = survey_of.loc[b["p_person_id"]].to_numpy()
    pspi = spi_of.loc[b["p_person_id"]].to_numpy()
    uspi = pd.Series(pspi, index=pu).groupby(level=0).first().reindex(units).to_numpy()

    def sup(unit_mask):
        return psurvey[np.isin(pu, units[unit_mask])]

    def units_with(person_mask):
        return np.isin(units, pu[person_mask])

    uc = {
        k: r["bu_universal_credit"]
        for k, r in (("base", b), ("pr", p), ("status", st), ("literal", lit))
    }
    y = {}
    for v in ("pr", "status"):
        d = uc[v] - uc["base"]
        y[f"{v}_change_bn"] = round(wsum(d, bw, 1e9), 4)
        y[f"{v}_cell_ge_10"] = ok(sup(np.abs(d) > 0.5))
    d_ps = uc["status"] - uc["pr"]
    y["pr_vs_status_difference_ge_10"] = ok(sup(np.abs(d_ps) > 0.5))
    y["pr_vs_literal_difference_ge_10"] = ok(
        sup(np.abs(uc["literal"] - uc["pr"]) > 0.5)
    )
    y["pc_hb_ctr_unchanged_pr_status"] = all(
        np.array_equal(b[f"bu_{x}"], r[f"bu_{x}"])
        for r in (p, st)
        for x in ("pension_credit", "housing_benefit", "council_tax_benefit")
    )
    d = uc["pr"] - uc["base"]
    y["hh_net_minus_uc_change_abs_gbp_m"] = round(
        abs(wsum(p["hh_net"] - b["hh_net"], b["hh_w"], 1e6) - wsum(d, bw, 1e6)), 3
    )

    # SPI-copy mechanism: who drives the net fall, and which directions sit inside it.
    mif0, mif1 = b["p_uc_mif_applies"].astype(bool), p["p_uc_mif_applies"].astype(bool)
    newly, removed = ~mif0 & mif1, mif0 & ~mif1
    sestat = np.isin(p["p_employment_status"].astype(str), SE)
    sei = p["p_self_employment_income"]
    g0, g1 = (
        b["p_uc_is_in_gainful_self_employment"].astype(bool),
        p["p_uc_is_in_gainful_self_employment"].astype(bool),
    )
    y["newly_floored_all_se_status_zero_profit"] = bool(
        np.all(sestat[newly] & (sei[newly] == 0) & g1[newly] & ~g0[newly])
    )
    y["newly_flagged_are_se_status_zero_profit"] = bool(
        np.array_equal(g1 & ~g0, sestat & (sei == 0))
    )
    y["unflagged_are_side_trades_profit_not_above_pay"] = bool(
        np.all(~sestat[g0 & ~g1] & (sei[g0 & ~g1] > 0))
    )
    drv, rem = units_with(newly), units_with(removed)
    for src, m in (("spi", uspi), ("frs", ~uspi)):
        # Only the published net is printed in money. Component money is withheld:
        # with the net it would give the under-10 residual by differencing.
        net = wsum(d[m], bw[m], 1e9)
        s = {"net_bn": round(net, 4)}
        classes = {
            "newly_floored_unit": m & drv,
            "newly_and_removed_unit": m & drv & rem,
            "floor_removed_only_unit": m & rem & ~drv,
            "no_floor_change_unit": m & ~drv & ~rem,
        }
        for lab, cm in classes.items():
            for direction, dm in (("fall", d < -0.5), ("rise", d > 0.5)):
                s[f"{lab}_{direction}"] = {
                    "exists": bool((cm & dm).any()),
                    "ge_10": ok(sup(cm & dm)),
                }
        drv_bn = wsum(d[m & drv], bw[m & drv], 1e9)
        s["all_falls_in_newly_floored_units"] = not bool((m & ~drv & (d < -0.5)).any())
        s["newly_floored_units_fall_at_least_net_fall"] = drv_bn <= net
        s["changes_outside_newly_floored_units_are_rises_only"] = bool(
            np.all(d[m & ~drv & (np.abs(d) > 0.5)] > 0)
        )
        y[src] = s

    if year == 2026:
        in0, in1 = (
            b["p_universal_credit_of_unit"] > 0,
            p["p_universal_credit_of_unit"] > 0,
        )
        y["headline"] = {
            "uc_total_bn": [round(wsum(uc[k], bw, 1e9), 4) for k in ("base", "pr")],
            "gainful_m": [
                round(wsum(r["p_uc_is_in_gainful_self_employment"], pw, 1e6), 4)
                for r in (b, p)
            ],
            "floor_m": [round(wsum(r["p_uc_mif_applies"], pw, 1e6), 4) for r in (b, p)],
            "floor_in_uc_units_k": [
                round(wsum(mif0 & in0, pw, 1e3), 3),
                round(wsum(mif1 & in1, pw, 1e3), 3),
            ],
            "uc_falling_units_k": round(wsum(d < -0.5, bw, 1e3), 3),
            "net_caseload_change_k": round(
                wsum(
                    (uc["pr"] > 0).astype(int) - (uc["base"] > 0).astype(int), bw, 1e3
                ),
                3,
            ),
        }
        pu_sup = lambda pm: psurvey[pm]
        y["support"] = {
            "uc_total_cells_ge_10": all(ok(sup(uc[k] > 0)) for k in ("base", "pr")),
            "gainful_cells_ge_10": ok(pu_sup(g0)) and ok(pu_sup(g1)),
            "gainful_difference_set_ge_10": ok(pu_sup(g0 != g1)),
            "floor_cells_ge_10": ok(pu_sup(mif0)) and ok(pu_sup(mif1)),
            "floor_difference_set_ge_10": ok(pu_sup(mif0 != mif1)),
            "floor_in_uc_cells_ge_10": ok(pu_sup(mif0 & in0))
            and ok(pu_sup(mif1 & in1)),
            "floor_in_uc_difference_set_ge_10": ok(
                pu_sup((mif0 & in0) != (mif1 & in1))
            ),
            "falling_units_ge_10": ok(sup(d < -0.5)),
            "caseload_change_set_ge_10": ok(sup((uc["pr"] > 0) != (uc["base"] > 0))),
            "rising_units_under_10": not ok(sup(d > 0.5)),
            "changed_without_fall_under_10": not ok(
                set(sup(np.abs(d) > 0.5)) - set(sup(d < -0.5))
            ),
            "poverty_bhc_ahc_changed_people_under_10": all(
                not ok(pu_sup(b[v].astype(bool) != p[v].astype(bool)))
                for v in (
                    "p_in_poverty_bhc",
                    "p_in_poverty_ahc",
                    "p_in_deep_poverty_ahc",
                )
            ),
        }
    impact[str(year)] = y
out["impact"] = impact
print(json.dumps(out, indent=1))
