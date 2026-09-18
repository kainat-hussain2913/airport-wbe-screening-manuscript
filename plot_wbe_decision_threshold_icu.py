"""
Figure 5 (ICU-enabled): WBE decision-threshold map.

Generated from results/wbe_sweep/wbe_threshold_sweep_icu_full_grid.csv.
ICU costing is included via the icu_fraction and icu_los_days columns
in that sweep file.

Column-name mapping vs the pre-ICU script:
  pre-ICU CSV: 'q', 'delta_c'
  ICU CSV:     'wbe_detection_prob_q', 'delta_c_wbe_minus_uc' (or wbe_cheaper)

Locked expected maxima for 365-day horizon (ICU-enabled sweep):
  RAT:              20/144 = 13.8889%   (unchanged from pre-ICU)
  Laboratory PCR:   60/144 = 41.6667%   (was 62/144 = 43.06% pre-ICU)
  Sentinel RT-LAMP: 16/144 = 11.1111%   (unchanged from pre-ICU)

REPRODUCE:
  cd <repo>
  python3 plot_wbe_decision_threshold_icu.py
"""
import os, sys
_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import csv
import math
from collections import defaultdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np

from parameters import ECON

SRC     = "results/wbe_sweep/wbe_threshold_sweep_icu_full_grid.csv"
OUT_CSV = "results/wbe_decision_threshold_icu_figure_data.csv"
OUT_FIG_SVG = "figures/wbe_decision_threshold.svg"
OUT_FIG_PNG = "figures/wbe_decision_threshold.png"

MODALITIES = ["RAT", "Laboratory PCR", "Sentinel RT-LAMP"]
CONTOUR_LEVELS = [0.01, 0.05, 0.10, 0.20]

# Column names differ from the pre-ICU sweep CSV
Q_COL    = "wbe_detection_prob_q"       # was "q" in pre-ICU file
COST_COL = "wbe_cost_per_sample"        # same
FAV_COL  = "wbe_cheaper"               # boolean string 'True'/'False'

# Aggregation and axis dimensions (using ICU CSV column names)
agg_dims  = ["pathogen", "prevalence_tier", "wbe_false_positive_rate", "follow_up_coverage"]
axis_dims = ["follow_up_modality", Q_COL, COST_COL]

# ===========================================================================
# Load
# ===========================================================================
with open(SRC) as f:
    rows = list(csv.DictReader(f))

print(f"Loaded {len(rows)} rows from {SRC}")

# ===========================================================================
# Part 1: re-derive aggregation denominator
# ===========================================================================
full_key_counts = defaultdict(int)
for r in rows:
    key = tuple(r[d] for d in agg_dims + axis_dims) + (r.get("avg_pax_per_flight", ""),)
    full_key_counts[key] += 1
n_dupes = sum(1 for v in full_key_counts.values() if v != 1)
print(f"Duplicated full-dimension combinations: {n_dupes} (expect 0)")

cell_rows = defaultdict(list)
for r in rows:
    cell_key = tuple(r[d] for d in axis_dims)
    cell_rows[cell_key].append(r)

cell_sizes = set(len(v) for v in cell_rows.values())
print(f"Distinct per-cell row counts: {cell_sizes} (expect one value)")
assert len(cell_sizes) == 1, "Non-uniform denominator across cells -- STOP."
DENOM = cell_sizes.pop()
print(f"Aggregation denominator (re-derived): {DENOM}")

expected_denom = 1
for d in agg_dims:
    expected_denom *= len(set(r[d] for r in rows))
print(f"Expected denominator from dimension cardinalities: {expected_denom}")
assert DENOM == expected_denom == 144, f"Denominator mismatch: {DENOM} vs 144"

n_modalities = len(set(r["follow_up_modality"] for r in rows))
n_q          = len(set(r[Q_COL] for r in rows))
n_cost       = len(set(r[COST_COL] for r in rows))
expected_cells = n_modalities * n_q * n_cost
print(f"Cells: {len(cell_rows)} expected {expected_cells} "
      f"({n_modalities} mod × {n_q} q × {n_cost} cost)")
assert len(cell_rows) == expected_cells
assert len(rows) == expected_cells * DENOM

# ===========================================================================
# Part 2: compute fraction-favorable surface per modality
# ===========================================================================
q_vals    = sorted(set(float(r[Q_COL]) for r in rows))
cost_vals = sorted(set(float(r[COST_COL]) for r in rows))

surfaces = {}
figure_data_rows = []

for mod in MODALITIES:
    surf = np.zeros((len(q_vals), len(cost_vals)))
    for qi, q in enumerate(q_vals):
        for ci, cost in enumerate(cost_vals):
            matched = None
            for k, v in cell_rows.items():
                if (k[0] == mod
                        and abs(float(k[1]) - q) < 1e-9
                        and abs(float(k[2]) - cost) < 1e-9):
                    matched = v
                    break
            assert matched is not None, f"Missing cell: {mod}, q={q}, cost={cost}"
            assert len(matched) == DENOM
            n_favorable = sum(1 for r in matched if r[FAV_COL] == "True")
            frac = n_favorable / DENOM
            surf[qi, ci] = frac
            figure_data_rows.append(dict(
                follow_up_modality=mod, q=q, wbe_cost_per_sample=cost,
                n_favorable=n_favorable, n_total=DENOM, fraction_favorable=frac,
            ))
    surfaces[mod] = surf

