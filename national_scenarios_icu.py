"""
national_scenarios_icu.py
=========================
ICU-enabled rerun of the Australia and US national-scale WBE threshold analyses.

This script reproduces the portfolio computations from scenario_australia.py and
scenario_us_350m.py with per-pathogen ICU fractions from icu_parameters.py.

SCOPE
-----
  Runs portfolio at d=5, base probability, no-avian-influenza inclusion,
  matching the primary manuscript result (Section 3.10 / Table 4).
  Also runs the full LEAD_DAYS × PROB_SCENARIOS grid for completeness.

WHAT IS UNCHANGED FROM BASELINE
---------------------------------
  National configurations:
    Australia: N_TOTAL = 52,700/day, N_DOWNSTREAM = 27,100,000
    United States: N_TOTAL = 300,000/day, N_DOWNSTREAM = 350,000,000
  Modality: molecular
  VSL: base_case ($3.5M)
  CM parameters: default (21-day delay, 14-day ramp, 0.6 reduction)
  THREAT_CLASSES, PROB_SCENARIOS: imported unchanged from portfolio.py
  engine.py, parameters.py: LOCKED — not modified

ICU ADDITIONS
-------------
  Per-pathogen ICU fractions from icu_parameters.py:
    SARS-CoV-2:  0.15  (Docherty et al. BMJ 2020; COVID-NET)
    Avian stress: 0.15  (FluSurv-NET; inherits Influenza A/B)
    Ebola:        0.35  (Schieffelin et al. NEJM 2014; caveat: Western cost structure)
    Mpox:         0.03  (Thornhill et al. NEJM 2022)
    Norovirus:    None  (excluded; 7-day ICU LOS implausible vs 1-3 day ward LOS)

REPRODUCE
---------
  cd <repo>
  python national_scenarios_icu.py
"""

import sys, os, csv, math, datetime, json

import os as _os
_HERE = _os.path.dirname(_os.path.abspath(__file__))
sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))

from parameters import PATHOGENS, ECON, MODALITIES, WBE_PARAMS, DOWNSTREAM_POPULATION, mid
from runners import run_scenario_a, run_scenario_b
from portfolio import THREAT_CLASSES, PROB_SCENARIOS
from icu_parameters import get_icu_params

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
HORIZON_DAYS       = 365
RESPONSE_MODALITY  = "molecular"
VSL                = ECON["VSL_base_case"]
LEAD_DAYS          = [2, 5, 10, 14]
AVG_PAX            = WBE_PARAMS["avg_pax_per_flight"]   # 250

# National scales
N_TOTAL_AUS        = 52_700
N_DOWNSTREAM_AUS   = 27_100_000
FLIGHTS_PER_YEAR_AUS = (N_TOTAL_AUS / AVG_PAX) * 365   # 76,942

N_TOTAL_US         = 300_000
N_DOWNSTREAM_US    = 350_000_000
FLIGHTS_PER_YEAR_US = (N_TOTAL_US / AVG_PAX) * 365     # 438,000

RESULTS_BASELINE_AUS = _os.path.join(_HERE, "results", "australia_scenario")
RESULTS_BASELINE_US  = _os.path.join(_HERE, "results", "us_scenario")
RESULTS_ICU_NAT      = _os.path.join(_HERE, "results", "icu")
os.makedirs(RESULTS_ICU_NAT, exist_ok=True)

# ---------------------------------------------------------------------------
# Core runner: compute conditional B(d) for one threat at given n_total / N
# ---------------------------------------------------------------------------
def run_bd(threat, runner_fn, d, n_total, N_pop):
    icu_frac, icu_los = get_icu_params(threat)
    im, dl = runner_fn(
        threat["pathogen_params"], RESPONSE_MODALITY, d,
        prevalence_multiplier=threat["prevalence_multiplier"],
        horizon_days=HORIZON_DAYS, vsl=VSL,
        n_total=n_total, N=N_pop,
        icu_fraction_of_hosp=icu_frac,
        icu_los_days=icu_los if icu_los is not None else 7,
    )
    bd             = max(0.0, dl["total_societal_cost"] - im["total_societal_cost"])
    deaths_averted = max(0.0, dl["cum_deaths"] - im["cum_deaths"])
    return bd, deaths_averted


