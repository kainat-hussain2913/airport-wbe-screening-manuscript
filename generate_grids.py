"""
Generate full B_d grids for Scenario A (screening_only) and
Scenario B (screening_plus_countermeasures).

Grid dimensions:
  pathogens:        all PATHOGENS with wbe_applicable = True
  modalities:       rapid (RAT), lab (Laboratory PCR), molecular (High-throughput)
  lead_days:        2, 5, 10, 14
  prevalence_tiers: 0.1x, 0.5x, 1x, 2x
  VSL scenarios:    low_resource, base_case, high_income
  horizon_days:     365

Output: results/scenario_a_grid.csv, results/scenario_b_grid.csv
"""

import sys, os, csv
import os as _os
_HERE = _os.path.dirname(_os.path.abspath(__file__))
sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))

from parameters import PATHOGENS, MODALITIES, ECON, mid
from runners import run_scenario_a, run_scenario_b
from icu_parameters import ICU_FRACTIONS, ICU_LOS_DAYS

# NOTE: existing grid CSVs (scenario_a_grid.csv, scenario_b_grid.csv) were
# generated WITHOUT icu_fraction_of_hosp / icu_los_days arguments and therefore
# have c_icu=0 throughout. They are pre-ICU outputs. Re-running this script
# after the ICU wiring below will update the grids to include per-pathogen ICU
# costs; this changes all Bd values and all downstream primary screening results.
# Do not re-run without explicit authorisation.

def _get_icu_for_pathogen(pathogen_name):
    """Return (icu_fraction, icu_los_days) for a WBE pathogen, or (None, None)."""
    frac = ICU_FRACTIONS.get(pathogen_name)
    los  = ICU_LOS_DAYS.get(pathogen_name)
    if frac is None or los is None:
        return None, None
    return frac, los

RESULTS_DIR = _os.path.join(_HERE, "results")
os.makedirs(RESULTS_DIR, exist_ok=True)

# Correct modality labels per spec
MODALITY_DISPLAY = {
    "rapid":     "Rapid Antigen Test (RAT)",
    "lab":       "Laboratory PCR",
    "molecular": "High-throughput molecular screening",
    "none":      "No screening",
}

LEAD_DAYS        = [2, 5, 10, 14]
PREVALENCE_TIERS = [("0.1x", 0.1), ("0.5x", 0.5), ("1x", 1.0), ("2x", 2.0)]
VSL_SCENARIOS    = [
    ("low_resource", ECON["VSL_low_resource"]),
    ("base_case",    ECON["VSL_base_case"]),
    ("high_income",  ECON["VSL_high_income"]),
]
MODALITY_KEYS    = ["rapid", "lab", "molecular"]
HORIZON_DAYS     = 365

WBE_PATHOGENS = {k: v for k, v in PATHOGENS.items() if v.get("wbe_applicable")}


def build_grid_row(scenario_label, pathogen, params, mk, d, prev_label, prev_mult,
                   vsl_label, vsl, immediate, delayed):
    bd = delayed["total_societal_cost"] - immediate["total_societal_cost"]
    bd_nn = max(0.0, bd)

    screening_bd   = delayed["screening_cost"]   - immediate["screening_cost"]
    hospital_bd    = delayed["hospital_cost"]    - immediate["hospital_cost"]
    productivity_bd= delayed["productivity_cost"]- immediate["productivity_cost"]
    mortality_bd   = delayed["mortality_cost"]   - immediate["mortality_cost"]
    icu_bd         = delayed["icu_cost"]         - immediate["icu_cost"]

    infections_bd  = delayed["cum_infections"]   - immediate["cum_infections"]
    deaths_bd      = delayed["cum_deaths"]       - immediate["cum_deaths"]

    return {
        "scenario":             scenario_label,
        "pathogen":             pathogen,
        "modality_key":         mk,
        "modality_label":       MODALITY_DISPLAY[mk],
        "lead_days":            d,
        "prevalence_tier":      prev_label,
        "prevalence_multiplier":prev_mult,
        "vsl_scenario":         vsl_label,
        "vsl":                  vsl,
        "horizon_days":         HORIZON_DAYS,
        "Bd":                   bd,
        "Bd_nonneg":            bd_nn,
        "delta_screening_cost": screening_bd,
        "delta_hospital_cost":  hospital_bd,
        "delta_productivity_cost": productivity_bd,
        "delta_mortality_cost": mortality_bd,
        "delta_icu_cost":       icu_bd,
        "delta_infections":     infections_bd,
        "delta_deaths":         deaths_bd,
        "immediate_total_cost": immediate["total_societal_cost"],
        "delayed_total_cost":   delayed["total_societal_cost"],
        "immediate_cm_start":   immediate["cm_start_day"],
        "delayed_cm_start":     delayed["cm_start_day"],
        "Rt":                   immediate["Rt"],
        "CFR_pct":              immediate["CFR_pct"],
        "infectious_period_days": immediate["infectious_period_days"],
        "phi_pct":              immediate["phi_pct"],
        "p0_pct":               immediate["p0_pct"],
        "sensitivity":          immediate["sensitivity"],
    }


def generate_grid(scenario_label, runner_fn, outpath):
    rows = []
    n_pathogens = len(WBE_PATHOGENS)
    total = n_pathogens * len(MODALITY_KEYS) * len(LEAD_DAYS) * len(PREVALENCE_TIERS) * len(VSL_SCENARIOS)
    done = 0
    for pathogen, params in WBE_PATHOGENS.items():
        for mk in MODALITY_KEYS:
            for d in LEAD_DAYS:
                for prev_label, prev_mult in PREVALENCE_TIERS:
                    for vsl_label, vsl in VSL_SCENARIOS:
                        icu_frac, icu_los = _get_icu_for_pathogen(pathogen)
                        immediate, delayed = runner_fn(
                            params, mk, d,
                            prevalence_multiplier=prev_mult,
                            horizon_days=HORIZON_DAYS,
                            vsl=vsl,
                            icu_fraction_of_hosp=icu_frac,
                            icu_los_days=icu_los if icu_los is not None else 7,
                        )
                        rows.append(build_grid_row(
                            scenario_label, pathogen, params, mk, d,
                            prev_label, prev_mult, vsl_label, vsl,
                            immediate, delayed
                        ))
                        done += 1
                        if done % 100 == 0:
                            print(f"  {scenario_label}: {done}/{total}")

    fieldnames = list(rows[0].keys())
    with open(outpath, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)
    print(f"Wrote {len(rows)} rows to {outpath}")
    return rows


if __name__ == "__main__":
    print(f"WBE-applicable pathogens: {list(WBE_PATHOGENS.keys())}")
    expected = len(WBE_PATHOGENS) * len(MODALITY_KEYS) * len(LEAD_DAYS) * len(PREVALENCE_TIERS) * len(VSL_SCENARIOS)
    print(f"Expected rows per scenario: {expected}")

    grid_a = generate_grid(
        "A_screening_only",
        run_scenario_a,
        os.path.join(RESULTS_DIR, "scenario_a_grid.csv"),
    )
    grid_b = generate_grid(
        "B_screening_plus_countermeasures",
        run_scenario_b,
        os.path.join(RESULTS_DIR, "scenario_b_grid.csv"),
    )
    print("\nGrid generation complete.")
    print(f"  Scenario A: {len(grid_a)} rows")
    print(f"  Scenario B: {len(grid_b)} rows")
