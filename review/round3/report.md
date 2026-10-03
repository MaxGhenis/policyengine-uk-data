# Independent review, round 3: policyengine-uk-data #525 (PR body only)

Reviewed the live body of [#525](https://github.com/PolicyEngine/policyengine-uk-data/pull/525), last edited 2026-10-03T11:25:44Z, at head `dc2abf7` (unchanged, draft). CI is 4/4 green on that head (`gh pr checks` exit 0) and the PR is `MERGEABLE`.

Evidence:
- the GitHub edit history, used to diff the live body against the revision round 2 reviewed (03:02Z);
- the saved run outputs in `~/reviews/uk-data-se-zero-profit-2026-10-02/impact/`;
- the raw FRS 2024-25 tab files;
- [verify_round3.py](verify_round3.py) → [round3-results.json](round3-results.json);
- [tiny_delta_check.py](tiny_delta_check.py) → [tiny-delta-results.json](tiny-delta-results.json).

Both scripts print aggregates only. They report support as a boolean (10 or more survey households). They withhold component money wherever, combined with a published total, it would give an under-10 residual. No microsimulation was rerun, and this report contains no record values and no under-10 cell.

| Check | Result |
|---|---|
| 1a. 5.72m → 5.71m | **PASS** |
| 1b. Exact support counts removed | **PASS** |
| 1c. £0.34bn as the net SPI-copy fall | **FAIL (one sentence)**: the net framing and the driver are right; "smaller changes in both directions" is contradicted by the arrays |
| 2. Disclosure, entire live body | **PASS** |
| 3. Every number against saved outputs | **PASS**, with two optional precision edits to figures the edit did not touch |

## 1. Round-2 required changes

The edit changed only three blocks: the gainful count; the SPI/FRS bullets; and the survey-support bullet together with the deleted "Survey support for the other figures" paragraph. Nothing else in the body moved.

**1a — PASS.** The table now reads 5.71m. The double-precision value is 5.7147m.

**1b — PASS.**
- The overall, falling-UC, SPI, FRS and sensitivity-difference household counts are gone.
- The body now says "Each published figure rests on at least 10 distinct survey households … Exact support counts are not given, because differences between them could reveal smaller cells."
- That claim holds (§2).
- Neither under-10 complement found in round 2 (changed-without-fall, SPI∩FRS) can be rebuilt from the live body.

**1c — the net and the driver PASS; the last sentence FAILS.**
- "The net fall in the SPI copy's households is £0.34bn" (−0.3374) and "The net fall in the original FRS households is £0.16bn" (−0.1608) are correct.
- "It is driven by the floor newly applying to SPI-copy rows whose employment status says self-employed but whose SPI-imputed profit is zero" is correct:
  - every person whose floor newly applies has self-employed status and zero profit;
  - the newly flagged set is exactly status self-employed with zero profit;
  - in every year 2025-26 to 2030-31, the benefit units containing those people carry a fall at least as large as the whole SPI net.
- "Smaller changes in both directions are inside the net figure and are not shown" is false. In all six years, in the SPI copy:
  - every UC fall sits in a unit where the floor newly applies;
  - no such unit has a rise;
  - no unit with both a newly applying and a removed floor changes UC;
  - units with no change in floor status have no change in UC;
  - the only changes outside the driver units are **rises**, in units where the floor no longer applies (side trades whose profit is not above pay). They rest on fewer than 10 survey households.
- So the smaller component runs in one direction, not both.
- The 50p threshold does not hide falls. Nonzero deltas under 50p reach 12p at most and contribute £0 in SPI-copy units outside the driver ([tiny-delta-results.json](tiny-delta-results.json)).

  Fix: "Smaller offsetting changes are inside the net figure and are not shown."
  - "Offsetting" implies rises, which the current text already implies, so the fix discloses nothing new.
  - Do not name the mechanism or count of the suppressed rise.

## 2. Disclosure pass over the entire live body — PASS

**Record-level values.** None. Every number is a weighted or unweighted aggregate. Ann and Ira are ADM examples, and test amounts are not in the body.

**Every published figure has 10+ distinct survey households.** Each item below was checked, along with its complement:

- *What the FRS says.* The published cells are:

  | Cell | Adults | Weighted |
  |---|---|---|
  | Self-employed main job | 2,110 | 4.20m |
  | Positive SEINCAM2 | 1,893 | 3.82m |
  | Zero SEINCAM2 | 176 | 0.31m |
  | Negative SEINCAM2 | 41 | 0.07m |
  | Zero or negative | 217 | 0.38m |
  | Side trades with profit | 227 | 0.49m |
  | Profit above pay | 65 | 0.14m |
  | Complement: profit not above pay | 162 | |

  - Each has 10+ households.
  - The two 21% shares are weighted (20.72%, 21.18%); numerators and complements both have 10+ households.
  - The two zeros are acceptable structural zeros, not 1–9 cells: no missing SEINCAM2 among self-employed main jobs, and no non-employee among the 65.
- *SPI copy shares.* Numerators and complements of the 7% and 5.5% shares have 10+ households in both the snapshot and the branch build.
- *Impact.*
  - All cells pass: both UC totals, both gainful, floor and floor-in-UC-units counts, the falling-UC units, the net caseload change set, and the SPI and FRS net money.
  - Every annual PR and sensitivity spending cell passes.
  - The set behind each base-to-PR difference (gainful, floor, floor in UC units) has 10+ households.

**Exact support counts.** None remain for any Impact figure. The FRS section still gives unweighted adult sample sizes, unchanged since round 1. Each is a published cell size with 10+ households, and every difference among them also has 10+:
- 2,110 = 1,893 + 176 + 41;
- 217 = 176 + 41;
- 227 = 65 + 162.

None combines with an Impact figure, which uses a different dataset, weights and year.

**Differencing.**
- *Total vs split.* −0.50 = −0.34 + −0.16 is a partition of money with both parts at 10+. No count now allows the source-household intersection to be recovered.
- *Falling units and caseload.* "97k falling" and "−37k net caseload" do not recover the rising-UC or joining units. Falls include continuing recipients, and leavers are unpublished.
- *Floor in UC units.* 302k → 349k is a net of several flows, and its change set has 10+.
- *Cross-variant.* The PR-versus-sensitivity difference has 10+ in every year. The literal variant, whose difference from the PR is under 10 in every year, appears nowhere in the body.
- *Suppressed cells.* Rising-UC and poverty-change cells are under 10 (confirmed for 2026-27) and are only described as suppressed. The new SPI sentence publishes no value, and the proposed fix publishes none either.

**Outside the live body (not a required change).** Earlier revisions in GitHub's edit history are still open to anyone who can view the PR. The 3 Oct 03:02Z revision shows the exact support counts, and the 2 Oct 15:55Z revision shows the round-1 loss-group percentage. The response relies on Max's rulings d838 and d826 ("current texts are redacted; old revisions stay"):
- they were made for policyengine-uk #1999 and #1952, not #525;
- d838 covered the same class: small survey cells in edit history;
- the analogy is sound, but there is no #525-specific ruling.

## 3. Numbers against saved outputs — PASS

| Figure in body | Recomputed | |
|---|---|---|
| PR row 2025–2030 (£bn) | −0.4756, −0.4983, −0.4960, −0.4933, −0.4906, −0.4861 | −0.48/−0.50/−0.50/−0.49/−0.49/−0.49 ✓ |
| Sensitivity row | −0.4086, −0.4268, −0.4274, −0.4278, −0.4275, −0.4263 | −0.41/−0.43 ×5 ✓ |
| UC 2026 | £78.3737bn → £77.8755bn | £78.37bn / £77.88bn ✓ |
| Gainful | 4.4502m → 5.7147m | 4.45m / 5.71m ✓ |
| Floor applies | 3.5941m → 4.5667m | 3.59m / 4.57m ✓ |
| … in UC units | 301.954k → 348.816k | 302k / 349k ✓ |
| UC falls | 96.696k units | 97k ✓ |
| Net caseload | −36.803k | 37k ✓ |
| SPI / FRS net | −0.3374 / −0.1608 | £0.34bn / £0.16bn ✓ |
| HNI change = UC change | gap under £500 every year | ✓ |
| PC/HB/CTR unchanged | exact, PR and sensitivity, all years | ✓ |
| FRS section | see §2 | ✓ |
| 7% SE-status copy rows with profit | 6.85% snapshot / 6.69% branch | ✓ |
| Lock no-op, 7 mutants killed | `lock_noop_check.out`, `mutation_check.out` | ✓ |

**Optional (not touched by this edit; no disclosure effect):**
1. "5.5% of the other copy rows draw a profit" reproduces the saved probe: 5.54% of *adult* non-self-employed copy rows in the pre-branch snapshot. On the branch build it is 5.39%; counting children, as "the other copy rows" literally does, it is 4.3–4.4%. Suggest: "about 5% of the other adult copy rows".
2. "227 adults … report self-employment income" counts positive SEINCAM2 only, and some adults whose main job is not self-employment report a loss. Suggest "report a self-employment profit". Publish no count for the loss group.

## Required changes

1. Replace "Smaller changes in both directions are inside the net figure and are not shown." with "Smaller offsetting changes are inside the net figure and are not shown.", or other wording that claims no SPI-copy falls outside the newly floored units. Nothing else blocks. A body whose only change is that wording needs no further data check.

VERDICT: REQUEST_CHANGES
