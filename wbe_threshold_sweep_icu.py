"""
wbe_threshold_sweep_icu.py
==========================
ICU-enabled regeneration of the WBE threshold sweep
(run_wbe_threshold_sweep_365day_locked.py + per-pathogen ICU costing).

Scope:
  - 4 WBE-applicable pathogens: SARS-CoV-2, Mpox, Norovirus, Ebola
  - 3 prevalence tiers: 0.5x, 1x, 2x
  - 3 follow-up modalities: rapid, lab, molecular
  - Q grid: 0.05–0.95 in 0.05 steps (19 points)
  - Cost grid: $10, 15, 25, 40, 60, 100, 150/sample
  - FP rate: 0.005, 0.02, 0.05, 0.10
  - Coverage: 0.50, 0.75, 1.00
  - Horizon: 365 days
  - ICU: per-pathogen fractions and LOS from icu_parameters.py

Output: results/wbe_sweep/wbe_threshold_sweep_icu_full_grid.csv

DIFFERENCES FROM LOCKED SCRIPT:
  1. ICU costing passed via icu_fraction_of_hosp_override / icu_los_days_override
  2. Output path: results/wbe_sweep/ (not pubengine/results/)
  3. No locked-reference validation (ICU changes expected values)
  4. n_total explicitly set to 10,000 (manuscript baseline)

REPRODUCE:
  cd <repo>
  python wbe_threshold_sweep_icu.py [PATHOGEN_NAME]
"""

import csv, sys, os, time, json, datetime

import os as _os
sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))

from parameters import PATHOGENS, ECON, WBE_PARAMS
from engine import run_scenario, run_wbe_gated_scenario
from icu_parameters import ICU_FRACTIONS, ICU_LOS_DAYS

RESULTS_DIR = "<repo>/results/wbe_sweep"
os.makedirs(RESULTS_DIR, exist_ok=True)

# CLI filter: run one pathogen at a time if desired
PATHOGEN_FILTER = sys.argv[1] if len(sys.argv) > 1 else None

WBE_PATHOGENS = {k: v for k, v in PATHOGENS.items() if v.get("wbe_applicable")}
if PATHOGEN_FILTER:
    WBE_PATHOGENS = {PATHOGEN_FILTER: WBE_PATHOGENS[PATHOGEN_FILTER]}
    SUFFIX = f"_{PATHOGEN_FILTER.replace(' ', '_').replace('/', '_')}"
else:
    SUFFIX = ""

PREV_TIERS = [("0.5x", 0.5), ("1x", 1.0), ("2x", 2.0)]
FOLLOWUP_MODALITIES = [("rapid", "RAT"), ("lab", "Laboratory PCR"), ("molecular", "Sentinel RT-LAMP")]

Q_GRID          = [round(0.05 + 0.05 * i, 2) for i in range(19)]  # 0.05..0.95
COST_GRID       = [10, 15, 25, 40, 60, 100, 150]
FP_GRID         = [0.005, 0.02, 0.05, 0.10]
COVERAGE_GRID   = [0.50, 0.75, 1.00]
REFERENCE_PAX   = 250
HORIZON_DAYS    = 365
N_TOTAL         = 10_000  # manuscript baseline


def _icu_kwargs(pathogen_name):
    """Return engine ICU kwargs for given pathogen (using _override names)."""
    frac = ICU_FRACTIONS.get(pathogen_name)
    los  = ICU_LOS_DAYS.get(pathogen_name)
    if frac is None or los is None:
        return {"icu_fraction_of_hosp_override": None, "icu_los_days_override": 7}
    return {"icu_fraction_of_hosp_override": frac, "icu_los_days_override": los}


t_start = time.time()

# Precompute comparator (universal screening) costs with ICU
comparator_cost = {}
for pathogen, params in WBE_PATHOGENS.items():
    icu_kw = _icu_kwargs(pathogen)
    for tier_label, mult in PREV_TIERS:
        for modality_key, _ in FOLLOWUP_MODALITIES:
            result = run_scenario(params, modality_key, prevalence_multiplier=mult,
                                  horizon_days=HORIZON_DAYS, n_total=N_TOTAL, **icu_kw)
            comparator_cost[(pathogen, tier_label, modality_key)] = result["total_societal_cost"]

print(f"Computed {len(comparator_cost)} comparator (UC) costs — horizon={HORIZON_DAYS}, n_total={N_TOTAL}, ICU-enabled.")

full_grid_rows = []
n_calls = 0

