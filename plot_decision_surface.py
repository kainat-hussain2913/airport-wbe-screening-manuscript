import csv
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from matplotlib.patches import Patch

rows = list(csv.DictReader(open("results/decision_surface_grid.csv")))
overlay = list(csv.DictReader(open("results/decision_surface_pathogen_overlay.csv")))

rt_vals = sorted(set(float(r["Rt"]) for r in rows))
cost_vals = sorted(set(float(r["cost_per_case"]) for r in rows))
rt_idx = {v: i for i, v in enumerate(rt_vals)}
cost_idx = {v: i for i, v in enumerate(cost_vals)}

strategy_order = ["No systematic screening", "Rapid Antigen Test (RAT)", "Laboratory PCR", "High-throughput molecular screening"]
# Colour-blind-safe (Okabe-Ito palette)
colours = ["#E8E8E8", "#0072B2", "#009E73", "#D55E00"]
cmap = ListedColormap(colours)
strategy_to_code = {s: i for i, s in enumerate(strategy_order)}

grid = np.zeros((len(cost_vals), len(rt_vals)))
for r in rows:
    ci = cost_idx[float(r["cost_per_case"])]
    ri = rt_idx[float(r["Rt"])]
    grid[ci, ri] = strategy_to_code.get(r["winner"], 0)

fig, ax = plt.subplots(figsize=(9, 7), dpi=200)
extent = [min(rt_vals), max(rt_vals), np.log10(min(cost_vals)), np.log10(max(cost_vals))]
im = ax.imshow(grid, origin="lower", aspect="auto", extent=extent, cmap=cmap, vmin=-0.5, vmax=3.5, interpolation="nearest")

ax.set_xlabel("Effective reproduction number, Rt", fontsize=12)
ax.set_ylabel("Expected societal cost per untested infectious case (USD, log scale)", fontsize=12)
ax.set_title("Cost-minimising surveillance strategy\n(illustrative pathogen scenarios overlaid)", fontsize=12)

yticks = [1, 2, 3, 4, 5, 6, 7]
ax.set_yticks(yticks)
ax.set_yticklabels([f"$10^{t}$" for t in yticks])

for r in overlay:
    rt = float(r["Rt"])
    cpc = float(r["cost_per_case"])
    if cpc <= 0:
        continue
    y = np.log10(cpc)
    ax.scatter([rt], [y], s=70, facecolor="white", edgecolor="black", linewidth=1.3, zorder=5)
    ax.annotate(r["pathogen"], (rt, y), textcoords="offset points", xytext=(6, 4),
                fontsize=8.5, fontweight="bold", color="black",
                bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.75))

legend_elems = [Patch(facecolor=colours[i], edgecolor="black", label=strategy_order[i]) for i in range(4)]
ax.legend(handles=legend_elems, loc="upper right", fontsize=9, framealpha=0.95, title="Cost-minimising strategy")

ax.text(0.02, 0.02,
        "Overlaid points: the six primary pathogens (measles is a stress test only, Section 3.8) at their cited midpoint\n"
        "parameters and baseline prevalence, with per-case burden including the incremental ICU cost per hospitalised case.\n"
        "Axes are collapsed to Rt x $/case via a single mortality-equivalent burden parameter; the surface itself carries no\n"
        "hospitalisations, so no ICU cost arises on it (Section 2.6).",
        transform=ax.transAxes, fontsize=6.8, va="bottom", ha="left", color="#333333")
ax.set_xlim(0.5, 3.2)

plt.tight_layout()
plt.savefig("figures/decision_surface.svg", format="svg")
plt.savefig("figures/decision_surface.png", format="png", dpi=300)
print("Saved figures/decision_surface.svg and .png")
