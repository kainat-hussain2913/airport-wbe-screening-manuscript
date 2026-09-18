"""
scenario_us_350m.py
====================
US-scale scenario: n_total = 300,000 arrivals/day, N = 350,000,000 downstream population.

RELATIONSHIP TO BASELINE (reconciliation_10k.py / manuscript Table 4)
-----------------------------------------------------------------------
  n_total:   10,000 → 300,000  (30× increase; provisional figure from Mans)
  N:         10,000,000 → 350,000,000  (35× increase; US national population)

WHAT IS UNCHANGED
------------------
  Pathogen parameters:    unchanged (locked parameters.py)
  VSL:                    base_case ($3.5M) — NOT adjusted for US income levels
                          Reported as a limitation; US VSL is higher (~$10–12M).
  Modality:               molecular (high-throughput)
  Horizon:                365 days
  Lead days:              2, 5, 10, 14
  CM parameters:          DEFAULT_CM_DELAY=21, DEFAULT_CM_RAMP=14, CM_REDUC=0.6
  P_event, P_warning:     unchanged from THREAT_CLASSES (UNSOURCED SCENARIO ASSUMPTIONS)
  Prevalence multiplier:  1.0 × pathogen-specific baseline

MODELLING CAVEAT (record in output, not omit)
----------------------------------------------
  The baseline model uses a single-compartment SIR with N=10M, described as a
  "generic large metropolitan catchment". Scaling N to 350M assumes the entire
  US population is a single homogeneous mixing pool. This is an unrealistic
  assumption for a national-scale analysis; the model was not designed for this
  configuration. The outputs should be read as order-of-magnitude estimates,
  not as validated national forecasts. The downstream population scaling is the
  dominant driver of cost differences from the baseline.

PRESERVATION
-------------
  This script writes ONLY to results/us_scenario/
  It does not modify any existing file.
  engine.py and parameters.py are not modified.

REPRODUCE
----------
  cd <repo>
  python scenario_us_350m.py
"""

import sys, os, csv, math, datetime

import os as _os
sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))

from parameters import (
    PATHOGENS, ECON, MODALITIES, WBE_PARAMS, ROUTE_TIERS,
    N_TOTAL_ARRIVALS_PER_DAY, DOWNSTREAM_POPULATION, mid,
)
from runners import run_scenario_a, run_scenario_b
from portfolio import THREAT_CLASSES, PROB_SCENARIOS, MODALITY_DISPLAY
from icu_parameters import get_icu_params, ICU_FRACTIONS, ICU_LOS_DAYS

# ---------------------------------------------------------------------------
# Configuration — US scenario overrides (all others unchanged from baseline)
# ---------------------------------------------------------------------------
N_TOTAL_US       = 300_000              # international air arrivals/day (Mans provisional)
N_DOWNSTREAM_US  = 350_000_000          # US downstream population

# Derived flight metrics (same pax-per-flight assumption as baseline)
AVG_PAX_PER_FLIGHT = WBE_PARAMS["avg_pax_per_flight"]   # 250 (unchanged)
FLIGHTS_PER_DAY  = N_TOTAL_US / AVG_PAX_PER_FLIGHT      # 1,200
FLIGHTS_PER_YEAR = FLIGHTS_PER_DAY * 365                 # 438,000

# Unchanged parameters
LEAD_DAYS         = [2, 5, 10, 14]
HORIZON_DAYS      = 365
RESPONSE_MODALITY = "molecular"
VSL               = ECON["VSL_base_case"]   # $3.5M — NOT US-adjusted; flagged below

# Baseline values for comparison (from reconciliation_10k; confirmed above)
N_TOTAL_BASELINE     = 10_000
N_DOWNSTREAM_BASELINE = 10_000_000
FLIGHTS_PER_YEAR_BASE = (N_TOTAL_BASELINE / AVG_PAX_PER_FLIGHT) * 365  # 14,600

RESULTS_DIR = "<repo>/results/us_scenario"
os.makedirs(RESULTS_DIR, exist_ok=True)

WBE_PATHOGENS = {k: v for k, v in PATHOGENS.items() if v.get("wbe_applicable")}

