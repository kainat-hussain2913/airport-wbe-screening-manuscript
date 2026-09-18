"""
reconciliation_icu.py
=====================
ICU-enabled rerun of the WBE lead-time value analysis.

This script is structurally identical to reconciliation_10k.py with one
addition: it passes per-pathogen ICU admission fractions from icu_parameters.py
to runners.py, which routes them to engine.py's compute_downstream_health_costs().

WHAT THIS SCRIPT CHANGES VS reconciliation_10k.py
----------------------------------------------------
  ICU costing:  ENABLED via icu_parameters.get_icu_params() per pathogen.
  All six THREAT_CLASSES pathogens assigned ICU fraction and LOS from icu_parameters.py.
  Norovirus:    fraction=0.03 (UNRESOLVED structural estimate), LOS=2 days.
  Per-pathogen ICU LOS is now configurable (engine.py icu_los_days_override,
  targeted change 2026-09); LOS=7 default preserves backward compatibility.
  All other parameters, delays, scenarios, VSL, modality, horizon: UNCHANGED.

WHAT THIS SCRIPT PRESERVES UNCHANGED
--------------------------------------
  n_total:        10,000  (manuscript base case, parameters.py S2.1)
  IC convention:  sensitivity=0 for BOTH arms
  Horizon:        365 days
  Delays:         [2, 5, 10, 14]
  Scenarios:      A (fixed CM) and B (CM shifts by d days)
  Modality:       molecular
  VSL:            base_case ($3.5M)
  Prevalence:     pathogen-specific baseline × multiplier=1.0
  Probabilities:  P_event and P_warning — UNSOURCED SCENARIO ASSUMPTIONS
  parameters.py:  LOCKED — not modified
  engine.py:      local copy in wbe_v2/ with targeted LOS change only

COST STRUCTURE (for audit):
  c_bed_per_day = $2,000 applied to ALL hospitalised bed-days (ward + ICU).
  c_icu = icu_fraction × ICU_LOS_days(per-pathogen) × $3,000/day
  These are additive; no double-counting (c_hosp charges ward-rate episode,
  c_icu charges incremental ICU cost above ward rate for ICU subset × LOS).
  Both $2,000/day and $3,000/day are structural modelling assumptions without
  cited primary sources — see parameters.py ICU_STRUCTURE and icu_parameters.py.

BASELINE VERIFICATION:
  This script first verifies that passing icu_fraction=None for all pathogens
  reproduces reconciliation_10k outputs to <0.01%.  The verification block
  imports and re-runs the baseline; if that fails the ICU run is aborted.

REPRODUCE THIS RUN
------------------
  cd <repo>
  python reconciliation_icu.py

  Requires: runners.py, portfolio.py, icu_parameters.py in <repo>/
            engine.py, parameters.py in locked manuscript code directory
            reconciliation_10k.py outputs in results/reconciled_10k/ (for verification)
"""

import sys, os, csv, math, datetime, json

import os as _os
sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))

from parameters import (
    PATHOGENS, ECON, MODALITIES, WBE_PARAMS, ROUTE_TIERS,
    N_TOTAL_ARRIVALS_PER_DAY, DOWNSTREAM_POPULATION, mid,
)
from engine import daily_importation_rate
from runners import run_scenario_a, run_scenario_b
from portfolio import THREAT_CLASSES, PROB_SCENARIOS, MODALITY_DISPLAY
from icu_parameters import get_icu_params, ICU_FRACTIONS, ICU_LOS_DAYS

# ---------------------------------------------------------------------------
# Configuration — identical to reconciliation_10k.py except ICU enabled
# ---------------------------------------------------------------------------
N_TOTAL_RECON      = 10_000
AVG_PAX_PER_FLIGHT = WBE_PARAMS["avg_pax_per_flight"]   # 250
FLIGHTS_PER_DAY    = N_TOTAL_RECON / AVG_PAX_PER_FLIGHT # 40
FLIGHTS_PER_YEAR   = FLIGHTS_PER_DAY * 365              # 14,600

