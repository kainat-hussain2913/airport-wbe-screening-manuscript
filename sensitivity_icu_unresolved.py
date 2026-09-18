"""
sensitivity_icu_unresolved.py
==============================
Sensitivity analysis for ICU parameters with [UNRESOLVED] or [PROXY] labels.

PURPOSE
-------
Requirements 2 and 3 of the ICU implementation review require:
  - Treating norovirus and Ebola ICU inputs explicitly as assumptions
    and testing justified alternatives.
  - Addressing diphtheria in the primary screening analysis (primary
    analysis of single-pathogen B(d), even though diphtheria is absent
    from the portfolio THREAT_CLASSES).

Pathogens / scenarios tested
-----------------------------
1. Norovirus    [UNRESOLVED fraction and LOS]
   Low: fraction=0.01, LOS=1    (very rare ICU; near-zero)
   Mid: fraction=0.03, LOS=2    (current structural placeholder)
   High: fraction=0.05, LOS=3   (upper plausible bound from lit range)
   All three are structural assumptions without primary sources.

2. Ebola        [UNRESOLVED fraction; PROXY LOS]
   Field: fraction=0.05, LOS=5    (field-hospital setting; West Africa 2014-16)
   Mid:   fraction=0.35, LOS=10   (current structural intermediate)
   West:  fraction=0.80, LOS=12   (high-resource Western ICU; approx universal)
   Source: Feldmann NRM 2020 qualitative characterisation of each end.

3. Diphtheria   [UNRESOLVED — treated as zero in portfolio; addressed here]
   Zero:  fraction=None (current — unresolved, treated as 0)
   Low:   fraction=0.10, LOS=5    (plausible lower bound from WHO guidance on
                                    ICU monitoring for laryngeal + cardiac complications)
   High:  fraction=0.30, LOS=7    (plausible upper bound if myocarditis ICU rate
                                    from pre-antibiotic era series were applied)
   Note: these are exploratory bounds; no peer-reviewed fraction exists.
   Diphtheria is NOT in portfolio THREAT_CLASSES; analysis here is
   single-pathogen B(d) to show what the unresolved gap implies.

4. Avian influenza proxy          [PROXY — inherits seasonal influenza 0.17]
   Low proxy: fraction=0.17, LOS=5  (seasonal influenza, current proxy)
   High proxy: fraction=0.50, LOS=8 (intermediate avian-specific; H5N1 severe but
                                      n too small for reliable estimate)
   Note: WHO 2024 H5N1 reports show >80% ICU but ascertainment-biased toward
   severe; 0.50 is a conservative intermediate, not a validated H5N1 estimate.

SCOPE
-----
Runs portfolio at d=5, base probability, no-avian-influenza (for portfolio items),
and single-pathogen B(d) for diphtheria and avian influenza proxy comparison.
Manuscript baseline N_TOTAL=14,082 arrivals/day (N_downstream = parameters.py default).
All sensitivity variants are supplementary — manuscript base case uses mid values.

REPRODUCE
---------
  cd <repo>
  python sensitivity_icu_unresolved.py
"""

import sys, os, csv, json, datetime

import os as _os
sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))

from parameters import PATHOGENS, ECON, MODALITIES, WBE_PARAMS, DOWNSTREAM_POPULATION, mid
from runners import run_scenario_a, run_scenario_b
from portfolio import THREAT_CLASSES, PROB_SCENARIOS
from icu_parameters import (
    get_icu_params, ICU_FRACTIONS, ICU_LOS_DAYS,
    DIPHTHERIA_ICU_UNRESOLVED, DIPHTHERIA_ICU_NOTE,
)
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
D_PRIMARY          = 5          # lead days for primary comparison
AVG_PAX            = WBE_PARAMS["avg_pax_per_flight"]

# Manuscript baseline scale (parameters.py default = 14,082 for Perth airport)
N_TOTAL            = 14_082
N_DOWNSTREAM       = DOWNSTREAM_POPULATION
FLIGHTS_PER_YEAR   = (N_TOTAL / AVG_PAX) * 365


# ---------------------------------------------------------------------------
# Sensitivity grids
# ---------------------------------------------------------------------------

NOROVIRUS_VARIANTS = [
    ("low",  0.01, 1, "Near-zero; very rare ICU for norovirus (immunocompetent)"),
    ("mid",  0.03, 2, "Structural placeholder (current base case)"),
    ("high", 0.05, 3, "Upper plausible bound; no primary source"),
]