# ---------------------------------------------------------------------------
# Portfolio builder
# ---------------------------------------------------------------------------
def build_portfolio_icu(n_total, N_pop, flights_per_year, scale_label):
    """Run full portfolio grid with ICU enabled. Returns list of summary row dicts."""
    rows = []
    for scen_key, runner_fn in [("A", run_scenario_a), ("B", run_scenario_b)]:
        for avian_included in [False, True]:
            for prob_scen, event_key, warn_key in PROB_SCENARIOS:
                for d in LEAD_DAYS:
                    threats = [t for t in THREAT_CLASSES
                               if not t["avian_influenza"] or avian_included]
                    portfolio_ev    = 0.0
                    portfolio_deaths = 0.0
                    for threat in threats:
                        bd, da = run_bd(threat, runner_fn, d, n_total, N_pop)
                        p_event   = threat[event_key]
                        p_warning = threat[warn_key]
                        portfolio_ev     += p_event * p_warning * bd
                        portfolio_deaths += p_event * p_warning * da
                    threshold_per_flight = portfolio_ev / flights_per_year
                    annual_threshold     = portfolio_ev
                    rows.append({
                        "scale":             scale_label,
                        "scenario":          scen_key,
                        "avian_included":    avian_included,
                        "prob_scenario":     prob_scen,
                        "lead_days":         d,
                        "n_total":           n_total,
                        "N_downstream":      N_pop,
                        "flights_per_year":  flights_per_year,
                        "portfolio_ev_usd":  portfolio_ev,
                        "annual_threshold_usd": annual_threshold,
                        "threshold_per_flight_usd": threshold_per_flight,
                        "deaths_averted":    portfolio_deaths,
                        "vsl":               VSL,
                        "icu_enabled":       True,
                    })
    return rows


# ---------------------------------------------------------------------------
# Run Australia and US portfolios
# ---------------------------------------------------------------------------
print("=== Building Australia ICU portfolio ===")
aus_rows = build_portfolio_icu(N_TOTAL_AUS, N_DOWNSTREAM_AUS,
                                FLIGHTS_PER_YEAR_AUS, "Australia")
print(f"  {len(aus_rows)} rows")

print("=== Building US ICU portfolio ===")
us_rows = build_portfolio_icu(N_TOTAL_US, N_DOWNSTREAM_US,
                               FLIGHTS_PER_YEAR_US, "United_States")
print(f"  {len(us_rows)} rows")

all_rows = aus_rows + us_rows

# ---------------------------------------------------------------------------
# Write combined results
# ---------------------------------------------------------------------------
out_path = os.path.join(RESULTS_ICU_NAT, "national_icu_portfolio.csv")
with open(out_path, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=all_rows[0].keys())
    w.writeheader()
    w.writerows(all_rows)
print(f"\nWrote {len(all_rows)} rows → {out_path}")

# ---------------------------------------------------------------------------
# Key results: d=5, base prob, no avian — comparison to baseline
# ---------------------------------------------------------------------------
def key_row(rows, scale, scen, d=5, prob="base", avian=False):
    for r in rows:
        if (r["scale"] == scale and r["scenario"] == scen
                and r["lead_days"] == d and r["prob_scenario"] == prob
                and r["avian_included"] == avian):
            return r
    return None

# Baseline values from existing results (verified outputs from prior session)
BASELINE_AUS_A_D5 = 22_500_000   # USD 22.5M/year Scen A (Australia)
BASELINE_AUS_B_D5 = 39_400_000   # USD 39.4M/year Scen B (Australia)
BASELINE_US_A_D5  = 152_900_000  # USD 152.9M/year Scen A (US)
BASELINE_US_B_D5  = 280_000_000  # USD 280.0M/year Scen B (US)

