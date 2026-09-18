"""
Generate all tables and figures from the CSVs.
All numbers are read from CSVs — no manual transcription.
Includes table-to-CSV reconciliation assertions.
"""

import sys, os, csv, math
import os as _os
_HERE = _os.path.dirname(_os.path.abspath(__file__))
sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))

RESULTS_DIR = _os.path.join(_HERE, "results")
FIGURES_DIR = _os.path.join(_HERE, "figures")
os.makedirs(FIGURES_DIR, exist_ok=True)

def load(path):
    with open(path) as f: return list(csv.DictReader(f))

def f(path): return os.path.join(RESULTS_DIR, path)

mech    = load(f("mechanism_decomposition.csv"))
summ    = load(f("portfolio_summary.csv"))
detail  = load(f("portfolio_detail.csv"))
grid_a  = load(f("scenario_a_grid.csv"))
grid_b  = load(f("scenario_b_grid.csv"))

def money(v, digits=2):
    v = float(v)
    if abs(v) >= 1e9:  return f"${v/1e9:.{digits}f}B"
    if abs(v) >= 1e6:  return f"${v/1e6:.{digits}f}M"
    return f"${v:,.0f}"

def pct(v): return f"{float(v):.1f}%"

# ============================================================
# TABLE 1: Mechanism decomposition — SARS-CoV-2 & Ebola, molecular
# ============================================================
print("\n" + "="*80)
print("TABLE 1: Mechanism Decomposition — B_screening_only vs B_combined")
print("(Pathogen: SARS-CoV-2 & Ebola | Modality: High-throughput molecular screening)")
print("="*80)

header = f"{'Pathogen':20s} {'d':>3s} {'B_A (screen-only)':>18s} {'B_B (combined)':>16s} {'ΔCM value':>14s} {'%CM of B_B':>12s}"
print(header)
print("-" * len(header))

recon_errs = []
for row in mech:
    if row["modality_key"] != "molecular": continue
    if row["pathogen"] not in ("SARS-CoV-2", "Ebola"): continue
    # Reconcile: B_combined - B_screening_only = B_incremental_CM
    ba  = float(row["B_screening_only"])
    bb  = float(row["B_combined"])
    inc = float(row["B_incremental_CM"])
    recon = abs((bb - ba) - inc)
    if recon > 1.0:
        recon_errs.append(f"Row {row['pathogen']} d={row['lead_days']}: recon error {recon:.2f}")
    print(f"  {row['pathogen']:18s} {int(row['lead_days']):>3d}d {money(ba):>18s} "
          f"{money(bb):>16s} {money(inc):>14s} {pct(row['pct_CM_of_combined']):>12s}")

if recon_errs:
    raise RuntimeError("TABLE 1 reconciliation FAILED:\n" + "\n".join(recon_errs))
print(f"\n  ✓ Table 1 B_combined - B_screening_only = B_incremental_CM reconciled for all rows")

# ============================================================
# TABLE 2: Four-view portfolio comparison — base scenario, d=5
# ============================================================
print("\n" + "="*80)
print("TABLE 2: Four Portfolio Views — base probability scenario, d=5 days lead")
print("(Perth airport: 14,082 arrivals/day | High-throughput molecular response)")
print("NOTE: All probabilities are UNSOURCED SCENARIO ASSUMPTIONS")
print("="*80)

VIEW_LABELS = {
    "A_screening_only_without_avian":               "Scenario A (screen-only), excl. avian flu",
    "A_screening_only_with_avian":                  "Scenario A (screen-only), incl. avian flu [stress test]",
    "B_screening_plus_countermeasures_without_avian": "Scenario B (screen+CM), excl. avian flu",
    "B_screening_plus_countermeasures_with_avian":   "Scenario B (screen+CM), incl. avian flu [stress test]",
}
header2 = f"{'View':55s} {'Max annual spend':>17s} {'Per flight':>11s} {'Deaths/yr':>11s}"
print(header2)
print("-" * len(header2))

for view_key, view_label in VIEW_LABELS.items():
    rows = [r for r in summ
            if r["portfolio_view"] == view_key
            and r["prob_scenario"] == "base"
            and int(r["lead_days"]) == 5]
    assert len(rows) == 1, f"Expected 1 row for view={view_key} base d=5, got {len(rows)}"
    r = rows[0]
    print(f"  {view_label[:53]:53s} {money(r['portfolio_ev']):>17s} "
          f"${float(r['cost_per_arriving_flight']):>10.0f} {float(r['expected_deaths_averted_per_year']):>11.2f}")