EBOLA_VARIANTS = [
    ("field",     0.05, 5,  "Field-hospital / community setting; W Africa 2014-16 <5% formal ICU (Feldmann NRM 2020)"),
    ("mid",       0.35, 10, "Intermediate-resource context (current base case structural assumption)"),
    ("western",   0.80, 12, "High-resource Western ICU setting; near-universal (Feldmann NRM 2020)"),
]

DIPHTHERIA_VARIANTS = [
    ("zero",  None, None, "Unresolved — treated as zero (current base case; NOT a sourced zero)"),
    ("low",   0.10, 5,    "Exploratory lower bound — WHO guidance: ICU monitoring for laryngeal/cardiac complications; no fraction cited"),
    ("high",  0.30, 7,    "Exploratory upper bound — if myocarditis-requiring-ICU rate from clinical guidance applied; no fraction cited"),
]

AVIAN_PROXY_VARIANTS = [
    ("seasonal_proxy", 0.17, 5,  "Current proxy: seasonal influenza FluSurv-NET 16.7% (Lancet Microbe 2023)"),
    ("intermediate",   0.50, 8,  "Intermediate exploratory: conservative avian-specific estimate; NOT a validated H5N1 figure"),
]


# ---------------------------------------------------------------------------
# Single-pathogen B(d) runner
# ---------------------------------------------------------------------------
def compute_bd(pathogen_name, pathogen_params, runner_fn, d, icu_frac, icu_los,
               prevalence_multiplier=1.0):
    icu_los_use = icu_los if icu_los is not None else 7
    im, dl = runner_fn(
        pathogen_params, RESPONSE_MODALITY, d,
        prevalence_multiplier=prevalence_multiplier,
        horizon_days=HORIZON_DAYS, vsl=VSL,
        n_total=N_TOTAL, N=N_DOWNSTREAM,
        icu_fraction_of_hosp=icu_frac,
        icu_los_days=icu_los_use,
    )
    bd = max(0.0, dl["total_societal_cost"] - im["total_societal_cost"])
    bd_no_icu = max(0.0,
        (dl["total_societal_cost"] - dl["icu_cost"]) -
        (im["total_societal_cost"] - im["icu_cost"])
    )
    c_icu_increment = bd - bd_no_icu
    return bd, bd_no_icu, c_icu_increment, dl["cum_deaths"] - im["cum_deaths"]


# ---------------------------------------------------------------------------
# 1. Norovirus sensitivity
# ---------------------------------------------------------------------------
print("\n=== 1. Norovirus ICU sensitivity (Scenario A, d=5) ===")
print(f"{'Variant':<8} {'ICU frac':>9} {'LOS':>5} {'B(d) total':>14} {'B(d) no-ICU':>14} {'ICU increment':>14} {'Δ%':>7}")
print("-" * 80)

noro_rows = []
noro_params = PATHOGENS["Norovirus"]
for variant, frac, los, note in NOROVIRUS_VARIANTS:
    bd, bd_ni, incr, da = compute_bd("Norovirus", noro_params, run_scenario_a,
                                      D_PRIMARY, frac, los)
    delta_pct = 100 * incr / bd_ni if bd_ni > 0 else 0.0
    print(f"  {variant:<6} {frac!r:>9} {los!r:>5} ${bd/1e6:>11.3f}M ${bd_ni/1e6:>11.3f}M ${incr/1e6:>11.3f}M {delta_pct:>+6.2f}%")
    noro_rows.append({
        "pathogen": "Norovirus", "scenario": "A", "lead_days": D_PRIMARY,
        "variant": variant, "icu_fraction": frac, "icu_los_days": los,
        "note": note, "bd_total": bd, "bd_no_icu": bd_ni,
        "icu_increment": incr, "deaths_averted": da, "delta_pct_vs_no_icu": delta_pct,
    })


# ---------------------------------------------------------------------------
# 2. Ebola sensitivity
# ---------------------------------------------------------------------------
print("\n=== 2. Ebola ICU sensitivity (Scenario A, d=5) ===")
print(f"{'Variant':<10} {'ICU frac':>9} {'LOS':>5} {'B(d) total':>14} {'B(d) no-ICU':>14} {'ICU increment':>14} {'Δ%':>7}")
print("-" * 85)

