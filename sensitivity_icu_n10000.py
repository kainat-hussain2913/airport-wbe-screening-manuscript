"""
sensitivity_icu_n10000.py
=========================
Runs the unresolved-ICU sensitivity analysis at N=10,000 arrivals/day —
the same scale as Table 4 in the manuscript (and reconciliation_icu.py).

This is a companion to sensitivity_icu_unresolved.py (N=14,082) so that
the sensitivity range can be expressed relative to the Table 4 baseline.

Scope: norovirus and Ebola ICU variants only; d=5 base-prob no-avian portfolio.
Diphtheria (primary-screening only) is excluded because the primary-screening
B(d) at N=14,082 and N=10,000 would differ only by a ~29% scaling factor and
the unresolved-ICU range expressed as a percentage of the mid-case is
scale-invariant.

REPRODUCE
---------
  cd <repo>
  python sensitivity_icu_n10000.py
"""

import sys, os, csv, json, datetime

import os as _os
sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))

from parameters import PATHOGENS, ECON, MODALITIES, WBE_PARAMS, DOWNSTREAM_POPULATION, mid
from runners import run_scenario_a, run_scenario_b
from portfolio import THREAT_CLASSES, PROB_SCENARIOS
from icu_parameters import get_icu_params, ICU_FRACTIONS, ICU_LOS_DAYS
import inspect
engine_path = inspect.getfile(
    __import__("engine", fromlist=["compute_downstream_health_costs"])
    .compute_downstream_health_costs
)

RESULTS_DIR = "<repo>/results/sensitivity_icu"
os.makedirs(RESULTS_DIR, exist_ok=True)

HORIZON_DAYS       = 365
RESPONSE_MODALITY  = "molecular"
VSL                = ECON["VSL_base_case"]
D_PRIMARY          = 5
AVG_PAX            = WBE_PARAMS["avg_pax_per_flight"]

# TABLE 4 scale
N_TOTAL            = 10_000        # matches Table 4 and reconciliation_icu.py
FLIGHTS_PER_YEAR   = (N_TOTAL / AVG_PAX) * 365

NOROVIRUS_VARIANTS = [
    ("low",  0.01, 1),
    ("mid",  0.03, 2),
    ("high", 0.05, 3),
]

EBOLA_VARIANTS = [
    ("field",   0.05, 5),
    ("mid",     0.35, 10),
    ("western", 0.80, 12),
]

# ---- helper ----------------------------------------------------------------

def run_bd(threat, runner_fn, d, icu_frac_override=None, icu_los_override=None):
    icu_frac, icu_los = get_icu_params(threat)
    if icu_frac_override is not None:
        icu_frac = icu_frac_override
    if icu_los_override is not None:
        icu_los = icu_los_override
    im, dl = runner_fn(
        threat["pathogen_params"],
        RESPONSE_MODALITY,
        d,
        prevalence_multiplier=threat["prevalence_multiplier"],
        horizon_days=HORIZON_DAYS,
        vsl=VSL,
        n_total=N_TOTAL,
        icu_fraction_of_hosp=icu_frac,
        icu_los_days=icu_los if icu_los is not None else 7,
    )
    return max(0.0, dl["total_societal_cost"] - im["total_societal_cost"])


def portfolio_ev(runner_fn, threat_overrides, include_avian=False, d=D_PRIMARY):
    """
    Compute portfolio EV at base prob, d=D_PRIMARY, no-avian.
    threat_overrides: dict of threat_class -> (icu_frac, icu_los) to substitute.
    """
    threats = [t for t in THREAT_CLASSES if (not t["avian_influenza"] or include_avian)]
    # use "base" prob scenario
    event_key   = "annual_event_probability_base"
    warning_key = "useful_warning_probability_base"
    ev_total = 0.0
    for threat in threats:
        override = threat_overrides.get(threat["threat_class"])
        if override:
            bd = run_bd(threat, runner_fn, d,
                        icu_frac_override=override[0],
                        icu_los_override=override[1])
        else:
            bd = run_bd(threat, runner_fn, d)
        p_event   = threat[event_key]
        p_warning = threat[warning_key]
        ev_total += p_event * p_warning * bd
    return ev_total


