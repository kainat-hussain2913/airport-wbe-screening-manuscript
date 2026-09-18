"""
QA and parity checks for the dual-scenario WBE analysis.

All assertions raise RuntimeError on failure with a descriptive message.
The QA log is written to results/qa_log.txt.
"""

import sys, os, csv, math
import os as _os
_HERE = _os.path.dirname(_os.path.abspath(__file__))
sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))

from parameters import PATHOGENS, MODALITIES, ECON, mid
from runners import run_scenario_a, run_scenario_b

RESULTS_DIR = _os.path.join(_HERE, "results")
QA_LOG      = os.path.join(RESULTS_DIR, "qa_log.txt")
EX_ANTE_CSV = _os.path.join(_HERE, "results", "bd_grid_ex_ante_v2.csv")

REL_TOL = 1e-4   # 0.01 % relative tolerance for numerical comparisons

log_lines = []
def log(msg):
    print(msg)
    log_lines.append(msg)

def assert_close(a, b, label, tol=REL_TOL):
    if b == 0 and a == 0:
        return
    rel = abs(a - b) / max(abs(b), 1e-10)
    if rel > tol:
        raise RuntimeError(f"FAIL [{label}]: {a:.6g} vs {b:.6g}  rel={rel:.4%}")
    log(f"  PASS [{label}]: {a:.6g} ≈ {b:.6g}  rel={rel:.4%}")

def assert_zero(v, label, atol=1.0):
    if abs(v) > atol:
        raise RuntimeError(f"FAIL [{label}]: expected ~0, got {v:.6g}")
    log(f"  PASS [{label}]: B(0)={v:.4g} ≈ 0")

def assert_no_nan_inf(rows, label):
    bad = []
    for i, row in enumerate(rows):
        for k, v in row.items():
            try:
                fv = float(v)
                if not math.isfinite(fv):
                    bad.append(f"row {i} col {k}: {v}")
            except (ValueError, TypeError):
                pass
    if bad:
        raise RuntimeError(f"FAIL [{label}] NaN/Inf found:\n  " + "\n  ".join(bad[:10]))
    log(f"  PASS [{label}]: no NaN/Inf in {len(rows)} rows")

def assert_unique_keys(rows, key_cols, label):
    seen = set()
    dupes = []
    for row in rows:
        key = tuple(row[c] for c in key_cols)
        if key in seen:
            dupes.append(key)
        seen.add(key)
    if dupes:
        raise RuntimeError(f"FAIL [{label}]: {len(dupes)} duplicate keys: {dupes[:3]}")
    log(f"  PASS [{label}]: {len(seen)} unique keys in {len(rows)} rows")

def assert_complete_grid(rows, expected_count, label):
    if len(rows) != expected_count:
        raise RuntimeError(f"FAIL [{label}]: expected {expected_count} rows, got {len(rows)}")
    log(f"  PASS [{label}]: {len(rows)} rows == {expected_count} expected")


