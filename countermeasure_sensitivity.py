"""
Task 2 of adversarial audit: sensitivity of cost-minimising strategy to the
countermeasure-suppression parameters (Correction 3), which were introduced
because the manuscript's own S1-S6 spec has no suppression term at all.

Parameter provenance (see CHANGELOG.md / engine.py docstring for full detail):
  - Functional form (smoothstep ramp, target_Rt = max(0.30, Rt0*(1-reduction)))
    INHERITED from old JS engine (outbreak.js: computeTimeVaryingTransmission).
  - reduction_strength=0.6 base case INHERITED from old engine's own default
    analysis script (scripts/run_scenarios.mjs: REDUCTION_STRENGTH = 0.6).
  - response_delay_days=21 (base case) is retained UNCHANGED by CORRECTION 17
    (horizon extended 90 -> 365 days): this sweep script's own base case is
    not itself a "base case" row (every row here is a swept combination), so
    no change was needed here to hold response_delay/ramp/reduction fixed
    across the horizon change -- that is enforced in run_master.py, which
    calls run_scenario() with cm_response_delay_days/cm_ramp_days/
    cm_reduction_strength left at their function defaults (21/14/0.6),
    deliberately NOT reverted to the old engine's 60-day/21-day defaults,
    so that the horizon extension's effect can be isolated (see
    engine.py CORRECTION 17 and manuscript Section 2.5).
  - ramp_days=14 (base case) is NEW - old engine used rampDays=21 fixed.
    Not literature-sourced.
This sweep exists specifically to check whether results depend sensitively
on these last two un-sourced choices. The generated manuscript-review table
is run over HORIZON_DAYS=365, with trigger_day=365 representing no
countermeasure activation within the simulation.
on these last two un-sourced choices, now at both the original 90-day and
the current 365-day horizon (ECON["horizon_days"], parameters.py).

CORRECTION 17 addition: alongside the 4x3x3 swept-parameter grid, this
script also runs one explicit "no countermeasure" row per pathogen
(apply_countermeasures=False, i.e. Rt(t) = Rt0 for every t of the horizon --
zero suppression, same simulation pipeline, same initial conditions, same
importation/cost/discounting logic as every other row). This is NOT encoded
via reduction_strength=0 with countermeasures nominally "on" (which would be
numerically equivalent but semantically indirect); it uses the engine's own
apply_countermeasures flag, so a "no countermeasure" row and a "countermeasure
active but achieving no reduction" row are never conflated. Rows are
distinguished by an explicit `countermeasure_status` column
("swept" | "none") rather than by blank/missing trigger-day or ramp-day
values; the no-countermeasure rows use the documented sentinel -1 (not a
valid day count) for `trigger_day` and `ramp_days`, so the column stays
numeric and directly filterable (e.g. `trigger_day >= 0` selects only the
swept rows) while remaining unambiguous. `reduction_strength` is set to the
true value (0.0) rather than a sentinel, since "0% reduction" is exactly
what apply_countermeasures=False produces, and `post_intervention_Rt` is
set equal to each pathogen's baseline Rt (no reduction from baseline, by
construction) -- so the no-countermeasure rows remain directly comparable
to the swept rows on every shared column.

ICU costing follows icu_parameters.scenario_icu_kwargs, as in every other
analysis in this study.
"""
import csv
import os
import sys
from parameters import PATHOGENS, MODALITIES, mid
from engine import run_scenario
from icu_parameters import scenario_icu_kwargs

HORIZON_DAYS = 365
# Trigger days swept: four response-delay values. An earlier design also swept
# trigger_day = HORIZON_DAYS as a stand-in for "no countermeasure activation
# within the simulation"; that stand-in is redundant now that the sweep carries
# an explicit apply_countermeasures=False row per pathogen (countermeasure_status
# = "none"), so the grid is 4 trigger x 3 reduction x 3 ramp per pathogen, as
# reported in the manuscript's supplementary item list.
TRIGGER_DAYS = [14, 21, 35, 50]
REDUCTION_STRENGTHS = [0.4, 0.6, 0.8]
RAMP_DAYS = [7, 14, 21]
MODALITY_KEYS = ["none", "rapid", "lab", "molecular"]
NA_DAY_SENTINEL = -1  # documented "not applicable" marker for trigger_day/ramp_days on no-countermeasure rows

FIELDNAMES = ["pathogen", "countermeasure_status", "trigger_day", "reduction_strength",
              "ramp_days", "post_intervention_Rt", "winner", "winner_key",
              "cost_none", "cost_rapid", "cost_lab", "cost_molecular"]