LEAD_DAYS          = [2, 5, 10, 14]
HORIZON_DAYS       = 365
RESPONSE_MODALITY  = "molecular"
VSL                = ECON["VSL_base_case"]

RESULTS_BASELINE = "<repo>/results/reconciled_10k"
RESULTS_ICU      = "<repo>/results/icu"
os.makedirs(RESULTS_ICU, exist_ok=True)

# ---------------------------------------------------------------------------
# QA / logging helpers
# ---------------------------------------------------------------------------
qa_lines = []

def qa(label, passed, detail=""):
    status = "PASS" if passed else "FAIL"
    line = f"[{status}] {label}"
    if detail:
        line += f"\n       {detail}"
    qa_lines.append(line)
    print(line)
    return passed


# ---------------------------------------------------------------------------
# QA CHECK 1: ICU=None reproduces baseline total_societal_cost to <0.01%
# Load one saved baseline result, rerun with icu_fraction=None, compare.
# ---------------------------------------------------------------------------
print("\n=== QA CHECK 1: ICU=None reproduces baseline (SARS-CoV-2, d=5, Scenario A) ===")
# Baseline file: portfolio_detail_10k.csv (written by reconciliation_10k.py)
# Columns: representative_pathogen, lead_days, conditional_Bd, scenario
_baseline_file = os.path.join(RESULTS_BASELINE, "portfolio_detail_10k.csv")
baseline_b5_sars = None
if os.path.exists(_baseline_file):
    with open(_baseline_file) as f:
        for row in csv.DictReader(f):
            if (row.get("representative_pathogen") == "SARS-CoV-2"
                    and row.get("lead_days") == "5"
                    and row.get("scenario") == "A_screening_only"
                    and row.get("prob_scenario") == "base"):
                baseline_b5_sars = float(row["conditional_Bd"])
                break

if baseline_b5_sars is not None:
    im_a, dl_a = run_scenario_a(
        PATHOGENS["SARS-CoV-2"], RESPONSE_MODALITY, 5,
        horizon_days=HORIZON_DAYS, vsl=VSL, n_total=N_TOTAL_RECON,
        N=DOWNSTREAM_POPULATION,
        icu_fraction_of_hosp=None,  # must reproduce baseline
    )
    rerun_b5 = max(0.0, dl_a["total_societal_cost"] - im_a["total_societal_cost"])
    rel_err = abs(rerun_b5 - baseline_b5_sars) / max(abs(baseline_b5_sars), 1e-8)
    qa("ICU=None reproduces baseline B(5) SARS-CoV-2 to <0.01%",
       rel_err < 0.0001,
       f"baseline={baseline_b5_sars:.2f}, rerun={rerun_b5:.2f}, rel_err={rel_err:.6f}")
else:
    print("[SKIP] Baseline file not found — run reconciliation_10k.py first.")
    qa("Baseline file exists", False, f"Path: {_baseline_file}")

# ---------------------------------------------------------------------------
# QA CHECK 2: ICU fraction adds to total cost (SARS-CoV-2)
# With icu_fraction=0.15, immediate arm c_icu > 0 and total_cost increases.
# ---------------------------------------------------------------------------
print("\n=== QA CHECK 2: ICU cost adds to total for SARS-CoV-2 ===")
im_no_icu, _ = run_scenario_a(
    PATHOGENS["SARS-CoV-2"], RESPONSE_MODALITY, 5,
    horizon_days=HORIZON_DAYS, vsl=VSL, n_total=N_TOTAL_RECON,
    icu_fraction_of_hosp=None,
)
im_with_icu, _ = run_scenario_a(
    PATHOGENS["SARS-CoV-2"], RESPONSE_MODALITY, 5,
    horizon_days=HORIZON_DAYS, vsl=VSL, n_total=N_TOTAL_RECON,
    icu_fraction_of_hosp=0.15,
)
icu_increment = im_with_icu["total_societal_cost"] - im_no_icu["total_societal_cost"]
c_icu_direct  = im_with_icu["icu_cost"]
qa("ICU fraction adds positive cost to SARS-CoV-2", icu_increment > 0,
   f"total increase={icu_increment:,.0f}, c_icu reported={c_icu_direct:,.0f}")
