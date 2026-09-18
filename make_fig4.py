"""
make_fig4.py
============
Figure 4 - probability that high-throughput molecular screening is the
cost-minimising strategy, by pathogen, under the ICU-enabled,
test-cost-corrected PSA.

Reads results/psa_icu_strategy_probabilities.csv (written by psa_icu.py) and
writes figures/psa_probability_bar.{png,svg}. No numbers are hard-coded: the
figure, its value labels and its subtitle are derived from the saved CSV and
the run metadata, so the figure cannot drift from the results file.

Shading, palette (Okabe-Ito colourblind-safe), geometry and title text are
unchanged from the original figure_scripts/make_fig4.py: deeper blue >=95%,
amber 85-94%, orange <85%, with a 50% reference line. The only changes are the
input file (ICU-enabled, test-cost-corrected results) and the removal of
hard-coded values.

REPRODUCE:
  python3 make_fig4.py
"""
import csv
import json
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

RESULTS = os.path.join(_HERE, "results", "psa_icu_strategy_probabilities.csv")
META    = os.path.join(_HERE, "results", "psa_icu_metadata.json")
OUTDIR  = os.path.join(_HERE, "figures")
MOLECULAR_LABEL = "High-throughput molecular screening"
DISPLAY = {"SARS-CoV-2": "SARS-CoV-2", "Influenza A/B": "Influenza A/B", "Mpox": "Mpox",
           "Norovirus": "Norovirus", "Ebola": "Ebola", "Diphtheria": "Diphtheria"}

# Okabe-Ito colourblind-safe palette, as in the original make_fig4.py
BLUE, AMBER, ORANGE = "#0072B2", "#E69F00", "#D55E00"


def band_colour(pct):
    if pct >= 95.0:
        return BLUE
    if pct >= 85.0:
        return AMBER
    return ORANGE


def main():
    rows = []
    with open(RESULTS, newline="") as f:
        for r in csv.DictReader(f):
            if r["strategy"] == MOLECULAR_LABEL:
                rows.append((r["pathogen"], float(r["prob_cost_minimising"]) * 100.0))
    if not rows:
        raise SystemExit(f"No '{MOLECULAR_LABEL}' rows found in {RESULTS}")

    with open(META) as f:
        meta = json.load(f)
    n_iter = meta["n_iter_per_pathogen"]
    seed = meta["base_seed"]
    cost_fixed = meta.get("test_cost_draws_propagated", False)
    if not cost_fixed:
        raise SystemExit("Refusing to build Figure 4 from a run with "
                         "test_cost_draws_propagated=false (that is the control run).")

    names = [DISPLAY.get(p, p) for p, _ in rows]
    vals  = [v for _, v in rows]
    colours = [band_colour(v) for v in vals]

    fig, ax = plt.subplots(figsize=(7, 5))
    bars = ax.bar(names, vals, color=colours, edgecolor="black", linewidth=0.6)
    ax.set_ylim(0, 108)
    ax.set_yticks(range(0, 101, 20))
    ax.set_ylabel("Probability high-throughput molecular\n"
                  "screening is cost-minimising (%)")
    ax.set_title("Probabilistic sensitivity analysis: strategy-selection probability\n"
                 f"({n_iter:,} iterations per pathogen, seed {seed})")
    ax.axhline(50, color="gray", linewidth=0.8, linestyle="--")
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + 1.5, f"{v:.1f}%",
                ha="center", fontsize=9)
    plt.xticks(rotation=20, ha="right")

    fig.tight_layout()
    os.makedirs(OUTDIR, exist_ok=True)
    png = os.path.join(OUTDIR, "psa_probability_bar.png")
    svg = os.path.join(OUTDIR, "psa_probability_bar.svg")
    fig.savefig(png, dpi=200, bbox_inches="tight", pad_inches=0.35)
    fig.savefig(svg, bbox_inches="tight", pad_inches=0.35)
    plt.close(fig)
    print(f"Wrote {png} and {svg}")
    for n, v in zip(names, vals):
        print(f"  {n:16s} {v:6.2f}%  band={band_colour(v)}")


if __name__ == "__main__":
    main()
