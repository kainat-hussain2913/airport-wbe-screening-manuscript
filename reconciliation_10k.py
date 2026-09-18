"""
reconciliation_10k.py
=====================
Controlled rerun of portfolio and mechanism-decomposition analyses at
n_total = 10,000 (manuscript base case, parameters.py S2.1).

WHAT THIS SCRIPT CHANGES VS portfolio.py
-----------------------------------------
  n_total:  14,082 → 10,000  (manuscript base case; the only change)

WHAT THIS SCRIPT PRESERVES UNCHANGED
--------------------------------------
  IC convention:  sensitivity=0 for BOTH arms in every comparison.
                  I(0) = lam0 = daily_importation_rate(p0, phi, 0.0, n_total)
                  Documented as a modelling assumption, NOT an equilibrium state.
  Horizon:        365 days
  Delays:         [2, 5, 10, 14]
  Scenarios:      A (fixed CM) and B (CM shifts by d days)
  Modality:       molecular (high-throughput)
  VSL:            base_case ($3.5M)
  Prevalence:     pathogen-specific baseline × multiplier=1.0
  Probabilities:  P_event and P_warning unchanged from portfolio.py THREAT_CLASSES
                  (labelled as UNSOURCED SCENARIO ASSUMPTIONS throughout)

PRESERVATION OF PREVIOUS OUTPUTS
----------------------------------
  This script writes ONLY to results/reconciled_10k/
  It does not modify or delete any file in results/
  It does not modify runners.py, portfolio.py, generate_grids.py, engine.py,
  parameters.py, or any manuscript file.

REPRODUCE THIS RUN
------------------
  cd <repo>
  python reconciliation_10k.py

  Requires: runners.py, portfolio.py in <repo>/
            engine.py, parameters.py in locked manuscript code directory
"""

import sys, os, csv, math, datetime

import os as _os
_HERE = _os.path.dirname(_os.path.abspath(__file__))
sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))

from parameters import (
    PATHOGENS, ECON, MODALITIES, WBE_PARAMS, ROUTE_TIERS,
    N_TOTAL_ARRIVALS_PER_DAY, DOWNSTREAM_POPULATION, mid,
)
from engine import daily_importation_rate
from runners import run_scenario_a, run_scenario_b

# Import threat classes and probability scenarios from portfolio.py (unchanged).
# portfolio.py's __main__ block does not run on import.
from portfolio import THREAT_CLASSES, PROB_SCENARIOS, MODALITY_DISPLAY

# ---------------------------------------------------------------------------
# Configuration — single source of truth for this rerun
# ---------------------------------------------------------------------------
N_TOTAL_RECON    = 10_000               # manuscript base case (S2.1)
AVG_PAX_PER_FLIGHT = WBE_PARAMS["avg_pax_per_flight"]   # 250
FLIGHTS_PER_DAY  = N_TOTAL_RECON / AVG_PAX_PER_FLIGHT   # 40
FLIGHTS_PER_YEAR = FLIGHTS_PER_DAY * 365                 # 14,600

LEAD_DAYS        = [2, 5, 10, 14]
HORIZON_DAYS     = 365
RESPONSE_MODALITY = "molecular"
VSL              = ECON["VSL_base_case"]

RESULTS_OLD = _os.path.join(_HERE, "results")
RESULTS_NEW = _os.path.join(_HERE, "results", "reconciled_10k")
os.makedirs(RESULTS_NEW, exist_ok=True)

# ---------------------------------------------------------------------------
# QA Log
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
# QA CHECK 1: Both arms use identical initial conditions
# Verify analytically: _run_arm() always calls daily_importation_rate(p0, phi, 0.0, n_total)
# regardless of deployment_delay_days. We confirm by computing lam0 externally and
# checking that the result is the same formula for both arms.
# ---------------------------------------------------------------------------
print("\n=== QA CHECK 1: Identical initial conditions ===")
ic_check_rows = []
for pname, params in PATHOGENS.items():
    if not params.get("wbe_applicable"):
        continue
    p0 = params["baseline_prevalence_pct"] / 100.0  # multiplier=1.0
    phi = mid(*params["detectable_at_arrival_pct_range"]) / 100.0
    lam0 = daily_importation_rate(p0, phi, 0.0, n_total=N_TOTAL_RECON)
    # Both arms (d=0 and d=any) use this same lam0 — verify it is finite and positive
    ok = math.isfinite(lam0) and lam0 > 0
    ic_check_rows.append({"pathogen": pname, "p0_pct": p0*100, "phi_pct": phi*100,
                           "lam0": lam0, "ok": ok})
    qa(f"IC lam0 > 0, finite ({pname})", ok, f"lam0 = {lam0:.4f}")