# Reconciliation: per-flight = portfolio_ev / flights_per_year
from parameters import WBE_PARAMS
N_TOTAL = 14_082
FPY = N_TOTAL / WBE_PARAMS["avg_pax_per_flight"] * 365
for r in summ:
    recon = abs(float(r["cost_per_arriving_flight"]) - float(r["portfolio_ev"]) / FPY)
    if recon > 0.01:
        raise RuntimeError(f"Table 2 per-flight recon error: {recon:.4f}")
print(f"\n  ✓ Table 2 per-flight = portfolio_ev / flights_per_year reconciled for all {len(summ)} rows")

# ============================================================
# TABLE 3: Threat-class contributions (Scenario B, with avian, base, d=5)
# ============================================================
print("\n" + "="*80)
print("TABLE 3: Threat-class contributions — Scenario B, incl. avian, base prob., d=5")
print("NOTE: probabilities are UNSOURCED SCENARIO ASSUMPTIONS throughout")
print("NOTE: avian influenza = ILLUSTRATIVE STRESS TEST; not a validated H5N1 estimate")
print("="*80)
header3 = f"{'Threat class':40s} {'B(d)':>12s} {'EV contrib':>12s} {'% portfolio':>12s} {'Deaths/yr':>11s}"
print(header3)
print("-" * len(header3))

tc_rows = [r for r in detail
           if r["portfolio_view"] == "B_screening_plus_countermeasures_with_avian"
           and r["prob_scenario"] == "base"
           and int(r["lead_days"]) == 5]
tc_ev_sum = sum(float(r["expected_annual_contribution"]) for r in tc_rows)
for r in tc_rows:
    flag = " [STRESS TEST]" if r["avian_influenza"] == "True" else ""
    print(f"  {(r['threat_class']+flag)[:38]:38s} {money(r['conditional_Bd']):>12s} "
          f"{money(r['expected_annual_contribution']):>12s} "
          f"{pct(r['pct_of_portfolio_ev']):>12s} "
          f"{float(r['expected_deaths_averted_per_year']):>11.3f}")
# Reconcile sum
summ_row = [r for r in summ
            if r["portfolio_view"] == "B_screening_plus_countermeasures_with_avian"
            and r["prob_scenario"] == "base" and int(r["lead_days"]) == 5][0]
recon3 = abs(tc_ev_sum - float(summ_row["portfolio_ev"]))
if recon3 > 1.0:
    raise RuntimeError(f"Table 3 contribution sum recon error: {recon3:.2f}")
print(f"\n  Sum of contributions: {money(tc_ev_sum)} ✓")
print(f"  ✓ Threat-class EV sum reconciles to summary portfolio_ev")

# ============================================================
# TABLE 4: All four views across all d and prob scenarios
# ============================================================
print("\n" + "="*80)
print("TABLE 4: Full four-view × d × prob-scenario matrix (base VSL)")
print("="*80)
for prob_sc in ["low", "base", "high"]:
    print(f"\n  --- {prob_sc.upper()} probability scenario ---")
    print(f"  {'View':50s} {'d=2':>10s} {'d=5':>10s} {'d=10':>10s} {'d=14':>10s}")
    print("  " + "-"*82)
    for view_key, view_label in VIEW_LABELS.items():
        vals = []
        for d in [2, 5, 10, 14]:
            rows = [r for r in summ
                    if r["portfolio_view"] == view_key
                    and r["prob_scenario"] == prob_sc
                    and int(r["lead_days"]) == d]
            vals.append(money(rows[0]["portfolio_ev"], 1) if rows else "N/A")
        print(f"  {view_label[:48]:48s} {vals[0]:>10s} {vals[1]:>10s} {vals[2]:>10s} {vals[3]:>10s}")

print("\n\nAll tables generated from CSV — no manual transcription.")