rows = []
for pathogen, params in PATHOGENS.items():
    # --no-icu reproduces the pre-ICU configuration; used only to verify that
    # this script reproduces the previously delivered CSV before ICU costing
    # is applied. It is not a reported configuration.
    icu_kw = {} if "--no-icu" in sys.argv else scenario_icu_kwargs(pathogen)
    # --- swept countermeasure-parameter grid (countermeasures active) ---
    for trigger in TRIGGER_DAYS:
        for reduction in REDUCTION_STRENGTHS:
            for ramp in RAMP_DAYS:
                costs = {}
                for mk in MODALITY_KEYS:
                    res = run_scenario(params, mk, prevalence_multiplier=1.0,
                                        horizon_days=HORIZON_DAYS,
                                        cm_response_delay_days=trigger, cm_reduction_strength=reduction,
                                        cm_ramp_days=ramp, **icu_kw)
                    costs[mk] = res["total_societal_cost"]
                winner = min(costs, key=costs.get)
                post_rt = max(0.3, mid(*params["Rt_range"]) * (1 - reduction))
                rows.append({"pathogen": pathogen, "countermeasure_status": "swept",
                             "trigger_day": trigger, "reduction_strength": reduction,
                             "ramp_days": ramp, "post_intervention_Rt": round(post_rt, 3),
                             "winner": MODALITIES[winner]["label"], "winner_key": winner,
                             "cost_none": costs["none"], "cost_rapid": costs["rapid"],
                             "cost_lab": costs["lab"], "cost_molecular": costs["molecular"]})

    # --- explicit "no countermeasure" comparator (apply_countermeasures=False) ---
    costs = {}
    for mk in MODALITY_KEYS:
        res = run_scenario(params, mk, prevalence_multiplier=1.0, apply_countermeasures=False, **icu_kw)
        costs[mk] = res["total_societal_cost"]
    winner = min(costs, key=costs.get)
    baseline_rt = round(mid(*params["Rt_range"]), 3)
    rows.append({"pathogen": pathogen, "countermeasure_status": "none",
                 "trigger_day": NA_DAY_SENTINEL, "reduction_strength": 0.0,
                 "ramp_days": NA_DAY_SENTINEL, "post_intervention_Rt": baseline_rt,
                 "winner": MODALITIES[winner]["label"], "winner_key": winner,
                 "cost_none": costs["none"], "cost_rapid": costs["rapid"],
                 "cost_lab": costs["lab"], "cost_molecular": costs["molecular"]})

OUT = ("results/countermeasure_sensitivity_NOICU_CHECK.csv" if "--no-icu" in sys.argv
       else "results/countermeasure_sensitivity.csv")
with open(OUT, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=FIELDNAMES)
    w.writeheader()
    for r in rows: w.writerow(r)

print(
    f"Wrote {len(rows)} rows to results/countermeasure_sensitivity.csv "
    f"({len(TRIGGER_DAYS)} trigger x {len(REDUCTION_STRENGTHS)} reduction x "
    f"{len(RAMP_DAYS)} ramp x {len(PATHOGENS)} pathogens = "
    f"{len(TRIGGER_DAYS) * len(REDUCTION_STRENGTHS) * len(RAMP_DAYS) * len(PATHOGENS)}; "
    f"horizon={HORIZON_DAYS} days)"
)
print(f"\nStrategy stability per pathogen (across all {len(TRIGGER_DAYS) * len(REDUCTION_STRENGTHS) * len(RAMP_DAYS)} countermeasure-parameter combinations):")
n_swept = sum(1 for r in rows if r["countermeasure_status"] == "swept")
n_none = sum(1 for r in rows if r["countermeasure_status"] == "none")
print(f"Wrote {len(rows)} rows to results/countermeasure_sensitivity.csv "
      f"({n_swept} swept [4 trigger x 3 reduction x 3 ramp x {len(PATHOGENS)} pathogens] "
      f"+ {n_none} no-countermeasure [1 x {len(PATHOGENS)} pathogens])")
print("\nStrategy stability per pathogen (across all swept countermeasure-parameter combinations, "
      "swept rows only):")
for pathogen in PATHOGENS:
    prow = [r for r in rows if r["pathogen"] == pathogen and r["countermeasure_status"] == "swept"]
    winners = set(r["winner"] for r in prow)
    stable = "STABLE" if len(winners) == 1 else f"CHANGES ({len(winners)} distinct winners)"
    print(f"  {pathogen:20s} [{stable}]  winners seen: {sorted(winners)}")

print("\nNo-countermeasure comparator (countermeasure_status == 'none'):")
for r in rows:
    if r["countermeasure_status"] == "none":
        print(f"  {r['pathogen']:20s} winner={r['winner']:35s} "
              f"post_intervention_Rt={r['post_intervention_Rt']} (== baseline Rt, by construction)")