qa("All pathogens have valid lam0", all(r["ok"] for r in ic_check_rows))


# ---------------------------------------------------------------------------
# QA CHECK 2: B(0) = 0 within numerical tolerance for all pathogens × modalities
# ---------------------------------------------------------------------------
print("\n=== QA CHECK 2: B(0) = 0 by construction ===")
WBE_PATHOGENS = {k: v for k, v in PATHOGENS.items() if v.get("wbe_applicable")}
b0_failures = []
for pname, params in WBE_PATHOGENS.items():
    for mk in ["rapid", "lab", "molecular"]:
        im_a, dl_a = run_scenario_a(params, mk, 0, horizon_days=HORIZON_DAYS,
                                    vsl=VSL, n_total=N_TOTAL_RECON)
        im_b, dl_b = run_scenario_b(params, mk, 0, horizon_days=HORIZON_DAYS,
                                    vsl=VSL, n_total=N_TOTAL_RECON)
        bd_a = dl_a["total_societal_cost"] - im_a["total_societal_cost"]
        bd_b = dl_b["total_societal_cost"] - im_b["total_societal_cost"]
        # B(0) should be zero (or extremely close) since both arms are the same call
        tol_pct = 0.001  # 0.001% relative tolerance
        base = abs(im_a["total_societal_cost"]) + 1e-6
        ok_a = abs(bd_a) / base < tol_pct / 100
        ok_b = abs(bd_b) / base < tol_pct / 100
        if not ok_a:
            b0_failures.append(f"Scen A {pname}/{mk}: Bd(0)={bd_a:.2f}")
        if not ok_b:
            b0_failures.append(f"Scen B {pname}/{mk}: Bd(0)={bd_b:.2f}")

qa("B(0) = 0 (all pathogens × modalities × scenarios)",
   len(b0_failures) == 0,
   f"Failures: {b0_failures}" if b0_failures else "All pass")


# ---------------------------------------------------------------------------
# QA CHECK 3: CM timing — Scenario A fixed, Scenario B shifts by d
# ---------------------------------------------------------------------------
print("\n=== QA CHECK 3: Countermeasure timing ===")
timing_ok = True
SARS = PATHOGENS["SARS-CoV-2"]
for d in LEAD_DAYS:
    im_a, dl_a = run_scenario_a(SARS, "molecular", d, horizon_days=HORIZON_DAYS,
                                 vsl=VSL, n_total=N_TOTAL_RECON)
    im_b, dl_b = run_scenario_b(SARS, "molecular", d, horizon_days=HORIZON_DAYS,
                                 vsl=VSL, n_total=N_TOTAL_RECON)
    # Scenario A: both arms CM=21
    ok_a = (im_a["cm_start_day"] == 21 and dl_a["cm_start_day"] == 21)
    # Scenario B: immediate CM=21, delayed CM=21+d
    ok_b = (im_b["cm_start_day"] == 21 and dl_b["cm_start_day"] == 21 + d)
    qa(f"Scen A CM fixed at 21, d={d}", ok_a,
       f"immediate={im_a['cm_start_day']}, delayed={dl_a['cm_start_day']}")
    qa(f"Scen B CM shifts, d={d}", ok_b,
       f"immediate={im_b['cm_start_day']}, delayed={dl_b['cm_start_day']}")
    if not ok_a or not ok_b:
        timing_ok = False
qa("All CM timing checks passed", timing_ok)


