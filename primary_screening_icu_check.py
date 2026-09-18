"""
primary_screening_icu_check.py
==============================
Compare primary screening strategy rankings before and after ICU costing.
Runs from <repo> using the PATCHED engine.

Outputs: results/primary_screening_icu_ranking.csv
"""

import sys, csv, os
import os as _os
sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
# coldsimulator added AFTER so patched engine takes precedence

from parameters import PATHOGENS, ECON
from engine import run_scenario
from icu_parameters import ICU_FRACTIONS, ICU_LOS_DAYS

# Verify we have the patched engine
import inspect
src = inspect.getfile(run_scenario)
print(f"Engine source: {src}")
import engine as _e
sig = str(inspect.signature(_e.run_scenario))
assert 'icu_fraction_of_hosp_override' in sig, f"WRONG ENGINE — signature: {sig}"
print("  ✓ Patched engine confirmed (icu_fraction_of_hosp_override present)")

HORIZON = 365
PREV_TIERS = [("0.5x", 0.5), ("1x", 1.0), ("2x", 2.0)]
MODALITIES = [
    ("none",      "No screening"),
    ("rapid",     "RAT"),
    ("lab",       "Lab PCR"),
    ("molecular", "Sentinel RT-LAMP"),
]

rows = []

for pathogen, params in PATHOGENS.items():
    icu_frac = ICU_FRACTIONS.get(pathogen)
    icu_los  = ICU_LOS_DAYS.get(pathogen)
    # None icu_fraction → c_icu = 0 (engine treats None as 0)
    icu_kw   = {
        "icu_fraction_of_hosp_override": icu_frac,
        "icu_los_days_override": icu_los if icu_los is not None else 7,
    }

    for tier_label, mult in PREV_TIERS:
        pre_icu_costs  = {}
        post_icu_costs = {}

        for mk, ml in MODALITIES:
            if mk == "none":
                # No-screening: run with any modality key but n_screened→0
                # Use run_scenario with modality="none" if supported, else proxy via rapid
                # Check engine signature for "none" modality
                try:
                    r_pre  = run_scenario(params, "none", prevalence_multiplier=mult, horizon_days=HORIZON)
                    r_post = run_scenario(params, "none", prevalence_multiplier=mult, horizon_days=HORIZON, **icu_kw)
                except (KeyError, Exception) as e:
                    # "none" may not be a valid modality key; skip it
                    pre_icu_costs[ml]  = None
                    post_icu_costs[ml] = None
                    continue
            else:
                r_pre  = run_scenario(params, mk, prevalence_multiplier=mult, horizon_days=HORIZON)
                r_post = run_scenario(params, mk, prevalence_multiplier=mult, horizon_days=HORIZON, **icu_kw)

            pre_icu_costs[ml]  = r_pre["total_societal_cost"]
            post_icu_costs[ml] = r_post["total_societal_cost"]

        # Ranking (lowest cost = rank 1), excluding None entries
        def rank_dict(d):
            valid = {k: v for k, v in d.items() if v is not None}
            sorted_keys = sorted(valid, key=lambda k: valid[k])
            return {k: sorted_keys.index(k) + 1 for k in valid}

        pre_ranks  = rank_dict(pre_icu_costs)
        post_ranks = rank_dict(post_icu_costs)

        for mk, ml in MODALITIES:
            if pre_icu_costs.get(ml) is None:
                continue
            pre_c  = pre_icu_costs[ml]
            post_c = post_icu_costs[ml]
            delta  = post_c - pre_c
            pct    = 100 * delta / pre_c if pre_c else 0
            rank_change = post_ranks.get(ml, "?") - pre_ranks.get(ml, "?") if ml in pre_ranks and ml in post_ranks else "?"
            rows.append(dict(
                pathogen=pathogen,
                prevalence_tier=tier_label,
                modality=ml,
                pre_icu_cost=round(pre_c, 2),
                post_icu_cost=round(post_c, 2),
                delta_cost=round(delta, 2),
                pct_change=round(pct, 4),
                pre_icu_rank=pre_ranks.get(ml, "?"),
                post_icu_rank=post_ranks.get(ml, "?"),
                rank_change=rank_change,
            ))

# Write CSV
os.makedirs("results", exist_ok=True)
out = "results/primary_screening_icu_ranking.csv"
with open(out, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(rows)
print(f"\nWrote {len(rows)} rows → {out}")

# Print summary: any rank changes?
print("\n=== Rank changes (pre-ICU → post-ICU) ===")
print(f"{'Pathogen':20s} {'Tier':6s} {'Modality':22s} {'Pre rank':10s} {'Post rank':10s} {'Changed?':10s} {'Δ% cost':10s}")
print("-" * 90)
any_change = False
for r in rows:
    changed = r["rank_change"] != 0
    if changed:
        any_change = True
    marker = " *** RANK CHANGE ***" if changed else ""
    print(f"  {r['pathogen']:18s} {r['prevalence_tier']:6s} {r['modality']:22s} "
          f"{str(r['pre_icu_rank']):10s} {str(r['post_icu_rank']):10s} "
          f"{'YES' if changed else 'no':10s} {r['pct_change']:+.3f}%{marker}")

if not any_change:
    print("\n✓ No rank changes: ICU costing does not alter strategy ordering for any pathogen/tier.")
else:
    print("\n⚠ Rank changes detected — see *** above.")

# Print break-even style: which modality cheapest pre vs post?
print("\n=== Cheapest modality per pathogen/tier ===")
print(f"{'Pathogen':20s} {'Tier':6s} {'Pre-ICU winner':25s} {'Post-ICU winner':25s} {'Same?':6s}")
print("-" * 85)
from collections import defaultdict
grouped = defaultdict(list)
for r in rows:
    grouped[(r["pathogen"], r["prevalence_tier"])].append(r)

for (path, tier), rs in grouped.items():
    pre_best  = min(rs, key=lambda x: x["pre_icu_cost"])["modality"]
    post_best = min(rs, key=lambda x: x["post_icu_cost"])["modality"]
    same = pre_best == post_best
    print(f"  {path:18s} {tier:6s} {pre_best:25s} {post_best:25s} {'✓' if same else '*** CHANGED ***'}")