ebola_rows = []
ebola_params = PATHOGENS["Ebola"]
for variant, frac, los, note in EBOLA_VARIANTS:
    bd, bd_ni, incr, da = compute_bd("Ebola", ebola_params, run_scenario_a,
                                      D_PRIMARY, frac, los)
    delta_pct = 100 * incr / bd_ni if bd_ni > 0 else 0.0
    print(f"  {variant:<8} {frac!r:>9} {los!r:>5} ${bd/1e6:>11.3f}M ${bd_ni/1e6:>11.3f}M ${incr/1e6:>11.3f}M {delta_pct:>+6.2f}%")
    ebola_rows.append({
        "pathogen": "Ebola", "scenario": "A", "lead_days": D_PRIMARY,
        "variant": variant, "icu_fraction": frac, "icu_los_days": los,
        "note": note, "bd_total": bd, "bd_no_icu": bd_ni,
        "icu_increment": incr, "deaths_averted": da, "delta_pct_vs_no_icu": delta_pct,
    })


# ---------------------------------------------------------------------------
# 3. Diphtheria sensitivity (primary screening, not portfolio)
# ---------------------------------------------------------------------------
print("\n=== 3. Diphtheria ICU sensitivity — PRIMARY SCREENING ANALYSIS (Scenario A, d=5) ===")
print(f"  Note: {DIPHTHERIA_ICU_NOTE}")
print()
print(f"{'Variant':<8} {'ICU frac':>9} {'LOS':>5} {'B(d) total':>14} {'B(d) no-ICU':>14} {'ICU increment':>14}")
print("-" * 80)

diph_rows = []
diph_params = PATHOGENS["Diphtheria"]
for variant, frac, los, note in DIPHTHERIA_VARIANTS:
    bd, bd_ni, incr, da = compute_bd("Diphtheria", diph_params, run_scenario_a,
                                      D_PRIMARY, frac, los)
    print(f"  {variant:<6} {frac!r:>9} {los!r:>5} ${bd/1e6:>11.3f}M ${bd_ni/1e6:>11.3f}M ${incr/1e6:>11.3f}M")
    diph_rows.append({
        "pathogen": "Diphtheria", "scenario": "A", "lead_days": D_PRIMARY,
        "variant": variant, "icu_fraction": frac, "icu_los_days": los,
        "note": note, "bd_total": bd, "bd_no_icu": bd_ni,
        "icu_increment": incr, "deaths_averted": da,
        "portfolio": False,  # Diphtheria is NOT in THREAT_CLASSES
        "primary_screening": True,
    })


# ---------------------------------------------------------------------------
# 4. Avian influenza proxy comparison
# ---------------------------------------------------------------------------
print("\n=== 4. Avian influenza ICU proxy comparison (Scenario A, d=5) ===")
print(f"{'Variant':<20} {'ICU frac':>9} {'LOS':>5} {'B(d) total':>14} {'B(d) no-ICU':>14} {'ICU increment':>14}")
print("-" * 90)

avian_threat = next(t for t in THREAT_CLASSES if t["avian_influenza"])
avian_rows = []
for variant, frac, los, note in AVIAN_PROXY_VARIANTS:
    bd, bd_ni, incr, da = compute_bd(
        "Avian (H5N1-stress)", avian_threat["pathogen_params"], run_scenario_a,
        D_PRIMARY, frac, los, prevalence_multiplier=avian_threat["prevalence_multiplier"]
    )
    print(f"  {variant:<18} {frac!r:>9} {los!r:>5} ${bd/1e6:>11.3f}M ${bd_ni/1e6:>11.3f}M ${incr/1e6:>11.3f}M")
    avian_rows.append({
        "pathogen": "Avian_H5N1_stress", "scenario": "A", "lead_days": D_PRIMARY,
        "variant": variant, "icu_fraction": frac, "icu_los_days": los,
        "note": note, "bd_total": bd, "bd_no_icu": bd_ni,
        "icu_increment": incr, "deaths_averted": da,
    })


# ---------------------------------------------------------------------------
# 5. Portfolio EV sensitivity: substituting norovirus and Ebola high/low
# ---------------------------------------------------------------------------
print("\n=== 5. Portfolio EV sensitivity (d=5, base, no-avian, Scenario A) ===")
print("    Substituting norovirus and Ebola ICU variants while holding others at mid")
print()

def portfolio_ev(noro_frac, noro_los, ebola_frac, ebola_los, label):
    """Recompute portfolio EV with specified norovirus and Ebola ICU params."""
    ev = 0.0
    for threat in [t for t in THREAT_CLASSES if not t["avian_influenza"]]:
        rep = threat.get("representative_pathogen", "")
        if rep == "Norovirus":
            frac, los = noro_frac, noro_los
        elif rep == "Ebola":
            frac, los = ebola_frac, ebola_los
        else:
            frac, los = get_icu_params(threat)
        bd, _, _, _ = compute_bd(rep, threat["pathogen_params"], run_scenario_a,
                                  D_PRIMARY, frac, los,
                                  prevalence_multiplier=threat["prevalence_multiplier"])
        p_event   = threat["annual_event_probability_base"]
        p_warning = threat["useful_warning_probability_base"]
        ev += p_event * p_warning * bd
    threshold_per_flight = ev / FLIGHTS_PER_YEAR
    print(f"  {label:<40} ${ev/1e6:>9.3f}M/yr   ${threshold_per_flight:>7.2f}/flight")
    return ev, threshold_per_flight