# ---------------------------------------------------------------------------
# Configuration record
# ---------------------------------------------------------------------------
config_lines = [
    "# US Scenario Configuration Record",
    f"Run timestamp: {datetime.datetime.utcnow().isoformat()}Z",
    "",
    "## Overrides from baseline (reconciliation_10k.py)",
    f"  n_total:            {N_TOTAL_BASELINE:,} → {N_TOTAL_US:,} (30×)",
    f"  N (downstream pop): {N_DOWNSTREAM_BASELINE:,} → {N_DOWNSTREAM_US:,} (35×)",
    f"  flights/year:       {FLIGHTS_PER_YEAR_BASE:,.0f} → {FLIGHTS_PER_YEAR:,.0f}",
    "",
    "## Unchanged parameters",
    f"  avg_pax_per_flight: {AVG_PAX_PER_FLIGHT}",
    f"  horizon_days:       {HORIZON_DAYS}",
    f"  lead_days:          {LEAD_DAYS}",
    f"  modality:           {RESPONSE_MODALITY}",
    f"  VSL (base_case):    ${VSL:,.0f}  [NOTE: US VSL (~$10-12M) not applied]",
    f"  CM delay:           21 days",
    f"  CM ramp:            14 days",
    f"  CM reduction:       0.60",
    f"  P_event/P_warning:  UNSOURCED SCENARIO ASSUMPTIONS (unchanged from THREAT_CLASSES)",
    "",
    "## Modelling caveat",
    "  Single-compartment SIR with N=350M assumes homogeneous mixing across US national population.",
    "  The model was designed for a metropolitan catchment (N=10M); this is an extrapolation.",
    "  Results are order-of-magnitude estimates, not validated national forecasts.",
    "",
    "## Files NOT modified",
    "  engine.py, parameters.py (locked)",
    "  All existing results/ files preserved",
]
print("\n".join(config_lines))

# ---------------------------------------------------------------------------
# Initial-conditions check: verify lam0 at both scales
# ---------------------------------------------------------------------------
print("\n=== Initial conditions at US scale ===")
from engine import daily_importation_rate

ic_check = {}
for pname, params in WBE_PATHOGENS.items():
    p0  = params["baseline_prevalence_pct"] / 100.0
    phi = mid(*params["detectable_at_arrival_pct_range"]) / 100.0
    lam0_base = daily_importation_rate(p0, phi, 0.0, n_total=N_TOTAL_BASELINE)
    lam0_us   = daily_importation_rate(p0, phi, 0.0, n_total=N_TOTAL_US)
    frac_base = lam0_base / N_DOWNSTREAM_BASELINE
    frac_us   = lam0_us   / N_DOWNSTREAM_US
    ic_check[pname] = {
        "lam0_base": lam0_base, "lam0_us": lam0_us,
        "frac_base": frac_base, "frac_us": frac_us,
    }
    print(f"  {pname}: lam0_base={lam0_base:.1f}, lam0_us={lam0_us:.1f} "
          f"| S/N fraction: base={frac_base:.2e}, us={frac_us:.2e}")


# ---------------------------------------------------------------------------
# B_d grid for US scenario
# ---------------------------------------------------------------------------
def run_bd_us(threat, runner_fn, d):
    icu_frac, icu_los = get_icu_params(threat)
    im, dl = runner_fn(
        threat["pathogen_params"],
        RESPONSE_MODALITY,
        d,
        prevalence_multiplier=threat["prevalence_multiplier"],
        horizon_days=HORIZON_DAYS,
        vsl=VSL,
        n_total=N_TOTAL_US,
        N=N_DOWNSTREAM_US,
        icu_fraction_of_hosp=icu_frac,
        icu_los_days=icu_los if icu_los is not None else 7,
    )
    bd             = max(0.0, dl["total_societal_cost"] - im["total_societal_cost"])
    bd_raw         = dl["total_societal_cost"] - im["total_societal_cost"]
    deaths_averted = max(0.0, dl["cum_deaths"]      - im["cum_deaths"])
    infect_averted = max(0.0, dl["cum_infections"]  - im["cum_infections"])
    return bd, bd_raw, deaths_averted, infect_averted, im, dl


