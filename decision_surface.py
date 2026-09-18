"""
Task 7: rebuild the decision surface from the corrected model.

Axes: Rt (x) vs expected societal cost per untested infectious case (y, log
scale) -- the same two axes the original manuscript figure used, now driven
entirely by the corrected engine rather than reused from the old figure.

Because a full per-pathogen sweep would conflate many correlated parameters,
the surface uses a SINGLE collapsed burden parameter B ($/case), applied as
an equivalent mortality-only burden (CFR_equiv = B / VSL, symptomatic
fraction = 1, hospitalisation/productivity terms zeroed) so that each grid
cell's total downstream cost per case is exactly B, independent of how that
$/case burden would be split across mortality/hospitalisation/productivity
for a real pathogen. This is a deliberate simplification, documented here,
to keep the two axes interpretable and non-circular; the 7 modelled
pathogens are overlaid as reference points using their own real parameters
for comparison, not used to define the axes.

gamma is fixed at 1/8 days (the arithmetic mean infectious period across the
7 retained pathogens) so that the surface reflects transmission speed (Rt)
independent of a specific pathogen's recovery dynamics; each pathogen's own
gamma is used only for its overlay point.

ICU costing and the surface: the grid's synthetic pathogen carries
hosp_rate = 0 by construction, since its whole downstream burden is collapsed
into the single mortality-equivalent parameter B. The engine derives ICU
admissions from hospitalised cases, so c_icu is identically zero at every grid
cell whatever ICU fraction is supplied. ICU costing is therefore structurally
inapplicable to the surface itself rather than omitted from it, and no ICU
override is passed. It does apply to the pathogen overlay points, which use each
pathogen's real parameters: their per-case burden below includes the incremental
ICU cost per hospitalised case (icu_parameters.icu_burden_per_hospitalised_case),
so the overlay sits on the surface at the position implied by the same cost
function used everywhere else in this study. Diphtheria has no identified ICU
inputs, so its overlay burden is unchanged by that term.
"""
import csv
import numpy as np
from parameters import PATHOGENS, MODALITIES, ECON, mid
from engine import run_scenario
from icu_parameters import icu_burden_per_hospitalised_case

RT_GRID = np.linspace(0.5, 3.2, 22)
COST_PER_CASE_GRID = np.logspace(1, 7, 25)  # $1,000 to $10,000,000 per case
MODALITY_KEYS = ["none", "rapid", "lab", "molecular"]
GAMMA_FIXED = 1 / 8.0

synthetic_pathogen_template = {
    "infectious_period_range": (8, 8),
    "hosp_rate_pct_range": (0, 0),
    "hosp_duration_days_range": (1, 1),
    "symptomatic_fraction_pct_range": (100, 100),
    "detectable_at_arrival_pct_range": (50, 50),
    "baseline_prevalence_pct": 1.0,
    "wbe_applicable": False,
}

rows = []
for Rt in RT_GRID:
    for B in COST_PER_CASE_GRID:
        cfr_equiv_pct = min(100.0, (B / ECON["VSL_base_case"]) * 100.0)
        costs = {}
        for mk in MODALITY_KEYS:
            res = run_scenario(
                synthetic_pathogen_template, mk, prevalence_multiplier=1.0,
                rt_override=Rt, gamma_override=GAMMA_FIXED,
                cfr_override=cfr_equiv_pct, hosp_rate_override=0.0,
                hosp_duration_override=1.0, symptomatic_fraction_override=1.0,
                phi_override=0.5, prevalence_override=0.01,
                apply_countermeasures=True,
            )
            costs[mk] = res["total_societal_cost"]
        winner = min(costs, key=costs.get)
        rows.append({"Rt": Rt, "cost_per_case": B, "winner": MODALITIES[winner]["label"],
                     "winner_key": winner, **{f"cost_{k}": v for k, v in costs.items()}})

with open("results/decision_surface_grid.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader()
    for r in rows: w.writerow(r)

# Pathogen overlay points: (Rt, effective $/case-of-inaction) at baseline prevalence
overlay = []
for name, p in PATHOGENS.items():
    Rt_pt = mid(*p["Rt_range"])
    symp = mid(*p["symptomatic_fraction_pct_range"]) / 100
    cfr = mid(*p["CFR_pct_range"]) / 100
    hosp_rate = mid(*p["hosp_rate_pct_range"]) / 100
    hosp_dur = mid(*p["hosp_duration_days_range"])
    mort_gate = 1.0 if p.get("mortality_already_infection_based") else symp
    icu_per_hosp_case = icu_burden_per_hospitalised_case(name)
    per_case_burden = (mort_gate * cfr * ECON["VSL_base_case"] +
                        symp * hosp_rate * hosp_dur * (ECON["c_bed_per_day"] + ECON["w_avg_per_day"] * (1 + ECON["epsilon_friction"])) +
                        symp * hosp_rate * icu_per_hosp_case)
    overlay.append({"pathogen": name, "Rt": Rt_pt, "cost_per_case": per_case_burden,
                    "icu_cost_per_case": symp * hosp_rate * icu_per_hosp_case})

with open("results/decision_surface_pathogen_overlay.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["pathogen", "Rt", "cost_per_case", "icu_cost_per_case"])
    w.writeheader()
    for r in overlay: w.writerow(r)

print("Decision surface grid written:", len(rows), "cells")
for r in overlay:
    print(f"  {r['pathogen']:20s} Rt={r['Rt']:.2f}  $/case={r['cost_per_case']:,.0f}")