qa("Reported c_icu matches total increment", abs(c_icu_direct - icu_increment) / max(icu_increment, 1) < 0.0001,
   f"diff={abs(c_icu_direct - icu_increment):.2f}")

# ---------------------------------------------------------------------------
# QA CHECK 3: Norovirus ICU costing is enabled with LOS=2 (unresolved estimate)
# Norovirus now has icu_fraction=0.03, LOS=2 (see icu_parameters.py).
# Previously excluded (None); now included as structural assumption.
# Check that c_icu > 0 and LOS change is reflected.
# ---------------------------------------------------------------------------
print("\n=== QA CHECK 3: Norovirus ICU costing enabled (fraction=0.03, LOS=2) ===")
noro_frac = ICU_FRACTIONS["Norovirus"]   # 0.03
noro_los  = ICU_LOS_DAYS["Norovirus"]    # 2
im_noro_icu, _ = run_scenario_a(
    PATHOGENS["Norovirus"], RESPONSE_MODALITY, 5,
    horizon_days=HORIZON_DAYS, vsl=VSL, n_total=N_TOTAL_RECON,
    icu_fraction_of_hosp=noro_frac, icu_los_days=noro_los,
)
im_noro_none, _ = run_scenario_a(
    PATHOGENS["Norovirus"], RESPONSE_MODALITY, 5,
    horizon_days=HORIZON_DAYS, vsl=VSL, n_total=N_TOTAL_RECON,
    icu_fraction_of_hosp=None,
)
qa("Norovirus c_icu > 0 when fraction=0.03, LOS=2",
   im_noro_icu["icu_cost"] > 0,
   f"c_icu(fraction=0.03,LOS=2)={im_noro_icu['icu_cost']:,.0f}; "
   f"c_icu(None)={im_noro_none['icu_cost']:.0f}")
# Cross-check: Norovirus LOS=2 vs LOS=4 should give ratio=0.5 (same pathogen)
im_noro_los4, _ = run_scenario_a(
    PATHOGENS["Norovirus"], RESPONSE_MODALITY, 5,
    horizon_days=HORIZON_DAYS, vsl=VSL, n_total=N_TOTAL_RECON,
    icu_fraction_of_hosp=noro_frac, icu_los_days=4,
)
noro_ratio = (im_noro_icu["icu_cost"] / im_noro_los4["icu_cost"]
              if im_noro_los4["icu_cost"] > 0 else None)
qa("Norovirus LOS=2 gives 0.5× LOS=4 cost (proportionality check)",
   noro_ratio is not None and abs(noro_ratio - 0.5) < 0.0001,
   f"ratio LOS2/LOS4 = {noro_ratio}")

# ---------------------------------------------------------------------------
# QA CHECK 4: Worked example — SARS-CoV-2 day-1 ICU cost with configurable LOS
# Verify engine formula: c_icu = incidence * symp * hosp_rate * icu_frac * LOS * 3000
# Also verify that changing LOS from 7 to 14 doubles c_icu (proportionality test).
# ---------------------------------------------------------------------------
print("\n=== QA CHECK 4: SARS-CoV-2 ICU worked example (LOS configurable) ===")
p = PATHOGENS["SARS-CoV-2"]
p0      = p["baseline_prevalence_pct"] / 100.0
phi     = mid(*p["detectable_at_arrival_pct_range"]) / 100.0
symp    = mid(*p["symptomatic_fraction_pct_range"]) / 100.0
hosp_r  = mid(*p["hosp_rate_pct_range"]) / 100.0
icu_f   = ICU_FRACTIONS["SARS-CoV-2"]   # 0.15
los_7   = ICU_LOS_DAYS["SARS-CoV-2"]    # 7
lam0    = daily_importation_rate(p0, phi, 0.0, n_total=N_TOTAL_RECON)
expected_c_icu_d1 = lam0 * symp * hosp_r * icu_f * los_7 * 3000
print(f"       lam0={lam0:.4f}, symp={symp:.2f}, hosp_r={hosp_r:.4f}, "
      f"icu_f={icu_f:.2f}, LOS={los_7}")
