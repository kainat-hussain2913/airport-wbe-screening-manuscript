"""
icu_cost_rate_sensitivity.py
============================
Sensitivity of reported results to the incremental ICU cost rate (USD per ICU
day above the ward rate), over a reference-informed range.

c_icu enters the cost function additively and is linear in the rate; it does
not feed back into transmission. Totals at any rate R are therefore obtained
exactly from the locked outputs as (total - icu) + icu * R / 3000. Step 1
verifies that identity against the engine before any rescaling is used.

REPRODUCE:  python icu_cost_rate_sensitivity.py
"""
import os, csv, json, datetime, sys
_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)

from parameters import PATHOGENS, ICU_STRUCTURE
from engine import run_scenario
from icu_parameters import scenario_icu_kwargs

RATES = [2000, 3000, 4500, 6000]
BASE_RATE = 3000
KEY = "icu_incremental_cost_per_day_IF_EVER_PARAMETERISED"
OUT = os.path.join(_HERE, "results", "icu_cost_sensitivity")
os.makedirs(OUT, exist_ok=True)
PRIMARY = ["none", "rapid", "lab", "molecular"]
TIERS = ["0.5x", "1x", "2x"]

# ---------------------------------------------------------------- step 1
def verify_linearity():
    checks, worst = [], 0.0
    for pathogen in ["SARS-CoV-2", "Influenza A/B", "Ebola", "Norovirus"]:
        params = PATHOGENS[pathogen]
        kw = scenario_icu_kwargs(pathogen)
        for mk in ["none", "molecular"]:
            ICU_STRUCTURE[KEY] = BASE_RATE
            base = run_scenario(params, mk, prevalence_multiplier=1.0, **kw)
            for R in RATES:
                ICU_STRUCTURE[KEY] = R
                got = run_scenario(params, mk, prevalence_multiplier=1.0, **kw)
                pred = base["total_societal_cost"] - base["icu_cost"] + base["icu_cost"] * R / BASE_RATE
                rel = abs(got["total_societal_cost"] - pred) / max(1.0, abs(pred))
                worst = max(worst, rel)
                checks.append((pathogen, mk, R, rel))
                # health outcomes must not move with a cost parameter
                assert abs(got["cumulative_infections"] - base["cumulative_infections"]) < 1e-9
                assert abs(got["cumulative_deaths"] - base["cumulative_deaths"]) < 1e-9
    ICU_STRUCTURE[KEY] = BASE_RATE
    return len(checks), worst

# ---------------------------------------------------------------- step 2
def load_master():
    p = os.path.join(_HERE, "results", "master_deterministic.csv")
    rows = [r for r in csv.DictReader(open(p))
            if r["wbe_gated"] == "False" and r["route_targeted"] == "False"]
    return rows

def total_at(row, R):
    t = float(row["total_societal_cost"]); i = float(row["icu_cost"])
    return t - i + i * R / BASE_RATE