# ============================================================
# FIGURES
# ============================================================
try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.ticker as mticker
    import numpy as np

    COLORS = {
        "A_excl": "#2166AC",
        "A_incl": "#74ADD1",
        "B_excl": "#D73027",
        "B_incl": "#F4A582",
    }
    VIEW_SHORT = {
        "A_screening_only_without_avian":               ("A_excl", "Scen A, excl. avian"),
        "A_screening_only_with_avian":                  ("A_incl", "Scen A, incl. avian*"),
        "B_screening_plus_countermeasures_without_avian": ("B_excl", "Scen B, excl. avian"),
        "B_screening_plus_countermeasures_with_avian":   ("B_incl", "Scen B, incl. avian*"),
    }

    # Figure 1: Portfolio EV vs lead_days, four views, base prob
    fig, axes = plt.subplots(1, 3, figsize=(15, 5.5), sharey=False)
    for ax_i, prob_sc in enumerate(["low", "base", "high"]):
        ax = axes[ax_i]
        for view_key, (color_key, short_label) in VIEW_SHORT.items():
            ds = [2, 5, 10, 14]
            evs = []
            for d in ds:
                rows = [r for r in summ if r["portfolio_view"] == view_key
                        and r["prob_scenario"] == prob_sc and int(r["lead_days"]) == d]
                evs.append(float(rows[0]["portfolio_ev"]) / 1e6 if rows else 0.0)
            ls = "--" if "incl" in color_key else "-"
            lw = 1.8 if "B_" in color_key else 1.4
            ax.plot(ds, evs, ls=ls, lw=lw, color=COLORS[color_key],
                    marker="o", markersize=5, label=short_label)
        ax.set_title(f"{prob_sc.capitalize()} probability scenario", fontsize=11, fontweight="bold")
        ax.set_xlabel("Lead time d (days)", fontsize=10)
        ax.set_ylabel("Max annual panel spend ($M)", fontsize=10)
        ax.xaxis.set_ticks([2, 5, 10, 14])
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"${x:.0f}M"))
        ax.grid(True, alpha=0.3)
        if ax_i == 2:
            ax.legend(fontsize=8, loc="upper left")
    fig.suptitle(
        "Maximum annual panel surveillance expenditure by scenario and lead time\n"
        "Perth airport (14,082 arr./day) | High-throughput molecular response | Base VSL\n"
        "* avian influenza = illustrative stress test; not a validated H5N1 estimate\n"
        "NOTE: all probabilities are unsourced scenario assumptions",
        fontsize=9, y=1.02
    )
    plt.tight_layout()
    fig1_path = os.path.join(FIGURES_DIR, "fig1_portfolio_comparison.png")
    plt.savefig(fig1_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"\nFigure 1 saved: {fig1_path}")

    # Figure 2: Mechanism decomposition — SARS-CoV-2, all modalities
    fig2, axes2 = plt.subplots(1, 3, figsize=(15, 5.5), sharey=True)
    MODALITY_LABELS = {
        "rapid": "Rapid Antigen Test (RAT)",
        "lab": "Laboratory PCR",
        "molecular": "High-throughput molecular",
    }
    MOD_COLORS = {"rapid": "#E66101", "lab": "#5E3C99", "molecular": "#1B7837"}
    for ax_i, pname in enumerate(["SARS-CoV-2", "Ebola", "Mpox"]):
        ax = axes2[ax_i]
        ds = [2, 5, 10, 14]
        for mk, mk_label in MODALITY_LABELS.items():
            ba_vals, bb_vals = [], []
            for d in ds:
                row = [r for r in mech if r["pathogen"] == pname
                       and r["modality_key"] == mk and int(r["lead_days"]) == d]
                ba_vals.append(float(row[0]["B_screening_only"]) / 1e6 if row else 0)
                bb_vals.append(float(row[0]["B_combined"]) / 1e6 if row else 0)
            ax.plot(ds, bb_vals, color=MOD_COLORS[mk], lw=1.8, marker="o", markersize=5,
                    label=f"{mk_label} (combined)")
            ax.fill_between(ds, ba_vals, bb_vals, color=MOD_COLORS[mk], alpha=0.18,
                            label=f"CM acceleration increment")
            ax.plot(ds, ba_vals, color=MOD_COLORS[mk], lw=1.0, ls="--", marker="s", markersize=4)
        ax.set_title(pname, fontsize=11, fontweight="bold")
        ax.set_xlabel("Lead time d (days)", fontsize=10)
        if ax_i == 0:
            ax.set_ylabel("B_d ($M)", fontsize=10)
        ax.xaxis.set_ticks([2, 5, 10, 14])
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"${x:.0f}M"))
        ax.grid(True, alpha=0.3)
        if ax_i == 0:
            # custom legend
            from matplotlib.lines import Line2D
            custom = [
                Line2D([0],[0], color=MOD_COLORS[mk], lw=1.8, label=MODALITY_LABELS[mk])
                for mk in MODALITY_LABELS
            ] + [Line2D([0],[0], color="grey", lw=1.0, marker="s", ms=5, ls="--",
                         label="Dashed = screen-only B_A")]
            ax.legend(handles=custom, fontsize=7.5, loc="upper left")
    fig2.suptitle(
        "Mechanism decomposition: B_d(screening only) vs B_d(combined)\n"
        "Shaded = incremental value of accelerated countermeasures | 1x prevalence, base VSL, 365-day horizon\n"
        "NOTE: 'causal' interpretation requires both arms differ ONLY in countermeasure timing (QA-verified)",
        fontsize=9, y=1.02
    )
    plt.tight_layout()
    fig2_path = os.path.join(FIGURES_DIR, "fig2_mechanism_decomposition.png")
    plt.savefig(fig2_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Figure 2 saved: {fig2_path}")

except ImportError as e:
    print(f"matplotlib not available ({e}) — figures skipped; CSVs are complete")

print("\nAll tables and figures complete.")