def run_bd_base(threat, runner_fn, d):
    icu_frac, icu_los = get_icu_params(threat)
    im, dl = runner_fn(
        threat["pathogen_params"],
        RESPONSE_MODALITY,
        d,
        prevalence_multiplier=threat["prevalence_multiplier"],
        horizon_days=HORIZON_DAYS,
        vsl=VSL,
        n_total=N_TOTAL_BASELINE,
        N=N_DOWNSTREAM_BASELINE,
        icu_fraction_of_hosp=icu_frac,
        icu_los_days=icu_los if icu_los is not None else 7,
    )
    bd             = max(0.0, dl["total_societal_cost"] - im["total_societal_cost"])
    deaths_averted = max(0.0, dl["cum_deaths"]      - im["cum_deaths"])
    infect_averted = max(0.0, dl["cum_infections"]  - im["cum_infections"])
    return bd, deaths_averted, infect_averted


# ---------------------------------------------------------------------------
# Build mechanism decomposition — SARS-CoV-2, molecular, both scales
# ---------------------------------------------------------------------------
print("\n=== Mechanism decomposition — SARS-CoV-2/molecular, both scales ===")

mech_rows = []
SARS = {"threat_class": "SARS-like", "pathogen_params": PATHOGENS["SARS-CoV-2"],
        "prevalence_multiplier": 1.0, "avian_influenza": False}

print(f"\n{'Lead d':>8} | {'B_A base':>12} | {'B_A US':>12} | {'B_B base':>12} | {'B_B US':>12} | {'ΔCM% base':>10} | {'ΔCM% US':>10}")
print("-" * 90)

_sars_icu_frac = ICU_FRACTIONS.get("SARS-CoV-2")
_sars_icu_los  = ICU_LOS_DAYS.get("SARS-CoV-2")
_sars_icu_kw   = {"icu_fraction_of_hosp": _sars_icu_frac,
                  "icu_los_days": _sars_icu_los if _sars_icu_los is not None else 7}

for d in LEAD_DAYS:
    im_a_b, dl_a_b = run_scenario_a(PATHOGENS["SARS-CoV-2"], "molecular", d,
                                     horizon_days=HORIZON_DAYS, vsl=VSL,
                                     n_total=N_TOTAL_BASELINE, N=N_DOWNSTREAM_BASELINE, **_sars_icu_kw)
    im_b_b, dl_b_b = run_scenario_b(PATHOGENS["SARS-CoV-2"], "molecular", d,
                                     horizon_days=HORIZON_DAYS, vsl=VSL,
                                     n_total=N_TOTAL_BASELINE, N=N_DOWNSTREAM_BASELINE, **_sars_icu_kw)
    im_a_u, dl_a_u = run_scenario_a(PATHOGENS["SARS-CoV-2"], "molecular", d,
                                     horizon_days=HORIZON_DAYS, vsl=VSL,
                                     n_total=N_TOTAL_US, N=N_DOWNSTREAM_US, **_sars_icu_kw)
    im_b_u, dl_b_u = run_scenario_b(PATHOGENS["SARS-CoV-2"], "molecular", d,
                                     horizon_days=HORIZON_DAYS, vsl=VSL,
                                     n_total=N_TOTAL_US, N=N_DOWNSTREAM_US, **_sars_icu_kw)

    ba_base = dl_a_b["total_societal_cost"] - im_a_b["total_societal_cost"]
    bb_base = dl_b_b["total_societal_cost"] - im_b_b["total_societal_cost"]
    ba_us   = dl_a_u["total_societal_cost"] - im_a_u["total_societal_cost"]
    bb_us   = dl_b_u["total_societal_cost"] - im_b_u["total_societal_cost"]

    dcm_pct_base = 100.0 * (bb_base - ba_base) / bb_base if bb_base > 0 else 0.0
    dcm_pct_us   = 100.0 * (bb_us   - ba_us)   / bb_us   if bb_us   > 0 else 0.0

    def fmt(v):
        if abs(v) >= 1e12: return f"${v/1e12:.2f}T"
        if abs(v) >= 1e9:  return f"${v/1e9:.2f}B"
        return f"${v/1e6:.0f}M"

    print(f"{d:>6}d | {fmt(ba_base):>12} | {fmt(ba_us):>12} | {fmt(bb_base):>12} | "
          f"{fmt(bb_us):>12} | {dcm_pct_base:>9.1f}% | {dcm_pct_us:>9.1f}%")

    mech_rows.append({
        "lead_days": d,
        "B_A_base": ba_base, "B_A_us": ba_us,
        "B_B_base": bb_base, "B_B_us": bb_us,
        "dcm_pct_base": dcm_pct_base, "dcm_pct_us": dcm_pct_us,
        "ratio_B_A": ba_us / ba_base if ba_base > 0 else None,
        "ratio_B_B": bb_us / bb_base if bb_base > 0 else None,
    })