print(f"  {'Variant':<40} {'Portfolio EV':>12}   {'$/flight':>10}")
print("  " + "-" * 65)

# Base case mid values
ev_mid, tpf_mid = portfolio_ev(
    ICU_FRACTIONS["Norovirus"], ICU_LOS_DAYS["Norovirus"],
    ICU_FRACTIONS["Ebola"],    ICU_LOS_DAYS["Ebola"],
    "Mid (base case)"
)
ev_noro_low, _ = portfolio_ev(
    0.01, 1,
    ICU_FRACTIONS["Ebola"], ICU_LOS_DAYS["Ebola"],
    "Norovirus low (frac=0.01, LOS=1)"
)
ev_noro_high, _ = portfolio_ev(
    0.05, 3,
    ICU_FRACTIONS["Ebola"], ICU_LOS_DAYS["Ebola"],
    "Norovirus high (frac=0.05, LOS=3)"
)
ev_ebola_field, _ = portfolio_ev(
    ICU_FRACTIONS["Norovirus"], ICU_LOS_DAYS["Norovirus"],
    0.05, 5,
    "Ebola field (frac=0.05, LOS=5)"
)
ev_ebola_west, _ = portfolio_ev(
    ICU_FRACTIONS["Norovirus"], ICU_LOS_DAYS["Norovirus"],
    0.80, 12,
    "Ebola western (frac=0.80, LOS=12)"
)
ev_worst_case, _ = portfolio_ev(
    0.05, 3,
    0.80, 12,
    "Worst case (noro high + ebola western)"
)
ev_best_case, _ = portfolio_ev(
    0.01, 1,
    0.05, 5,
    "Best case (noro low + ebola field)"
)

print()
pct_range = 100 * (ev_worst_case - ev_best_case) / ev_mid
print(f"  Portfolio EV range across unresolved ICU variants: "
      f"${ev_best_case/1e6:.3f}M – ${ev_worst_case/1e6:.3f}M "
      f"(mid: ${ev_mid/1e6:.3f}M; span: {pct_range:+.1f}% of mid)")


# ---------------------------------------------------------------------------
# Write outputs
# ---------------------------------------------------------------------------
all_rows = noro_rows + ebola_rows + diph_rows + avian_rows
# Collect union of all fieldnames to handle diphtheria's extra columns
all_fields: list[str] = []
seen: set[str] = set()
for row in all_rows:
    for k in row.keys():
        if k not in seen:
            all_fields.append(k); seen.add(k)
out_path = os.path.join(RESULTS_DIR, "sensitivity_icu_unresolved.csv")
with open(out_path, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=all_fields, extrasaction="ignore")
    # fill missing keys with empty string so DictWriter doesn't complain
    def _fill(r):
        return {k: r.get(k, "") for k in all_fields}
    w.writeheader(); w.writerows([_fill(r) for r in all_rows])

meta = {
    "run_datetime_utc": datetime.datetime.utcnow().isoformat() + "Z",
    "engine_path": engine_path,
    "d_primary": D_PRIMARY,
    "prob_scenario": "base",
    "avian_included": False,
    "n_total": N_TOTAL,
    "n_downstream": N_DOWNSTREAM,
    "revised_influenza_icu_fraction": ICU_FRACTIONS["Influenza A"],
    "revised_influenza_icu_los": ICU_LOS_DAYS["Influenza A"],
    "portfolio_ev_sensitivity": {
        "mid":       ev_mid,
        "noro_low":  ev_noro_low,
        "noro_high": ev_noro_high,
        "ebola_field":   ev_ebola_field,
        "ebola_western": ev_ebola_west,
        "worst_case":    ev_worst_case,
        "best_case":     ev_best_case,
    },
}
meta_path = os.path.join(RESULTS_DIR, "sensitivity_icu_metadata.json")
with open(meta_path, "w") as f:
    json.dump(meta, f, indent=2)

print(f"\nWrote {len(all_rows)} rows → {out_path}")
print(f"Metadata → {meta_path}")
print("\nDone.")
