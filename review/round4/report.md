# Review round 4: PolicyEngine/policyengine-uk-data#525 (head dc2abf7, PR body only)

Live body last edited 3 Oct 12:59:57Z. Head is still `dc2abf7`. `gh pr checks` exits 0 (4/4 pass), the PR is MERGEABLE (CLEAN) and still a draft, with no reviews or comments.

## Only the three stated edits changed

The body round 3 reviewed is the 3 Oct 11:25:44Z revision in GitHub's edit history. The live body equals the 12:59:57Z revision byte for byte. A line diff between the two touches four lines in three places, and nothing else:

| Line | Before | After |
|---|---|---|
| 40 | report self-employment income | report **a** self-employment **profit** |
| 81 | Only 7% of copy rows with a self-employed status | About 7% of **adult** copy rows with a self-employed status |
| 82 | 5.5% of the other copy rows | About 5% of the other **adult** copy rows |
| 126 | Smaller changes in both directions are inside the net figure | Smaller **offsetting** changes are inside the net figure |

Every other figure and sentence is unchanged, so the round-3 whole-body checks still hold.

## Each edit against the saved data

Script `verify_round4.py`, output `round4-results.json`. It prints aggregates and threshold flags only. It maps enhanced-FRS rows to survey households from the build code. The SPI copy, capital-gains clone and band donors each stack with ids offset by the previous max + 1, and one OA clone keeps ids unchanged. The mapping is checked three ways: every mapped id is an FRS sernum, the offsets agree with the three flags for every household, and every household's size equals its source household's size.

1. **"Smaller offsetting changes" (line 126): correct.** For 2026-27 the SPI-copy net is -£0.337bn, shown as £0.34bn. In every year from 2025-26 to 2030-31:
   - every SPI-copy fall is in a unit the floor newly applies to;
   - the only other changes are rises, all in units where the floor stops applying;
   - the rises rest on fewer than 10 survey households and are smaller than the falls.

   So the hidden changes run one way and offset the net fall, which "offsetting" says. The changes under 50p are under £1 and include no fall outside the newly floored units. The sentence gives no size, count or cause for the rise.
2. **"About 7%" / "About 5% of adult copy rows" (lines 81-82): correct.**

   | Row scope (branch build `efrs_branch.h5`) | SE status | Other |
   |---|---|---|
   | SPI-copy rows aged 16+ (the author's definition) | 6.69% | 5.255% |
   | Aged 18+ | 6.70% | 5.38% |
   | Copy rows excluding capital-gains clones, 16+ | 6.70% | 5.25% |
   | All ages (not "adult") | 6.69% | 4.32% |

   Every adult definition rounds to 7% and 5%. Round 3's FRS-adult-row figure, 5.39%, does too. Every self-employed-status copy row is aged 16 or over. Numerators and complements each rest on at least 10 survey households in every scope.
3. **"227 adults (0.49m weighted) report a self-employment profit" (line 40): correct.** Raw FRS 2024-25, EMPSTATI not 3/4 and SEINCAM2 > 0: 227 adults, 0.4862m weighted, at least 10 households. Some such adults report a loss, so "profit" is more accurate than "income". The loss group's size is not published. Including it leaves the weighted figure at 0.49m, so nothing can be differenced. The following sentence still holds: 65 adults (0.1417m), all employees (EMPSTATI 1/2), a subset of the 227. The 65 and the remaining 162 each rest on at least 10 households.

## Disclosure

- No record-level values. Every new or changed figure rests on at least 10 distinct survey households, for both numerator and complement.
- The new shares are coarser than before ("about 5%" instead of 5.5%), so they open no differencing route.
- The line-126 wording shows that some of the suppressed rises are in the SPI copy, but not their count or size. Line 130 already says rising units exist and rest on fewer than 10 households.
- The new revision adds nothing disclosive to the edit history. Round 3's note on older revisions stands unchanged.

## Non-blocking notes (no change needed)

- The shares count rows, as the body says. Shares weighted by calibrated weight are higher (about 9% and 7%) but tell the same story. The copy enters with zero weight, so a row share is the natural measure of what the SPI model draws.
- SEINCAM2 > 0 is profit or estimated drawings (the glossary quote on line 26). The body uses "profit" for positive self-employment income throughout, so line 40 is consistent.

VERDICT: APPROVE