# ---------------------------------------------------------------------------
# Portfolio — US scenario
# ---------------------------------------------------------------------------
def build_portfolio_us(scenario_label, runner_fn, include_avian):
    detail_rows  = []
    summary_rows = []

    for prob_scenario, event_key, warning_key in PROB_SCENARIOS:
        for d in LEAD_DAYS:
            threats_used = [t for t in THREAT_CLASSES
                            if (not t["avian_influenza"] or include_avian)]

            bd_cache_us   = {}
            bd_cache_base = {}
            for threat in threats_used:
                bd_u, bd_raw_u, da_u, ia_u, im_u, dl_u = run_bd_us(threat, runner_fn, d)
                bd_b, da_b, ia_b                        = run_bd_base(threat, runner_fn, d)
                bd_cache_us[threat["threat_class"]]   = (bd_u, bd_raw_u, da_u, ia_u)
                bd_cache_base[threat["threat_class"]] = (bd_b, da_b, ia_b)

            portfolio_ev_us   = 0.0
            portfolio_ev_base = 0.0
            portfolio_deaths_us = portfolio_deaths_base = 0.0
            threat_rows = []

            for threat in threats_used:
                p_event   = threat[event_key]
                p_warning = threat[warning_key]

                bd_u, bd_raw_u, da_u, ia_u = bd_cache_us[threat["threat_class"]]
                bd_b, da_b, ia_b           = bd_cache_base[threat["threat_class"]]

                ev_us   = p_event * p_warning * bd_u
                ev_base = p_event * p_warning * bd_b
                ev_deaths_us   = p_event * p_warning * da_u
                ev_deaths_base = p_event * p_warning * da_b

                portfolio_ev_us     += ev_us
                portfolio_ev_base   += ev_base
                portfolio_deaths_us += ev_deaths_us
                portfolio_deaths_base += ev_deaths_base

                threat_rows.append({
                    "scenario":          scenario_label,
                    "avian_included":    include_avian,
                    "prob_scenario":     prob_scenario,
                    "lead_days":         d,
                    "threat_class":      threat["threat_class"],
                    "p_event":           p_event,
                    "p_warning":         p_warning,
                    "Bd_us":             bd_u,
                    "Bd_base":           bd_b,
                    "ratio_Bd":          bd_u / bd_b if bd_b > 0 else None,
                    "ev_us":             ev_us,
                    "ev_base":           ev_base,
                    "deaths_averted_us": da_u,
                    "deaths_averted_base": da_b,
                })

            for row in threat_rows:
                row["pct_of_portfolio_ev_us"] = (
                    100.0 * row["ev_us"] / portfolio_ev_us
                    if portfolio_ev_us > 0 else 0.0
                )
            detail_rows.extend(threat_rows)

            summary_rows.append({
                "scenario":             scenario_label,
                "avian_included":       include_avian,
                "prob_scenario":        prob_scenario,
                "lead_days":            d,
                "n_total_us":           N_TOTAL_US,
                "N_downstream_us":      N_DOWNSTREAM_US,
                "n_total_base":         N_TOTAL_BASELINE,
                "N_downstream_base":    N_DOWNSTREAM_BASELINE,
                "portfolio_ev_us":      portfolio_ev_us,
                "portfolio_ev_base":    portfolio_ev_base,
                "ratio_ev":             portfolio_ev_us / portfolio_ev_base if portfolio_ev_base > 0 else None,
                "cost_per_flight_us":   portfolio_ev_us   / FLIGHTS_PER_YEAR,
                "cost_per_flight_base": portfolio_ev_base / FLIGHTS_PER_YEAR_BASE,
                "deaths_averted_us":    portfolio_deaths_us,
                "deaths_averted_base":  portfolio_deaths_base,
                "flights_per_year_us":  FLIGHTS_PER_YEAR,
                "flights_per_year_base": FLIGHTS_PER_YEAR_BASE,
                "vsl":                  VSL,
                "horizon_days":         HORIZON_DAYS,
            })

    return detail_rows, summary_rows