# ===========================================================================
# Part 2.5: derive shared colour-scale ceiling
# ===========================================================================
overall_max = max(surf.max() for surf in surfaces.values())
COLOR_MAX   = math.ceil(overall_max / 0.05) * 0.05
print(f"\nDerived color-scale ceiling: COLOR_MAX={COLOR_MAX:.2f} "
      f"(true max={overall_max*100:.4f}%, horizon={ECON['horizon_days']} days)")

with open(OUT_CSV, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(figure_data_rows[0].keys()))
    w.writeheader()
    w.writerows(figure_data_rows)
print(f"Wrote {len(figure_data_rows)} rows → {OUT_CSV}")

# ===========================================================================
# Part 3: plot
# ===========================================================================
fig, axes = plt.subplots(1, 3, figsize=(16, 5.5), sharex=True, sharey=True)

X, Y = np.meshgrid(cost_vals, q_vals)

im = None
for ax, mod in zip(axes, MODALITIES):
    surf = surfaces[mod]
    im = ax.pcolormesh(X, Y, surf, shading="nearest", cmap="viridis",
                       vmin=0.0, vmax=COLOR_MAX)
    max_frac = surf.max()
    levels_present = [lv for lv in CONTOUR_LEVELS if lv <= max_frac]
    if levels_present:
        cs = ax.contour(X, Y, surf, levels=levels_present, colors="white", linewidths=1.1)
        ax.clabel(cs, fmt=lambda v: f"{v*100:.0f}%", fontsize=8, colors="white")
    ax.set_xscale("log")
    ax.set_xticks(cost_vals)
    ax.get_xaxis().set_major_formatter(mticker.ScalarFormatter())
    ax.set_xlabel("WBE sampling cost per aircraft (USD/sample)")
    ax.set_title(f"{mod}\n(max favourable fraction: {max_frac*100:.2f}%)",
                 fontsize=10.5, pad=8)

axes[0].set_ylabel("Aircraft-level WBE detection probability, q")

cbar = fig.colorbar(im, ax=axes, shrink=0.85, pad=0.02)
cbar.set_label("Fraction of 144 explored scenarios\nwith WBE-gated cheaper than universal (%)")
cbar.ax.yaxis.set_major_formatter(mticker.PercentFormatter(xmax=1.0))

fig.suptitle("WBE-gated screening decision-threshold map, by follow-up modality\n"
             "(exploratory parameter space; ICU costing included; not an empirically validated estimate)",
             fontsize=11, y=1.08)

import os
os.makedirs("figures", exist_ok=True)
fig.savefig(OUT_FIG_SVG, bbox_inches="tight")
fig.savefig(OUT_FIG_PNG, dpi=200, bbox_inches="tight")
print(f"Wrote {OUT_FIG_SVG} and {OUT_FIG_PNG}")

# ===========================================================================
# Part 4: locked-reference validation
# ===========================================================================
EXPECTED_MAXIMA_ICU_365 = {
    "RAT":              20 / 144,  # 13.8889% — unchanged from pre-ICU
    "Laboratory PCR":   60 / 144,  # 41.6667% — was 62/144 = 43.06% pre-ICU
    "Sentinel RT-LAMP": 16 / 144,  # 11.1111% — unchanged from pre-ICU
}

print("\n" + "=" * 78)
print("VALIDATION REPORT (ICU-enabled sweep, 365-day horizon)")
print("=" * 78)

maxima = {mod: surfaces[mod].max() for mod in MODALITIES}
print("\n1. Maxima check:")
all_match = True
for mod in MODALITIES:
    got = maxima[mod]
    exp = EXPECTED_MAXIMA_ICU_365[mod]
    match = abs(got - exp) < 1e-9
    all_match &= match
    print(f"   {mod}: computed={got*100:.4f}%  expected={exp*100:.4f}%  "
          f"[{'MATCH' if match else 'MISMATCH'}]")
print(f"   → {'CONFIRMED' if all_match else 'NOT CONFIRMED'}")
if not all_match:
    raise SystemExit("MISMATCH — do not use this figure. Check CSV or expected maxima.")

n_wrong = sum(1 for r in figure_data_rows if r["n_total"] != 144)
print(f"\n2. Cells with denominator != 144: {n_wrong} (expect 0) → "
      f"{'PASS' if n_wrong == 0 else 'FAIL'}")

print(f"\n3. Duplicate full-dim combos: {n_dupes} (expect 0) → "
      f"{'PASS' if n_dupes == 0 else 'FAIL'}")
print(f"   Total cells: {len(figure_data_rows)}, expected {expected_cells} → "
      f"{'PASS' if len(figure_data_rows) == expected_cells else 'FAIL'}")

import sys
engine_imported = "engine" in sys.modules
print(f"\n4. engine.py imported: {engine_imported} (expect False) → "
      f"{'PASS' if not engine_imported else 'FAIL'}")
print(f"   Figure generated purely from {SRC}.")

lamp_total = n_q * n_cost
lamp_nz = sum(1 for r in figure_data_rows
              if r["follow_up_modality"] == "Sentinel RT-LAMP" and r["n_favorable"] > 0)
print(f"\nSentinel RT-LAMP: {lamp_nz}/{lamp_total} cells with ≥1 favourable scenario.")
print("=" * 78)