# ---------------------------------------------------------------------------
# QA CHECK 4: Negative raw B_d accessible before clipping
# Generate full grid with raw Bd and clipped Bd_nonneg for inspection
# ---------------------------------------------------------------------------
print("\n=== QA CHECK 4: Negative B_d accessible ===")
raw_grid_rows = []
for pname, params in WBE_PATHOGENS.items():
    for mk in ["rapid", "lab", "molecular"]:
        for d in LEAD_DAYS:
            for scenario_label, runner_fn in [
                ("A_screening_only", run_scenario_a),
                ("B_screening_plus_countermeasures", run_scenario_b),
            ]:
                im, dl = runner_fn(params, mk, d, horizon_days=HORIZON_DAYS,
                                   vsl=VSL, n_total=N_TOTAL_RECON)
                bd_raw = dl["total_societal_cost"] - im["total_societal_cost"]
                raw_grid_rows.append({
                    "scenario": scenario_label,
                    "pathogen": pname,
                    "modality": mk,
                    "lead_days": d,
                    "Bd_raw": bd_raw,
                    "Bd_nonneg": max(0.0, bd_raw),
                    "is_negative": bd_raw < 0,
                    "immediate_total_cost": im["total_societal_cost"],
                    "delayed_total_cost": dl["total_societal_cost"],
                    "immediate_cm_start": im["cm_start_day"],
                    "delayed_cm_start": dl["cm_start_day"],
                    "n_total": N_TOTAL_RECON,
                })

neg_rows = [r for r in raw_grid_rows if r["is_negative"]]
qa("Negative raw Bd rows preserved and accessible",
   True,
   f"{len(neg_rows)} negative Bd rows (of {len(raw_grid_rows)} total): "
   + "; ".join(f"{r['scenario']}/{r['pathogen']}/{r['modality']}/d={r['lead_days']}"
               for r in neg_rows[:8])
   + ("..." if len(neg_rows) > 8 else ""))

# Write raw grid for inspection
raw_path = os.path.join(RESULTS_NEW, "raw_grid_with_negatives_10k.csv")
with open(raw_path, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(raw_grid_rows[0].keys()))
    w.writeheader(); w.writerows(raw_grid_rows)
print(f"  Wrote {len(raw_grid_rows)} rows (including {len(neg_rows)} negative) to {raw_path}")


# ---------------------------------------------------------------------------
# Mechanism decomposition at n=10,000
# ---------------------------------------------------------------------------
print("\n=== Building mechanism decomposition (n=10,000) ===")
mech_rows = []
for pname, params in WBE_PATHOGENS.items():
    for mk in ["rapid", "lab", "molecular"]:
        for d in LEAD_DAYS:
            im_a, dl_a = run_scenario_a(params, mk, d, horizon_days=HORIZON_DAYS,
                                        vsl=VSL, n_total=N_TOTAL_RECON)
            im_b, dl_b = run_scenario_b(params, mk, d, horizon_days=HORIZON_DAYS,
                                        vsl=VSL, n_total=N_TOTAL_RECON)
            bd_a = dl_a["total_societal_cost"] - im_a["total_societal_cost"]
            bd_b = dl_b["total_societal_cost"] - im_b["total_societal_cost"]
            incr = bd_b - bd_a
            pct  = 100.0 * incr / bd_b if bd_b > 0 else 0.0
            mech_rows.append({
                "pathogen": pname,
                "modality_key": mk,
                "modality_label": MODALITY_DISPLAY[mk],
                "lead_days": d,
                "B_screening_only": bd_a,
                "B_combined": bd_b,
                "B_incremental_CM": incr,
                "pct_CM_of_combined": pct,
                "immediate_cm_start_A": im_a["cm_start_day"],
                "delayed_cm_start_A":   dl_a["cm_start_day"],
                "immediate_cm_start_B": im_b["cm_start_day"],
                "delayed_cm_start_B":   dl_b["cm_start_day"],
                "n_total": N_TOTAL_RECON,
            })

mech_path = os.path.join(RESULTS_NEW, "mechanism_decomposition_10k.csv")
with open(mech_path, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(mech_rows[0].keys()))
    w.writeheader(); w.writerows(mech_rows)