print("\n=== Building portfolios — US scenario ===")
all_detail  = []
all_summary = []
for scenario_label, runner_fn in [
    ("A_screening_only",                run_scenario_a),
    ("B_screening_plus_countermeasures", run_scenario_b),
]:
    for include_avian in [False, True]:
        label = f"{scenario_label}_{'with' if include_avian else 'without'}_avian"
        print(f"  {label} ...")
        det, summ = build_portfolio_us(scenario_label, runner_fn, include_avian)
        for r in det:  r["portfolio_view"] = label
        for r in summ: r["portfolio_view"] = label
        all_detail.extend(det)
        all_summary.extend(summ)

det_path  = os.path.join(RESULTS_DIR, "portfolio_detail_us.csv")
summ_path = os.path.join(RESULTS_DIR, "portfolio_summary_us.csv")
mech_path = os.path.join(RESULTS_DIR, "mechanism_decomposition_us.csv")

with open(det_path, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(all_detail[0].keys()))
    w.writeheader(); w.writerows(all_detail)
with open(summ_path, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(all_summary[0].keys()))
    w.writeheader(); w.writerows(all_summary)
with open(mech_path, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(mech_rows[0].keys()))
    w.writeheader(); w.writerows(mech_rows)

print(f"Wrote {len(all_detail)} detail rows to {det_path}")
print(f"Wrote {len(all_summary)} summary rows to {summ_path}")
print(f"Wrote {len(mech_rows)} mech rows to {mech_path}")


# ---------------------------------------------------------------------------
# Results summary
# ---------------------------------------------------------------------------
def get_summ(rows, scenario, avian, prob, d):
    for r in rows:
        if (r["scenario"] == scenario
                and str(r["avian_included"]) == str(avian)
                and r["prob_scenario"] == prob
                and int(float(r["lead_days"])) == d):
            return r
    return None

def fmt_M(v):
    if v is None: return "n/a"
    if abs(v) >= 1e12: return f"${v/1e12:.2f}T"
    if abs(v) >= 1e9:  return f"${v/1e9:.2f}B"
    return f"${v/1e6:.1f}M"

print("\n\n" + "="*95)
print("=== RESULTS SUMMARY: n=10,000 / N=10M (BASELINE) vs n=300,000 / N=350M (US SCENARIO) ===")
print("="*95)
print("Configuration: d=5 days, base probability assumptions, molecular screening, VSL=$3.5M")
print("All portfolio EVs are expected annual values (P_event × P_warning × B_d, summed).")
print("P_event and P_warning are UNSOURCED SCENARIO ASSUMPTIONS — unchanged from baseline.")
print("MODELLING CAVEAT: N=350M uses single-compartment SIR (national mixing not validated).")
print()

# --- Primary results table (excl. avian) ---
print(f"{'Scenario':35} | {'Baseline EV':>12} | {'US EV':>14} | {'Per-flight (US)':>16} | {'Deaths/yr (US)':>15}")
print("-" * 100)
for scen_lbl, scen_short in [
    ("A_screening_only", "Scen A — screening only"),
    ("B_screening_plus_countermeasures", "Scen B — screening + CM"),
]:
    for d in LEAD_DAYS:
        r = get_summ(all_summary, scen_lbl, False, "base", d)
        if r:
            print(f"{scen_short + f', d={d}':35} | "
                  f"{fmt_M(r['portfolio_ev_base']):>12} | "
                  f"{fmt_M(r['portfolio_ev_us']):>14} | "
                  f"${r['cost_per_flight_us']:>14,.0f} | "
                  f"{r['deaths_averted_us']:>13.2f}")