def main():
    n_checks, worst = verify_linearity()
    print(f"linearity check: {n_checks} cases, worst relative error {worst:.3e}")
    assert worst < 1e-12, "cost is not linear in the ICU rate - rescaling invalid"

    rows = load_master()
    by = {}
    for r in rows:
        by.setdefault((r["pathogen"], r["prevalence_tier"]), {})[r["strategy_key"]] = r

    grid, rank_changes = [], []
    for (pathogen, tier), d in sorted(by.items()):
        if not all(k in d for k in PRIMARY):
            continue
        base_best = min(PRIMARY, key=lambda k: total_at(d[k], BASE_RATE))
        for R in RATES:
            costs = {k: total_at(d[k], R) for k in PRIMARY}
            best = min(costs, key=costs.get)
            b = d[best]
            icu_at_R = float(b["icu_cost"]) * R / BASE_RATE
            grid.append({
                "pathogen": pathogen, "prevalence_scenario": tier, "icu_rate_usd_per_day": R,
                "cost_minimising_strategy": best,
                "total_cost_best": round(costs[best], 2),
                "icu_cost_best": round(icu_at_R, 2),
                "icu_share_of_total_pct": round(100 * icu_at_R / costs[best], 4),
                "pct_change_total_vs_3000": round(
                    100 * (costs[best] / total_at(d[base_best], BASE_RATE) - 1), 4),
                "strategy_changed_vs_3000": best != base_best,
            })
            if best != base_best:
                rank_changes.append((pathogen, tier, R, base_best, best))

    with open(os.path.join(OUT, "icu_rate_grid.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(grid[0].keys())); w.writeheader(); w.writerows(grid)

    # ------------------------------------------------------------ step 3
    fp_src = os.path.join(_HERE, "results", "false_positive_breakeven.csv")
    fp_rows = list(csv.DictReader(open(fp_src)))
    be = []
    for r in fp_rows:
        if not r["breakeven_cost_per_fp"]:
            continue
        key = (r["pathogen"], r["prevalence_tier"])
        d = by.get(key, {})
        LABEL = {"No screening": "none", "RAT": "rapid", "Lab PCR": "lab",
                 "Sentinel RT-LAMP": "molecular"}
        b, a = d.get(LABEL.get(r["best_strategy"])), d.get(LABEL.get(r["comparison_strategy"]))
        if b is None or a is None:
            continue
        fp_diff = float(r["best_fp_cum"]) - float(r["alt_fp_cum"])
        if abs(fp_diff) < 1e-6:
            continue
        row = {"pathogen": r["pathogen"], "prevalence_scenario": r["prevalence_tier"],
               "best_strategy": r["best_strategy"], "comparison_strategy": r["comparison_strategy"],
               "published_breakeven_usd_per_fp": r["breakeven_cost_per_fp"]}
        for R in RATES:
            th = (total_at(a, R) - total_at(b, R)) / fp_diff
            row[f"breakeven_at_{R}"] = round(th, 2) if th > 0 else None
        pub = float(r["breakeven_cost_per_fp"])
        row["pct_change_2000_vs_3000"] = round(100 * (row["breakeven_at_2000"] / pub - 1), 3) if row["breakeven_at_2000"] else None
        row["pct_change_6000_vs_3000"] = round(100 * (row["breakeven_at_6000"] / pub - 1), 3) if row["breakeven_at_6000"] else None
        be.append(row)
    with open(os.path.join(OUT, "icu_rate_fp_breakeven.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(be[0].keys())); w.writeheader(); w.writerows(be)

    # ------------------------------------------------------------ step 4
    unres = os.path.join(_HERE, "results", "sensitivity_icu", "sensitivity_icu_unresolved.csv")
    port = []
    if os.path.exists(unres):
        for r in csv.DictReader(open(unres)):
            if not r["bd_total"]:
                continue
            no_icu = float(r["bd_no_icu"]); incr = float(r["icu_increment"])
            row = {"pathogen": r["pathogen"], "scenario": r["scenario"], "variant": r["variant"],
                   "icu_fraction": r["icu_fraction"], "icu_los_days": r["icu_los_days"],
                   "bd_no_icu": round(no_icu, 2)}
            for R in RATES:
                v = no_icu + incr * R / BASE_RATE
                row[f"bd_at_{R}"] = round(v, 2)
                row[f"icu_share_pct_at_{R}"] = round(100 * (incr * R / BASE_RATE) / v, 4)
            port.append(row)
        with open(os.path.join(OUT, "icu_rate_leadtime_bd.csv"), "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(port[0].keys())); w.writeheader(); w.writerows(port)

    meta = {"generated": datetime.datetime.now().isoformat(timespec="seconds"),
            "rates_usd_per_icu_day_incremental": RATES, "base_rate": BASE_RATE,
            "linearity_cases": n_checks, "linearity_worst_relative_error": worst,
            "grid_cells": len(grid), "strategy_rank_changes": rank_changes,
            "fp_breakeven_cells": len(be), "leadtime_rows": len(port)}
    json.dump(meta, open(os.path.join(OUT, "icu_cost_sensitivity_metadata.json"), "w"), indent=2)

    print(f"grid cells {len(grid)} | rank changes {len(rank_changes)} | fp cells {len(be)} | leadtime rows {len(port)}")
    if rank_changes:
        for c in rank_changes: print("  RANK CHANGE:", c)
    else:
        print("  no cost-minimising strategy changes at any rate in", RATES)

if __name__ == "__main__":
    main()