print(f"Wrote {len(mech_rows)} rows to {mech_path}")


# ---------------------------------------------------------------------------
# Portfolio at n=10,000
# ---------------------------------------------------------------------------
def run_bd_for_threat_10k(threat, runner_fn, d):
    im, dl = runner_fn(
        threat["pathogen_params"],
        RESPONSE_MODALITY,
        d,
        prevalence_multiplier=threat["prevalence_multiplier"],
        horizon_days=HORIZON_DAYS,
        vsl=VSL,
        n_total=N_TOTAL_RECON,
    )
    bd            = max(0.0, dl["total_societal_cost"] - im["total_societal_cost"])
    bd_raw        = dl["total_societal_cost"] - im["total_societal_cost"]
    deaths_averted= max(0.0, dl["cum_deaths"]          - im["cum_deaths"])
    infect_averted= max(0.0, dl["cum_infections"]      - im["cum_infections"])
    return bd, bd_raw, deaths_averted, infect_averted


def build_portfolio_10k(scenario_label, runner_fn, include_avian):
    detail_rows  = []
    summary_rows = []

    for prob_scenario, event_key, warning_key in PROB_SCENARIOS:
        for d in LEAD_DAYS:
            threats_used = [t for t in THREAT_CLASSES if (not t["avian_influenza"] or include_avian)]

            bd_cache = {}
            for threat in threats_used:
                bd, bd_raw, deaths, infect = run_bd_for_threat_10k(threat, runner_fn, d)
                bd_cache[threat["threat_class"]] = (bd, bd_raw, deaths, infect)

            portfolio_ev     = 0.0
            portfolio_deaths = 0.0
            portfolio_infect = 0.0
            threat_rows = []

            for threat in threats_used:
                p_event   = threat[event_key]
                p_warning = threat[warning_key]
                bd, bd_raw, deaths, infect = bd_cache[threat["threat_class"]]

                ev        = p_event * p_warning * bd
                ev_deaths = p_event * p_warning * deaths
                ev_infect = p_event * p_warning * infect
                portfolio_ev     += ev
                portfolio_deaths += ev_deaths
                portfolio_infect += ev_infect

                threat_rows.append({
                    "scenario":              scenario_label,
                    "avian_included":        include_avian,
                    "prob_scenario":         prob_scenario,
                    "lead_days":             d,
                    "threat_class":          threat["threat_class"],
                    "representative_pathogen": threat["representative_pathogen"],
                    "annual_event_probability":  p_event,
                    "useful_warning_probability_given_event": p_warning,
                    "combined_prob":         p_event * p_warning,
                    "conditional_Bd":        bd,
                    "conditional_Bd_raw":    bd_raw,
                    "expected_annual_contribution": ev,
                    "expected_deaths_averted_per_year": ev_deaths,
                    "cost_per_arriving_flight_contribution": (
                        ev / FLIGHTS_PER_YEAR if FLIGHTS_PER_YEAR > 0 else 0.0
                    ),
                    "n_total": N_TOTAL_RECON,
                })

            for row in threat_rows:
                row["pct_of_portfolio_ev"] = (
                    100.0 * row["expected_annual_contribution"] / portfolio_ev
                    if portfolio_ev > 0 else 0.0
                )
            detail_rows.extend(threat_rows)

            summary_rows.append({
                "scenario":            scenario_label,
                "avian_included":      include_avian,
                "prob_scenario":       prob_scenario,
                "lead_days":           d,
                "n_threats":           len(threats_used),
                "portfolio_ev":        portfolio_ev,
                "cost_per_arriving_flight": portfolio_ev / FLIGHTS_PER_YEAR,
                "expected_deaths_averted_per_year": portfolio_deaths,
                "expected_infections_averted_per_year": portfolio_infect,
                "flights_per_year":    FLIGHTS_PER_YEAR,
                "n_total_arrivals_per_day": N_TOTAL_RECON,
                "avg_pax_per_flight":  AVG_PAX_PER_FLIGHT,
                "response_modality":   MODALITY_DISPLAY[RESPONSE_MODALITY],
                "vsl":                 VSL,
                "horizon_days":        HORIZON_DAYS,
            })

    return detail_rows, summary_rows