print()
print("--- Avian-influenza stress test (SEPARATE — not in primary figures) ---")
for scen_lbl, scen_short in [
    ("A_screening_only", "Scen A + avian [STRESS]"),
    ("B_screening_plus_countermeasures", "Scen B + avian [STRESS]"),
]:
    for d in [5]:
        r = get_summ(all_summary, scen_lbl, True, "base", d)
        if r:
            print(f"{scen_short + f', d={d}':35} | "
                  f"{fmt_M(r['portfolio_ev_base']):>12} | "
                  f"{fmt_M(r['portfolio_ev_us']):>14} | "
                  f"${r['cost_per_flight_us']:>14,.0f} | "
                  f"{r['deaths_averted_us']:>13.2f}")

print()
print("--- Low / base / high probability sensitivity, d=5, Scen B, excl. avian ---")
print(f"{'Probability scenario':25} | {'Baseline EV':>12} | {'US EV':>14} | {'Per-flight (US)':>16}")
print("-" * 74)
for prob in ["low", "base", "high"]:
    r = get_summ(all_summary, "B_screening_plus_countermeasures", False, prob, 5)
    if r:
        print(f"{prob:25} | {fmt_M(r['portfolio_ev_base']):>12} | "
              f"{fmt_M(r['portfolio_ev_us']):>14} | ${r['cost_per_flight_us']:>14,.0f}")

print()
print("--- Per-threat-class breakdown, d=5, Scen B, base prob, excl. avian ---")
print(f"{'Threat class':45} | {'Bd_base':>12} | {'Bd_us':>14} | {'Ratio':>7} | {'% of US EV':>11}")
print("-" * 98)
det_d5_b = [r for r in all_detail
            if r["scenario"] == "B_screening_plus_countermeasures"
            and not r["avian_included"]
            and r["prob_scenario"] == "base"
            and int(float(r["lead_days"])) == 5]
for r in det_d5_b:
    ratio = r["ratio_Bd"]
    ratio_str = f"{ratio:.1f}×" if ratio is not None else "n/a"
    print(f"{r['threat_class']:45} | {fmt_M(r['Bd_base']):>12} | "
          f"{fmt_M(r['Bd_us']):>14} | {ratio_str:>7} | {r['pct_of_portfolio_ev_us']:>10.1f}%")

print()
print("--- Key ratios ---")
r_a5 = get_summ(all_summary, "A_screening_only",                False, "base", 5)
r_b5 = get_summ(all_summary, "B_screening_plus_countermeasures", False, "base", 5)
if r_a5 and r_b5:
    print(f"  n_total ratio (US/base):          {N_TOTAL_US / N_TOTAL_BASELINE:.0f}×")
    print(f"  N ratio (US/base):                {N_DOWNSTREAM_US / N_DOWNSTREAM_BASELINE:.0f}×")
    print(f"  Portfolio EV ratio, Scen A d=5:   {r_a5['ratio_ev']:.1f}×")
    print(f"  Portfolio EV ratio, Scen B d=5:   {r_b5['ratio_ev']:.1f}×")
    print(f"  Flights/year ratio (US/base):      {FLIGHTS_PER_YEAR / FLIGHTS_PER_YEAR_BASE:.0f}×")
    print(f"  Per-flight threshold, Scen A d=5: ${r_a5['cost_per_flight_us']:,.0f} (base: ${r_a5['cost_per_flight_base']:,.0f})")
    print(f"  Per-flight threshold, Scen B d=5: ${r_b5['cost_per_flight_us']:,.0f} (base: ${r_b5['cost_per_flight_base']:,.0f})")

print()
print("--- VSL sensitivity note ---")
print(f"  Base VSL used: ${VSL:,.0f} (parameters.py base_case)")
print(f"  US VSL (Dept of Transportation 2024): ~$12.5M")
print(f"  If US VSL were applied (~{12_500_000/VSL:.1f}× base): all monetary outputs scale proportionally")
r_b5 = get_summ(all_summary, "B_screening_plus_countermeasures", False, "base", 5)
if r_b5:
    us_vsl_scaling = 12_500_000 / VSL
    print(f"  Scen B d=5 US EV at US VSL ($12.5M): ~{fmt_M(r_b5['portfolio_ev_us'] * us_vsl_scaling)} [illustrative only]")

print()
print(f"Files written to: {RESULTS_DIR}/")
print("=== US SCENARIO COMPLETE ===")