for pathogen, params in WBE_PATHOGENS.items():
    icu_kw = _icu_kwargs(pathogen)
    for tier_label, mult in PREV_TIERS:
        for modality_key, modality_label in FOLLOWUP_MODALITIES:
            uc_cost = comparator_cost[(pathogen, tier_label, modality_key)]
            for fp in FP_GRID:
                for cov in COVERAGE_GRID:
                    for q in Q_GRID:
                        for cost_per_sample in COST_GRID:
                            r = run_wbe_gated_scenario(
                                params, modality_key, prevalence_multiplier=mult,
                                wbe_detection_prob=q, wbe_false_positive_rate=fp,
                                follow_up_coverage=cov, avg_pax_per_flight=REFERENCE_PAX,
                                wbe_cost_per_sample=cost_per_sample, horizon_days=HORIZON_DAYS,
                                n_total=N_TOTAL,
                                **icu_kw,
                            )
                            n_calls += 1
                            wbe_cost = r["total_societal_cost"]
                            delta_c  = wbe_cost - uc_cost
                            full_grid_rows.append(dict(
                                pathogen=pathogen,
                                prevalence_tier=tier_label,
                                follow_up_modality=modality_label,
                                wbe_false_positive_rate=fp,
                                follow_up_coverage=cov,
                                avg_pax_per_flight=REFERENCE_PAX,
                                horizon_days=HORIZON_DAYS,
                                n_total=N_TOTAL,
                                icu_fraction=icu_kw["icu_fraction_of_hosp_override"],
                                icu_los_days=icu_kw["icu_los_days_override"],
                                wbe_detection_prob_q=q,
                                wbe_cost_per_sample=cost_per_sample,
                                uc_total_cost=uc_cost,
                                wbe_total_cost=wbe_cost,
                                delta_c_wbe_minus_uc=delta_c,
                                wbe_cheaper=(delta_c < 0),
                            ))

elapsed = time.time() - t_start
print(f"Full grid: {n_calls} run_wbe_gated_scenario() calls, {elapsed:.1f}s elapsed.")

# Write CSV
out_path = os.path.join(RESULTS_DIR, f"wbe_threshold_sweep_icu_full_grid{SUFFIX}.csv")
fieldnames = list(full_grid_rows[0].keys())
with open(out_path, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=fieldnames)
    w.writeheader()
    w.writerows(full_grid_rows)
print(f"Wrote {len(full_grid_rows)} rows to {out_path}")

# Write metadata
meta = {
    "run_timestamp": datetime.datetime.now().isoformat(),
    "n_total": N_TOTAL,
    "horizon_days": HORIZON_DAYS,
    "pathogens": list(WBE_PATHOGENS.keys()),
    "icu_params": {p: {"icu_fraction": ICU_FRACTIONS.get(p), "icu_los_days": ICU_LOS_DAYS.get(p)}
                   for p in WBE_PATHOGENS},
    "n_rows": len(full_grid_rows),
    "elapsed_seconds": elapsed,
    "note": "ICU-enabled WBE threshold sweep at manuscript baseline N=10,000",
}
meta_path = os.path.join(RESULTS_DIR, f"wbe_threshold_sweep_icu_metadata{SUFFIX}.json")
with open(meta_path, "w") as f:
    json.dump(meta, f, indent=2)
print(f"Metadata: {meta_path}")

# Summary: at what q does WBE become cheaper than UC? (fp=0.02, cov=1.0, cost=$25, 1x tier)
print(f"\n=== Threshold summary: fp=0.02, cov=1.0, cost=$25/sample, 1x prevalence ===")
print(f"{'Pathogen':20s} {'Modality':20s} {'First q where WBE < UC':25s} {'delta_c at q=0.95':18s}")
print("-" * 85)
for pathogen in WBE_PATHOGENS:
    for mk, ml in FOLLOWUP_MODALITIES:
        threshold_q = None
        delta_at_max_q = None
        for row in full_grid_rows:
            if (row["pathogen"] == pathogen and row["follow_up_modality"] == ml
                    and row["prevalence_tier"] == "1x"
                    and row["wbe_false_positive_rate"] == 0.02
                    and row["follow_up_coverage"] == 1.0
                    and row["wbe_cost_per_sample"] == 25):
                if row["wbe_cheaper"] and threshold_q is None:
                    threshold_q = row["wbe_detection_prob_q"]
                if row["wbe_detection_prob_q"] == 0.95:
                    delta_at_max_q = row["delta_c_wbe_minus_uc"]
        thr_str = f"q={threshold_q:.2f}" if threshold_q else "never cheaper"
        dlt_str = f"${delta_at_max_q/1e6:.3f}M" if delta_at_max_q is not None else "N/A"
        print(f"  {pathogen:18s} {ml:20s} {thr_str:25s} {dlt_str:18s}")