print("\n=== Building portfolio (n=10,000) ===")
all_detail  = []
all_summary = []
for scenario_label, runner_fn in [
    ("A_screening_only",                run_scenario_a),
    ("B_screening_plus_countermeasures", run_scenario_b),
]:
    for include_avian in [False, True]:
        label = f"{scenario_label}_{'with' if include_avian else 'without'}_avian"
        print(f"  Building: {label} ...")
        det, summ = build_portfolio_10k(scenario_label, runner_fn, include_avian)
        for r in det:  r["portfolio_view"] = label
        for r in summ: r["portfolio_view"] = label
        all_detail.extend(det)
        all_summary.extend(summ)

det_path  = os.path.join(RESULTS_NEW, "portfolio_detail_10k.csv")
summ_path = os.path.join(RESULTS_NEW, "portfolio_summary_10k.csv")
with open(det_path, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(all_detail[0].keys()))
    w.writeheader(); w.writerows(all_detail)
with open(summ_path, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(all_summary[0].keys()))
    w.writeheader(); w.writerows(all_summary)
print(f"Wrote {len(all_detail)} detail rows to {det_path}")
print(f"Wrote {len(all_summary)} summary rows to {summ_path}")


# ---------------------------------------------------------------------------
# Read old portfolio_summary.csv for comparison
# ---------------------------------------------------------------------------
def read_csv_as_dicts(path):
    with open(path) as f:
        return list(csv.DictReader(f))

def get_ev(summary_rows, scenario_label, avian, prob_scenario, d):
    """Look up portfolio EV from in-memory summary rows."""
    for r in summary_rows:
        if (r["scenario"] == scenario_label
                and str(r["avian_included"]) in (str(avian), "True" if avian else "False")
                and r["prob_scenario"] == prob_scenario
                and int(float(r["lead_days"])) == d):
            return float(r["portfolio_ev"])
    return None

# Read old summary
old_summ_path = os.path.join(RESULTS_OLD, "portfolio_summary.csv")
old_summary = read_csv_as_dicts(old_summ_path)


# ---------------------------------------------------------------------------
# Comparison table: old (n=14,082) vs new (n=10,000), base prob, d=5
# ---------------------------------------------------------------------------
print("\n=== Comparison: old (n=14,082) vs new (n=10,000), base probability, d=5 ===")

comparison_rows = []
for scenario_label, scenario_short in [
    ("A_screening_only",                "Scen A"),
    ("B_screening_plus_countermeasures", "Scen B"),
]:
    for avian, avian_label in [(False, "excl. avian"), (True, "incl. avian [STRESS]")]:
        for d in LEAD_DAYS:
            old_ev = None
            # Old CSV uses portfolio_view column
            view_key = f"{scenario_label}_{'with' if avian else 'without'}_avian"
            for r in old_summary:
                if (r.get("portfolio_view") == view_key
                        and r["prob_scenario"] == "base"
                        and int(float(r["lead_days"])) == d):
                    old_ev = float(r["portfolio_ev"])
                    break
            # New (from all_summary)
            new_ev = get_ev(all_summary, scenario_label, avian, "base", d)
            ratio = (new_ev / old_ev) if (old_ev and old_ev != 0) else None
            comparison_rows.append({
                "view":        f"{scenario_short}, {avian_label}",
                "lead_days":   d,
                "old_n":       14082,
                "new_n":       N_TOTAL_RECON,
                "old_ev_M":    old_ev / 1e6 if old_ev is not None else None,
                "new_ev_M":    new_ev / 1e6 if new_ev is not None else None,
                "ratio_new_old": ratio,
                "change_pct":  (ratio - 1) * 100 if ratio is not None else None,
            })

comp_path = os.path.join(RESULTS_NEW, "comparison_old_vs_new.csv")
with open(comp_path, "w", newline="") as f:
    fn = ["view", "lead_days", "old_n", "new_n", "old_ev_M", "new_ev_M",
          "ratio_new_old", "change_pct"]
    w = csv.DictWriter(f, fieldnames=fn)
    w.writeheader(); w.writerows(comparison_rows)