# Load precise baselines from stored summary files where available
def load_baseline(summary_file, scen_key, d=5, prob="base", avian_col="False"):
    try:
        with open(summary_file) as f:
            for row in csv.DictReader(f):
                if (str(row.get("lead_days")) == str(d)
                        and row.get("prob_scenario") == prob
                        and str(row.get("avian_included")) == avian_col):
                    # Try various scenario column formats
                    if (row.get("scenario") == scen_key
                            or row.get("scenario") == f"{scen_key}_screening_only"
                            or row.get("scenario") == f"{scen_key}_screening_plus_countermeasures"):
                        # Get annual threshold
                        fpf = float(row.get("cost_per_flight_aus")
                                    or row.get("cost_per_flight_us") or 0)
                        fpy = float(row.get("flights_per_year_aus")
                                    or row.get("flights_per_year_us") or 0)
                        return fpf * fpy if fpf and fpy else None
    except FileNotFoundError:
        pass
    return None

# Load baselines for precise comparison
base_aus_A = load_baseline(
    os.path.join(RESULTS_BASELINE_AUS, "portfolio_summary_aus.csv"), "A")
base_aus_B = load_baseline(
    os.path.join(RESULTS_BASELINE_AUS, "portfolio_summary_aus.csv"), "B")
base_us_A = load_baseline(
    os.path.join(RESULTS_BASELINE_US, "portfolio_summary_us.csv"), "A_screening_only")
base_us_B = load_baseline(
    os.path.join(RESULTS_BASELINE_US, "portfolio_summary_us.csv"),
    "B_screening_plus_countermeasures")

print("\n=== KEY RESULTS: d=5, base probability, no avian influenza ===")
print(f"{'Scale/Scenario':<40} {'ICU threshold':>15} {'Baseline':>15} {'Δ%':>8}")
print("-" * 80)

comparisons = [
    ("Australia", "A", base_aus_A or BASELINE_AUS_A_D5),
    ("Australia", "B", base_aus_B or BASELINE_AUS_B_D5),
    ("United_States", "A", base_us_A or BASELINE_US_A_D5),
    ("United_States", "B", base_us_B or BASELINE_US_B_D5),
]

key_results = {}
for scale, scen, baseline_val in comparisons:
    r = key_row(all_rows, scale, scen)
    if r:
        icu_val = r["annual_threshold_usd"]
        delta_pct = 100 * (icu_val - baseline_val) / max(abs(baseline_val), 1)
        label = f"{scale} Scenario {scen}"
        print(f"  {label:<38} ${icu_val/1e6:>12.1f}M  ${baseline_val/1e6:>12.1f}M  {delta_pct:+.1f}%")
        key_results[f"{scale}_{scen}"] = {
            "icu_annual_usd": icu_val,
            "baseline_annual_usd": baseline_val,
            "delta_pct": delta_pct,
            "threshold_per_flight": r["threshold_per_flight_usd"],
        }

# ---------------------------------------------------------------------------
# Save key results as JSON for manuscript update
# ---------------------------------------------------------------------------
key_path = os.path.join(RESULTS_ICU_NAT, "national_icu_key_results.json")
with open(key_path, "w") as f:
    json.dump({
        "run_datetime_utc": datetime.datetime.utcnow().isoformat() + "Z",
        "d": 5,
        "prob_scenario": "base",
        "avian_included": False,
        "icu_params": {k: {"fraction": get_icu_params({"representative_pathogen": k, "avian_influenza": False})[0],
                           "los_days": get_icu_params({"representative_pathogen": k, "avian_influenza": False})[1]}
                      for k in ["SARS-CoV-2", "Influenza A", "Mpox", "Norovirus", "Ebola"]},
        "key_results": key_results,
    }, f, indent=2)
print(f"\nKey results → {key_path}")
print("\nDone.")