def run_all_qa(grid_a, grid_b):
    os.makedirs(RESULTS_DIR, exist_ok=True)
    log("=" * 70)
    log("QA LOG — WBE dual-scenario analysis")
    log("=" * 70)

    # --- QA-1: B(0) = 0 for both scenarios, for each pathogen × modality ---
    log("\n[QA-1] B(0) = 0 parity for both scenarios")
    pathogens_to_check = list(PATHOGENS.keys())[:3]  # spot-check first three
    for pname in pathogens_to_check:
        params = PATHOGENS[pname]
        for mk in ["rapid", "lab", "molecular"]:
            im_a, dl_a = run_scenario_a(params, mk, 0)
            im_b, dl_b = run_scenario_b(params, mk, 0)
            b0_a = dl_a["total_societal_cost"] - im_a["total_societal_cost"]
            b0_b = dl_b["total_societal_cost"] - im_b["total_societal_cost"]
            assert_zero(b0_a, f"Scenario A B(0) {pname}/{mk}")
            assert_zero(b0_b, f"Scenario B B(0) {pname}/{mk}")

    # --- QA-2: d=0 parity between Scenario A and Scenario B ---
    log("\n[QA-2] d=0 parity: Scenario A immediate == Scenario B immediate")
    for pname in pathogens_to_check:
        params = PATHOGENS[pname]
        for mk in ["rapid", "molecular"]:
            im_a, _ = run_scenario_a(params, mk, 0)
            im_b, _ = run_scenario_b(params, mk, 0)
            assert_close(im_a["total_societal_cost"], im_b["total_societal_cost"],
                         f"d=0 total cost {pname}/{mk}")
            assert_close(im_a["screening_cost"], im_b["screening_cost"],
                         f"d=0 screening cost {pname}/{mk}")

    # --- QA-3: CM timing correctness ---
    log("\n[QA-3] CM timing: Scenario A fixed, Scenario B shifts by d")
    test_d = 10
    params = PATHOGENS["SARS-CoV-2"]
    _, dl_a = run_scenario_a(params, "molecular", test_d)
    _, dl_b = run_scenario_b(params, "molecular", test_d)
    # Scenario A: CM starts at DEFAULT_CM_DELAY = 21 regardless of d
    if dl_a["cm_start_day"] != 21:
        raise RuntimeError(f"FAIL [QA-3a]: Scenario A CM start = {dl_a['cm_start_day']}, expected 21")
    log(f"  PASS [QA-3a]: Scenario A CM start = {dl_a['cm_start_day']} (fixed at 21 for d={test_d})")
    # Scenario B: CM starts at DEFAULT_CM_DELAY + d = 31
    expected_b = 21 + test_d
    if dl_b["cm_start_day"] != expected_b:
        raise RuntimeError(f"FAIL [QA-3b]: Scenario B CM start = {dl_b['cm_start_day']}, expected {expected_b}")
    log(f"  PASS [QA-3b]: Scenario B CM start = {dl_b['cm_start_day']} (= 21+d for d={test_d})")

    # --- QA-4: B_d = C_late - C_early reconciliation ---
    log("\n[QA-4] B_d = C_late(d) - C_early(0) reconciliation")
    for scenario, runner in [("A", run_scenario_a), ("B", run_scenario_b)]:
        for d in [2, 5, 14]:
            im, dl = runner(PATHOGENS["SARS-CoV-2"], "molecular", d)
            bd_direct = dl["total_societal_cost"] - im["total_societal_cost"]
            # Find in grid
            grid = grid_a if scenario == "A" else grid_b
            match = [r for r in grid
                     if r["pathogen"] == "SARS-CoV-2"
                     and r["modality_key"] == "molecular"
                     and int(r["lead_days"]) == d
                     and r["prevalence_tier"] == "1x"
                     and r["vsl_scenario"] == "base_case"]
            if not match:
                raise RuntimeError(f"FAIL [QA-4]: no row for Scenario {scenario} d={d}")
            bd_csv = float(match[0]["Bd"])
            assert_close(bd_direct, bd_csv, f"Scenario {scenario} B_d={d} reconciliation")

    # --- QA-5: Component reconciliation ---
    log("\n[QA-5] Component cost reconciliation (screening + hosp + prod + mort + icu = total)")
    for scenario, runner in [("A", run_scenario_a), ("B", run_scenario_b)]:
        im, _ = runner(PATHOGENS["Ebola"], "lab", 5)
        comp_sum = (im["screening_cost"] + im["hospital_cost"] +
                    im["productivity_cost"] + im["mortality_cost"] + im["icu_cost"])
        assert_close(comp_sum, im["total_societal_cost"], f"Scenario {scenario} component sum")

    # --- QA-6: No NaN/Inf in full grids ---
    log("\n[QA-6] NaN/Inf checks on full grids")
    assert_no_nan_inf(grid_a, "Scenario A grid")
    assert_no_nan_inf(grid_b, "Scenario B grid")

    # --- QA-7: Unique keys ---
    log("\n[QA-7] Unique key checks")
    key_cols = ["pathogen", "modality_key", "lead_days", "prevalence_tier", "vsl_scenario", "horizon_days"]
    assert_unique_keys(grid_a, key_cols, "Scenario A grid keys")
    assert_unique_keys(grid_b, key_cols, "Scenario B grid keys")

    # --- QA-8: B > 0 for positive delays where we expect cost savings ---
    log("\n[QA-8] B_d > 0 for d > 0 (earlier screening reduces costs for Rt > 1 pathogens)")
    for pname in ["SARS-CoV-2", "Ebola"]:
        params = PATHOGENS[pname]
        im_a, dl_a = run_scenario_a(params, "molecular", 5)
        bd = dl_a["total_societal_cost"] - im_a["total_societal_cost"]
        if bd <= 0:
            raise RuntimeError(f"FAIL [QA-8]: B_A(5) for {pname} = {bd:.2f} (expected > 0)")
        log(f"  PASS [QA-8]: B_A(5) for {pname} = ${bd/1e6:.2f}M > 0")

    # --- QA-9: Scenario B Bd >= Scenario A Bd (CM acceleration can only add value) ---
    log("\n[QA-9] B_B(d) >= B_A(d) for all tested cases")
    for pname in ["SARS-CoV-2", "Ebola"]:
        params = PATHOGENS[pname]
        for d in [2, 5, 10, 14]:
            im_a, dl_a = run_scenario_a(params, "molecular", d)
            im_b, dl_b = run_scenario_b(params, "molecular", d)
            bd_a = dl_a["total_societal_cost"] - im_a["total_societal_cost"]
            bd_b = dl_b["total_societal_cost"] - im_b["total_societal_cost"]
            if bd_b < bd_a - 1.0:   # allow $1 floating point tolerance
                raise RuntimeError(f"FAIL [QA-9]: B_B < B_A for {pname} d={d}: {bd_b:.0f} < {bd_a:.0f}")
            log(f"  PASS [QA-9]: {pname} d={d}: B_B={bd_b/1e6:.2f}M >= B_A={bd_a/1e6:.2f}M")

    log("\n" + "=" * 70)
    log("ALL QA CHECKS PASSED")
    log("=" * 70)

    with open(QA_LOG, "w") as f:
        f.write("\n".join(log_lines))
    print(f"\nQA log written to {QA_LOG}")