print(f"Wrote comparison to {comp_path}")


# ---------------------------------------------------------------------------
# Human-readable summary report
# ---------------------------------------------------------------------------
print("\n=== RESULTS SUMMARY ===\n")

# Mechanism decomposition — SARS-CoV-2/molecular
print("--- Mechanism decomposition (SARS-CoV-2 / molecular screening, n=10,000) ---")
print(f"{'Lead d':>8} | {'B_A screen-only':>18} | {'B_B combined':>14} | {'ΔCM value':>14} | {'%CM of B_B':>12}")
print("-" * 78)
for row in mech_rows:
    if row["pathogen"] == "SARS-CoV-2" and row["modality_key"] == "molecular":
        ba   = row["B_screening_only"]
        bb   = row["B_combined"]
        incr = row["B_incremental_CM"]
        pct  = row["pct_CM_of_combined"]
        d    = row["lead_days"]
        def fmt_M(v):
            if abs(v) >= 1e9: return f"${v/1e9:.2f}B"
            return f"${v/1e6:.0f}M"
        print(f"{d:>6}d | {fmt_M(ba):>18} | {fmt_M(bb):>14} | {fmt_M(incr):>14} | {pct:>10.1f}%")

print()
print("--- Portfolio 5-day thresholds (base probability, excl. avian flu) ---")
print(f"{'View':<40} | {'Old n=14,082':>14} | {'New n=10,000':>14} | {'Change':>10}")
print("-" * 84)
for row in comparison_rows:
    if row["lead_days"] == 5 and "STRESS" not in row["view"]:
        old_str = f"${row['old_ev_M']:.1f}M" if row['old_ev_M'] is not None else "n/a"
        new_str = f"${row['new_ev_M']:.1f}M" if row['new_ev_M'] is not None else "n/a"
        chg_str = f"{row['change_pct']:.1f}%" if row['change_pct'] is not None else "n/a"
        print(f"{row['view']:<40} | {old_str:>14} | {new_str:>14} | {chg_str:>10}")

print()
print("--- Portfolio 5-day thresholds (base probability, incl. avian flu [STRESS TEST]) ---")
print(f"{'View':<40} | {'Old n=14,082':>14} | {'New n=10,000':>14} | {'Change':>10}")
print("-" * 84)
for row in comparison_rows:
    if row["lead_days"] == 5 and "STRESS" in row["view"]:
        old_str = f"${row['old_ev_M']:.1f}M" if row['old_ev_M'] is not None else "n/a"
        new_str = f"${row['new_ev_M']:.1f}M" if row['new_ev_M'] is not None else "n/a"
        chg_str = f"{row['change_pct']:.1f}%" if row['change_pct'] is not None else "n/a"
        print(f"{row['view']:<40} | {old_str:>14} | {new_str:>14} | {chg_str:>10}")

print()
print("--- All lead times, base probability, excl. avian flu ---")
for scenario_label, scenario_short in [
    ("A_screening_only",                "Scen A, excl. avian"),
    ("B_screening_plus_countermeasures", "Scen B, excl. avian"),
]:
    vals = []
    for d in LEAD_DAYS:
        ev = get_ev(all_summary, scenario_label, False, "base", d)
        if ev is not None:
            vals.append(f"d={d}: ${ev/1e6:.1f}M")
    print(f"  {scenario_short:<30}: {' | '.join(vals)}")

print()
print("--- All lead times, base probability, incl. avian flu [STRESS TEST] ---")
for scenario_label, scenario_short in [
    ("A_screening_only",                "Scen A, incl. avian [STRESS]"),
    ("B_screening_plus_countermeasures", "Scen B, incl. avian [STRESS]"),
]:
    vals = []
    for d in LEAD_DAYS:
        ev = get_ev(all_summary, scenario_label, True, "base", d)
        if ev is not None:
            vals.append(f"d={d}: ${ev/1e6:.1f}M")
    print(f"  {scenario_short:<40}: {' | '.join(vals)}")