# ---- run -------------------------------------------------------------------

rows = []

for scenario_label, runner_fn in [
    ("A_screening_only", run_scenario_a),
    ("B_screening_plus_countermeasures", run_scenario_b),
]:
    # Base case (all ICU params at mid values from icu_parameters.py)
    ev_mid = portfolio_ev(runner_fn, {})

    # Norovirus sensitivity
    nov_tc = "High-burden enteric outbreak"   # Norovirus threat class name
    for variant_name, frac, los in NOROVIRUS_VARIANTS:
        ev = portfolio_ev(runner_fn, {nov_tc: (frac, los)})
        rows.append({
            "n_total": N_TOTAL,
            "scenario": scenario_label,
            "sensitivity_pathogen": "Norovirus",
            "variant": variant_name,
            "icu_fraction": frac,
            "icu_los_days": los,
            "portfolio_ev": ev,
            "ev_mid": ev_mid,
            "delta_from_mid": ev - ev_mid,
            "pct_delta_from_mid": 100.0 * (ev - ev_mid) / ev_mid if ev_mid > 0 else 0.0,
            "cost_per_arriving_flight": ev / FLIGHTS_PER_YEAR,
        })

    # Ebola sensitivity
    ebo_tc = "Ebola-like viral haemorrhagic fever"
    for variant_name, frac, los in EBOLA_VARIANTS:
        ev = portfolio_ev(runner_fn, {ebo_tc: (frac, los)})
        rows.append({
            "n_total": N_TOTAL,
            "scenario": scenario_label,
            "sensitivity_pathogen": "Ebola",
            "variant": variant_name,
            "icu_fraction": frac,
            "icu_los_days": los,
            "portfolio_ev": ev,
            "ev_mid": ev_mid,
            "delta_from_mid": ev - ev_mid,
            "pct_delta_from_mid": 100.0 * (ev - ev_mid) / ev_mid if ev_mid > 0 else 0.0,
            "cost_per_arriving_flight": ev / FLIGHTS_PER_YEAR,
        })

# ---- write output ----------------------------------------------------------

out_path = os.path.join(RESULTS_DIR, "sensitivity_icu_n10000.csv")
fieldnames = list(rows[0].keys())
with open(out_path, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=fieldnames)
    w.writeheader(); w.writerows(rows)
print(f"Wrote {len(rows)} rows to {out_path}")

meta = {
    "run_timestamp": datetime.datetime.now().isoformat(),
    "engine_path": engine_path,
    "n_total": N_TOTAL,
    "purpose": "Sensitivity over unresolved ICU inputs at Table 4 scale (N=10,000)",
    "d_primary": D_PRIMARY,
    "prob_scenario": "base",
    "avian_included": False,
}
meta_path = os.path.join(RESULTS_DIR, "sensitivity_icu_n10000_metadata.json")
with open(meta_path, "w") as f:
    json.dump(meta, f, indent=2)
print(f"Metadata: {meta_path}")

# ---- print summary ---------------------------------------------------------
print("\n--- Scenario A portfolio EV sensitivity (N=10,000, d=5, base, no-avian) ---")
for r in rows:
    if r["scenario"] == "A_screening_only":
        print(f"  {r['sensitivity_pathogen']:10s} {r['variant']:8s} "
              f"EV=${r['portfolio_ev']/1e6:.4f}M  Δ={r['delta_from_mid']/1e6:+.4f}M  "
              f"({r['pct_delta_from_mid']:+.2f}%)")
print("\n--- Scenario B portfolio EV sensitivity (N=10,000, d=5, base, no-avian) ---")
for r in rows:
    if r["scenario"] == "B_screening_plus_countermeasures":
        print(f"  {r['sensitivity_pathogen']:10s} {r['variant']:8s} "
              f"EV=${r['portfolio_ev']/1e6:.4f}M  Δ={r['delta_from_mid']/1e6:+.4f}M  "
              f"({r['pct_delta_from_mid']:+.2f}%)")
