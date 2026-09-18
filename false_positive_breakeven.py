"""
false_positive_breakeven.py — Post-hoc FP cost breakeven analysis.

For each pathogen × prevalence-tier combination (18 total), computes the
incremental per-false-positive cost at which the currently cost-minimising
strategy would change if that cost were added uniformly to every strategy's
false-positive count. This is a sensitivity check on the exclusion of
false-positive follow-up costs from the main cost function (Section 2.6.1).

Derived from ICU-enabled deterministic results (post_icu_cost from
results/primary_screening_icu_ranking.csv) using ICU-enabled engine calls
for false-positive counts.

Outputs:
    results/false_positive_breakeven.csv

Key results (ICU-enabled, 365-day horizon):
    Min threshold: influenza A/B 0.5× prevalence — USD 564/FP
    Max threshold: Ebola 2× prevalence             — USD 182,844/FP

REPRODUCE:
    cd <repo>
    python3 false_positive_breakeven.py
"""
import os, sys
_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import csv
from engine import run_scenario
from parameters import PATHOGENS, ECON
from icu_parameters import ICU_FRACTIONS, ICU_LOS_DAYS

HORIZON = 365

MODALITY_MAP = {
    "No screening":     "none",
    "RAT":              "rapid",
    "Lab PCR":          "lab",
    "Sentinel RT-LAMP": "molecular",
}
MULT_MAP = {"0.5x": 0.5, "1x": 1.0, "2x": 2.0}

OUT_CSV = "results/false_positive_breakeven.csv"

# Load ICU-enabled primary screening ranking
rows_by_combo = {}
with open("results/primary_screening_icu_ranking.csv") as f:
    for r in csv.DictReader(f):
        key = (r["pathogen"], r["prevalence_tier"])
        rows_by_combo.setdefault(key, []).append(r)

output_rows = []

for (pathogen, tier), rows in sorted(rows_by_combo.items()):
    mult   = MULT_MAP[tier]
    params = PATHOGENS[pathogen]

    icu_frac = ICU_FRACTIONS.get(pathogen)
    icu_los  = ICU_LOS_DAYS.get(pathogen, 7)
    icu_kw   = {}
    if icu_frac is not None:
        icu_kw["icu_fraction_of_hosp_override"] = icu_frac
        icu_kw["icu_los_days_override"]          = icu_los

    strat_costs = {}
    strat_fps   = {}
    for r in rows:
        mk  = MODALITY_MAP[r["modality"]]
        strat_costs[r["modality"]] = float(r["post_icu_cost"])
        result = run_scenario(params, mk, prevalence_multiplier=mult,
                              horizon_days=HORIZON, **icu_kw)
        strat_fps[r["modality"]] = result["false_positives_cum"]

    # Cost-minimising strategy
    best_mod  = min(strat_costs, key=strat_costs.get)
    best_cost = strat_costs[best_mod]
    best_fp   = strat_fps[best_mod]

    # Breakeven C for each non-best strategy:
    # best_cost + C*best_fp == alt_cost + C*alt_fp
    # C = (alt_cost - best_cost) / (best_fp - alt_fp)
    for mod, cost in strat_costs.items():
        fp       = strat_fps[mod]
        fp_diff  = best_fp - fp
        if abs(fp_diff) < 1e-6 or mod == best_mod:
            threshold = None
        else:
            raw_threshold = (cost - best_cost) / fp_diff
            threshold = round(raw_threshold, 2) if raw_threshold > 0 else None

        output_rows.append({
            "pathogen":            pathogen,
            "prevalence_tier":     tier,
            "best_strategy":       best_mod,
            "comparison_strategy": mod,
            "best_cost_icu":       round(best_cost, 2),
            "alt_cost_icu":        round(cost, 2),
            "best_fp_cum":         round(best_fp, 1),
            "alt_fp_cum":          round(fp, 1),
            "breakeven_cost_per_fp": threshold,
        })

fields = [
    "pathogen", "prevalence_tier", "best_strategy", "comparison_strategy",
    "best_cost_icu", "alt_cost_icu", "best_fp_cum", "alt_fp_cum",
    "breakeven_cost_per_fp",
]
with open(OUT_CSV, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=fields)
    w.writeheader()
    w.writerows(output_rows)

print(f"Wrote {len(output_rows)} rows → {OUT_CSV}")

# Report min/max positive thresholds
valid = [(r["pathogen"], r["prevalence_tier"], r["breakeven_cost_per_fp"])
         for r in output_rows
         if r["breakeven_cost_per_fp"] is not None and r["breakeven_cost_per_fp"] > 0]

if valid:
    min_v = min(valid, key=lambda x: x[2])
    max_v = max(valid, key=lambda x: x[2])
    print(f"\nMin positive breakeven: {min_v[0]} {min_v[1]} → USD {min_v[2]:,.0f}/FP")
    print(f"Max positive breakeven: {max_v[0]} {max_v[1]} → USD {max_v[2]:,.0f}/FP")
    print("Manuscript §3.3.1 should state: USD 564 (influenza A/B 0.5×) to USD 182,844 (Ebola 2×)")