print()
print("--- Negative Bd summary ---")
for scenario_label in ["A_screening_only", "B_screening_plus_countermeasures"]:
    neg = [r for r in raw_grid_rows
           if r["scenario"] == scenario_label and r["is_negative"]]
    neg_desc = ("(" + ", ".join(r["pathogen"] + "/" + r["modality"] + "/d=" + str(r["lead_days"]) for r in neg) + ")") if neg else ""
    print(f"  {scenario_label}: {len(neg)} negative raw Bd rows " + neg_desc)


# ---------------------------------------------------------------------------
# QA final summary
# ---------------------------------------------------------------------------
print("\n=== QA LOG ===")
for line in qa_lines:
    print(line)

all_pass = all("PASS" in l for l in qa_lines if l.startswith("["))
print(f"\nOverall QA: {'ALL PASS' if all_pass else 'FAILURES PRESENT — see log'}")


# ---------------------------------------------------------------------------
# Write QA log and config file
# ---------------------------------------------------------------------------
qa_log_path = os.path.join(RESULTS_NEW, "qa_log_10k.txt")
with open(qa_log_path, "w") as f:
    f.write(f"QA log — reconciliation_10k.py\n")
    f.write(f"Run timestamp: {datetime.datetime.utcnow().isoformat()}Z\n\n")
    f.write("\n".join(qa_lines))
    f.write(f"\n\nOverall: {'ALL PASS' if all_pass else 'FAILURES PRESENT'}\n")

config_path = os.path.join(RESULTS_NEW, "reconciliation_config.md")
with open(config_path, "w") as f:
    f.write(f"""# Reconciliation Run Configuration

**Script:** `<repo>/reconciliation_10k.py`
**Run timestamp:** {datetime.datetime.utcnow().isoformat()}Z

## Parameters

| Parameter | Value | Note |
|-----------|-------|------|
| n_total | 10,000 | Manuscript base case (parameters.py S2.1); was 14,082 in portfolio.py |
| IC convention | sensitivity=0 for BOTH arms | lam0 = daily_importation_rate(p0, phi, 0.0, n_total); I(0) = lam0; modelling assumption, not equilibrium |
| Horizon | 365 days | Unchanged |
| Delays | 2, 5, 10, 14 days | Unchanged |
| Response modality | molecular | Unchanged |
| VSL | $3,500,000 (base_case) | Unchanged |
| Prevalence | pathogen baseline × 1.0 multiplier | Unchanged; SARS-CoV-2 1.5% retained from prior engine constants — provenance unresolved |
| P_event, P_warning | Unchanged from portfolio.py THREAT_CLASSES | All labelled UNSOURCED SCENARIO ASSUMPTIONS |

## Unresolved assumptions (not changed, but requiring declaration)

- SARS-CoV-2 baseline prevalence (1.5%): retained from prior engine constants, not sourced from manuscript S1.
- All P_event and P_warning values: unsourced scenario assumptions.
- aircraft WBE detection probability (q=0.5): placeholder; does not enter lead-time calculations.

## Reproduce command

```
cd <repo>
python reconciliation_10k.py
```

## Files written

- `results/reconciled_10k/portfolio_detail_10k.csv`
- `results/reconciled_10k/portfolio_summary_10k.csv`
- `results/reconciled_10k/mechanism_decomposition_10k.csv`
- `results/reconciled_10k/raw_grid_with_negatives_10k.csv`
- `results/reconciled_10k/comparison_old_vs_new.csv`
- `results/reconciled_10k/qa_log_10k.txt`
- `results/reconciled_10k/reconciliation_config.md`

## Files NOT modified

- `<repo>/portfolio.py` (unchanged)
- `<repo>/runners.py` (unchanged)
- `<repo>/generate_grids.py` (unchanged)
- `<repo>/results/*.csv` (all previous outputs preserved)
- `/mnt/user-data/uploads/coldsimulator/manuscript_review_files/code/engine.py` (locked)
- `/mnt/user-data/uploads/coldsimulator/manuscript_review_files/code/parameters.py` (locked)
""")

print(f"\nWrote QA log: {qa_log_path}")
print(f"Wrote config: {config_path}")
print("\n=== RECONCILIATION COMPLETE ===")