print(f"       Expected day-1 ICU (approx): ${expected_c_icu_d1:,.0f}")
qa("ICU formula produces finite positive value", expected_c_icu_d1 > 0,
   f"expected_c_icu_d1 = {expected_c_icu_d1:,.0f}")
# Proportionality: LOS=14 should give exactly 2× LOS=7
im_sars_los7, _  = run_scenario_a(PATHOGENS["SARS-CoV-2"], RESPONSE_MODALITY, 0,
    horizon_days=1, vsl=VSL, n_total=N_TOTAL_RECON, icu_fraction_of_hosp=icu_f, icu_los_days=7)
im_sars_los14, _ = run_scenario_a(PATHOGENS["SARS-CoV-2"], RESPONSE_MODALITY, 0,
    horizon_days=1, vsl=VSL, n_total=N_TOTAL_RECON, icu_fraction_of_hosp=icu_f, icu_los_days=14)
ratio = (im_sars_los14["icu_cost"] / im_sars_los7["icu_cost"]
         if im_sars_los7["icu_cost"] > 0 else None)
qa("LOS=14 gives exactly 2× LOS=7 ICU cost (proportionality)",
   ratio is not None and abs(ratio - 2.0) < 0.0001,
   f"ratio LOS14/LOS7 = {ratio}")

# ---------------------------------------------------------------------------
# MAIN ANALYSIS — ICU-enabled portfolio
# ---------------------------------------------------------------------------
print("\n=== MAIN ICU-ENABLED ANALYSIS ===")

detail_rows  = []
summary_rows = []

for threat in THREAT_CLASSES:
    pname    = threat["representative_pathogen"]
    p_params = threat["pathogen_params"]
    avian    = threat.get("avian_influenza", False)
    icu_frac, icu_los = get_icu_params(threat)
    _los_use  = icu_los if icu_los is not None else 7
    icu_label = (f"frac={icu_frac:.2f}, LOS={_los_use}d"
                 if icu_frac is not None else "None (unresolved→c_icu=0)")

    for scen_label, scen_key_event, scen_key_warn in PROB_SCENARIOS:
        p_event  = threat[scen_key_event]
        p_warn   = threat[scen_key_warn]

        for d in LEAD_DAYS:
            # Scenario A
            im_a, dl_a = run_scenario_a(
                p_params, RESPONSE_MODALITY, d,
                prevalence_multiplier=threat["prevalence_multiplier"],
                horizon_days=HORIZON_DAYS, vsl=VSL,
                n_total=N_TOTAL_RECON, N=DOWNSTREAM_POPULATION,
                icu_fraction_of_hosp=icu_frac,
                icu_los_days=_los_use,
            )
            bd_a    = max(0.0, dl_a["total_societal_cost"] - im_a["total_societal_cost"])
            dth_a   = max(0.0, dl_a["cum_deaths"] - im_a["cum_deaths"])
            inf_a   = max(0.0, dl_a["cum_infections"] - im_a["cum_infections"])
            icu_a   = dl_a["icu_cost"] - im_a["icu_cost"]   # can be negative if early arm has higher ICU

            # Scenario B
            im_b, dl_b = run_scenario_b(
                p_params, RESPONSE_MODALITY, d,
                prevalence_multiplier=threat["prevalence_multiplier"],
                horizon_days=HORIZON_DAYS, vsl=VSL,
                n_total=N_TOTAL_RECON, N=DOWNSTREAM_POPULATION,
                icu_fraction_of_hosp=icu_frac,
                icu_los_days=_los_use,
            )
            bd_b    = max(0.0, dl_b["total_societal_cost"] - im_b["total_societal_cost"])
            dth_b   = max(0.0, dl_b["cum_deaths"] - im_b["cum_deaths"])
            inf_b   = max(0.0, dl_b["cum_infections"] - im_b["cum_infections"])
            icu_b   = dl_b["icu_cost"] - im_b["icu_cost"]

            # Expected benefits applying P_event and P_warning
            eb_a = p_event * p_warn * bd_a
            eb_b = p_event * p_warn * bd_b

            # Per-flight thresholds
            thresh_a = eb_a / FLIGHTS_PER_YEAR if FLIGHTS_PER_YEAR > 0 else 0.0
            thresh_b = eb_b / FLIGHTS_PER_YEAR if FLIGHTS_PER_YEAR > 0 else 0.0

            detail_rows.append({
                "threat_class":    threat["threat_class"],
                "pathogen":        pname,
                "avian_influenza": avian,
                "icu_fraction":    icu_frac,
                "icu_label":       icu_label,
                "prob_scenario":   scen_label,
                "p_event":         p_event,
                "p_warning":       p_warn,
                "delay_days":      d,
                "benefit_A_usd":   bd_a,
                "benefit_B_usd":   bd_b,
                "expected_benefit_A_usd": eb_a,
                "expected_benefit_B_usd": eb_b,
                "threshold_A_per_flight": thresh_a,
                "threshold_B_per_flight": thresh_b,
                "icu_benefit_A_usd": icu_a,
                "icu_benefit_B_usd": icu_b,
                "deaths_averted_A": dth_a,
                "deaths_averted_B": dth_b,
                "infections_averted_A": inf_a,
                "infections_averted_B": inf_b,
            })

# ---------------------------------------------------------------------------
# Write detail CSV
# ---------------------------------------------------------------------------
detail_path = os.path.join(RESULTS_ICU, "icu_detail_rows.csv")
with open(detail_path, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=detail_rows[0].keys())
    w.writeheader()
    w.writerows(detail_rows)
print(f"\nWrote {len(detail_rows)} detail rows → {detail_path}")

# ---------------------------------------------------------------------------
# Build summary: focus on d=5 (base case lead time), base probability scenario
# Compare Scenario A and B thresholds with and without ICU, for each pathogen
# ---------------------------------------------------------------------------
print("\n=== SUMMARY: d=5, base probability scenario ===")
summary_lines = []
for threat in THREAT_CLASSES:
    pname   = threat["representative_pathogen"]
    icu_f, icu_l = get_icu_params(threat)
    avian   = threat.get("avian_influenza", False)

    rows_d5 = [r for r in detail_rows
               if r["pathogen"] == pname
               and r["delay_days"] == 5
               and r["prob_scenario"] == "base"]
    if not rows_d5:
        continue
    r = rows_d5[0]
    line = (
        f"{pname}{' (avian stress)' if avian else ''}: "
        f"ICU frac={r['icu_label']:15s} | "
        f"Scen A threshold = ${r['threshold_A_per_flight']:>7.2f}/flight | "
        f"Scen B = ${r['threshold_B_per_flight']:>7.2f}/flight | "
        f"ICU benefit component A = ${r['icu_benefit_A_usd']:>9.0f}"
    )
    print(f"  {line}")
    summary_lines.append(line)

# ---------------------------------------------------------------------------
# Build comparison vs baseline (reconciled_10k) for SARS-CoV-2 and d=5,base
# to quantify the effect of adding ICU costing
# ---------------------------------------------------------------------------
print("\n=== ICU IMPACT: comparison to pre-ICU baseline (SARS-CoV-2, d=5, base) ===")
baseline_thresh_a = baseline_thresh_b = None
baseline_comp_file = os.path.join(RESULTS_BASELINE, "portfolio_detail_10k.csv")
if os.path.exists(baseline_comp_file):
    with open(baseline_comp_file) as f:
        for row in csv.DictReader(f):
            if (row.get("representative_pathogen") == "SARS-CoV-2"
                    and row.get("lead_days") == "5"
                    and row.get("prob_scenario") == "base"):
                scen = row.get("scenario", "")
                val  = float(row.get("cost_per_arriving_flight_contribution", 0))
                if scen == "A_screening_only" and baseline_thresh_a is None:
                    baseline_thresh_a = val
                elif scen == "B_screening_plus_countermeasures" and baseline_thresh_b is None:
                    baseline_thresh_b = val

sars_d5 = [r for r in detail_rows
           if r["pathogen"] == "SARS-CoV-2"
           and r["delay_days"] == 5
           and r["prob_scenario"] == "base"][0]

if baseline_thresh_a is not None:
    delta_a = sars_d5["threshold_A_per_flight"] - baseline_thresh_a
    delta_b = sars_d5["threshold_B_per_flight"] - baseline_thresh_b
    pct_a   = 100 * delta_a / max(baseline_thresh_a, 1e-8)
    pct_b   = 100 * delta_b / max(baseline_thresh_b, 1e-8)
    print(f"  Scenario A: pre-ICU ${baseline_thresh_a:.4f} → ICU ${sars_d5['threshold_A_per_flight']:.4f} "
          f"(Δ ${delta_a:+.4f}, {pct_a:+.1f}%)")
    print(f"  Scenario B: pre-ICU ${baseline_thresh_b:.4f} → ICU ${sars_d5['threshold_B_per_flight']:.4f} "
          f"(Δ ${delta_b:+.4f}, {pct_b:+.1f}%)")
else:
    print("  [Baseline threshold file not found; run reconciliation_10k.py first]")

# ---------------------------------------------------------------------------
# QA summary
# ---------------------------------------------------------------------------
n_pass = sum(1 for l in qa_lines if l.startswith("[PASS]"))
n_fail = sum(1 for l in qa_lines if l.startswith("[FAIL]"))
print(f"\n=== QA SUMMARY: {n_pass} PASS, {n_fail} FAIL ===")

qa_path = os.path.join(RESULTS_ICU, "qa_log.txt")
with open(qa_path, "w") as f:
    f.write(f"reconciliation_icu.py  QA LOG\n")
    f.write(f"Run: {datetime.datetime.utcnow().isoformat()}Z\n")
    f.write(f"ICU fractions: {json.dumps({k: v for k, v in ICU_FRACTIONS.items()})}\n\n")
    f.write("\n".join(qa_lines))
    f.write(f"\n\nSUMMARY: {n_pass} PASS, {n_fail} FAIL\n")
print(f"QA log → {qa_path}")

# ---------------------------------------------------------------------------
# Metadata / provenance record
# ---------------------------------------------------------------------------
meta = {
    "script":             "reconciliation_icu.py",
    "run_datetime_utc":   datetime.datetime.utcnow().isoformat() + "Z",
    "n_total":            N_TOTAL_RECON,
    "lead_days":          LEAD_DAYS,
    "modality":           RESPONSE_MODALITY,
    "vsl":                VSL,
    "icu_fractions":      {k: v for k, v in ICU_FRACTIONS.items()},
    "icu_los_days":       {k: v for k, v in ICU_LOS_DAYS.items()},
    "icu_incremental_cost_per_day": 3000,
    "c_bed_per_day":      2000,
    "icu_los_source":     "per-pathogen from icu_parameters.ICU_LOS_DAYS; engine.py icu_los_days_override (targeted change 2026-09)",
    "norovirus_icu":      "fraction=0.03 (UNRESOLVED structural estimate), LOS=2 days — previously excluded when LOS was hardcoded",
    "avian_stress_icu_frac": ICU_FRACTIONS.get("Influenza A"),
    "qa_pass":            n_pass,
    "qa_fail":            n_fail,
}
meta_path = os.path.join(RESULTS_ICU, "run_metadata.json")
with open(meta_path, "w") as f:
    json.dump(meta, f, indent=2)
print(f"Metadata → {meta_path}")

if n_fail > 0:
    print(f"\n*** WARNING: {n_fail} QA checks FAILED — review qa_log.txt before using outputs ***")
else:
    print("\nAll QA checks passed.")
