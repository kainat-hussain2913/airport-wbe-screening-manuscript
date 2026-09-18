# Airport passenger screening and aircraft wastewater surveillance

Model code, parameter tables, result files, manuscript and supplementary material for
*Aircraft Wastewater Surveillance for Airport Biosecurity: When Does Early Warning
Deliver Value?*

A deterministic decision-analytic model asks three questions: which passenger-screening
strategy minimises expected societal cost; under what conditions wastewater-gated
follow-up testing improves on universal screening; and what conditional value earlier
warning could deliver if it activated faster screening and countermeasure deployment.

## Start here

| If you want to | Open |
|---|---|
| Read the paper | [`manuscript/manuscript.md`](manuscript/manuscript.md) |
| Read the methods and extended analyses | [`supplementary/supplementary_material.md`](supplementary/supplementary_material.md) |
| Find the file behind a specific table or figure | [`MANIFEST.md`](MANIFEST.md) |
| Re-run the analysis | [Reproducing the results](#reproducing-the-results) below |
| Check what was validated, and what was not | [`VALIDATION.md`](VALIDATION.md) |

## Headline results

| Result | Value | File |
|---|---|---|
| Cost-minimising screening strategy, all six pathogens | high-throughput molecular testing | `results/master_deterministic.csv` |
| Probability it is cost-minimising under PSA | 71.7%–97.2% by pathogen | `results/psa_icu_strategy_probabilities.csv` |
| Maximum favourable fraction for the WBE gate | 41.67% (laboratory PCR follow-up) | `results/wbe_sweep/wbe_threshold_sweep_icu_full_grid.csv` |
| Cost-neutral annual surveillance expenditure, d = 5 days | USD 4.92M (screening only), USD 8.92M (plus countermeasures) | `results/portfolio_summary.csv` |

All figures are conditional on the stated probability assumptions. They are cost-neutrality
thresholds, not realised savings, and none of the aircraft-WBE performance parameters is
empirically estimated — see [Scope and limitations](#scope-and-limitations).

## Repository map

```
manuscript/               manuscript (Markdown and DOCX)
supplementary/            supplementary material (Markdown and DOCX) and its two source workbooks
*.py                      model, analyses and figure scripts — run from the repository root
results/                  every CSV, JSON and .npz output reported in the manuscript
results/national/         Australia and United States national-scale configurations and outputs
results/icu/              ICU-enabled portfolio and national-scale outputs
results/wbe_sweep/        WBE gate parameter sweep and idealised limiting case
figures/                  Figures 1-4 and supplementary figures (PNG and, where produced, SVG)
logs/                     run logs for the three long-running analyses
CONFIGURATION.md          the configuration and seeds every analysis was run under
VALIDATION.md             engine validation, reproduction and stream-identity checks
MANIFEST.md               manuscript claim to file, for every table, figure and promised item
CHECKSUMS.txt             SHA-256 (first 16 hex) of every file here
requirements.txt          pinned dependency versions
```

## The model

- `engine.py` — screening layer, SIR integration (RK4, daily step), societal cost function
- `parameters.py` — pathogen, diagnostic, economic and scenario parameters, with sources
- `icu_parameters.py` — ICU admission fractions, lengths of stay, incremental daily rate
- `runners.py` — scenario runners shared by the portfolio and national-scale analyses
- `portfolio.py` — lead-time value analysis and expenditure thresholds

Missed infected arrivals feed an SIR model of a downstream catchment population, and a
societal cost function prices the resulting burden over a 365-day horizon. Probabilistic
analysis draws 10,000 iterations per pathogen under base seed 20260811, offset by pathogen
index. `CONFIGURATION.md` states every seed.

## Reproducing the results

```bash
pip install -r requirements.txt
```

Every script resolves imports relative to its own directory; there are no absolute paths.
Scripts write into `results/` and `figures/`, overwriting the copies distributed here.
Approximate runtimes on a laptop:

```bash
python3 run_master.py                              # deterministic strategy grid       ~3 min
python3 vsl_sensitivity.py                         # value-of-statistical-life anchors ~1 min
python3 countermeasure_sensitivity.py              # 4x3x3 sweep                       ~4 min
python3 decision_surface.py                        # Figure 3 data
python3 plot_decision_surface.py                   # Figure 3
python3 psa_icu.py                                 # PSA                              ~15 min
python3 psa_icu.py --no-cost-draws \
        --out-prefix psa_icu_midpointcost_control  # PSA control arm                  ~15 min
python3 psa_convergence_icu.py --with-measles      # convergence and decomposition    ~12 min
python3 make_fig4.py                               # Figure 4, from the saved CSV
python3 wbe_threshold_sweep_icu.py                 # WBE gate sweep (Table 4)
python3 plot_wbe_decision_threshold_icu.py         # Supplementary Figure S2
python3 false_positive_breakeven.py                # false-positive follow-up breakeven
python3 reconciliation_10k.py                      # lead-time value analysis, portfolios
python3 wbe_idealised_limit.py                     # WBE gate at its idealised limit
python3 national_scenarios_icu.py                  # Table 6 Panel A thresholds
```

## Scope and limitations

The limitations of the analysis are stated in the manuscript and are not repeated here.
Four points bear on this repository specifically.

- **The aircraft-WBE performance parameters are swept, not estimated.** Detection
  probability, fielded false-positive rate, cost per aircraft sample and achievable
  follow-up coverage are varied over bounding ranges. Nothing in `results/wbe_sweep/`
  is a measurement of real-world aircraft WBE performance.
- **Expenditure thresholds are conditional.** They depend on assumed event and
  actionable-warning probabilities, which are scenario assumptions rather than estimates,
  and they describe cost neutrality rather than money saved.
- **Some ICU inputs are unresolved.** `icu_parameters.py` records, per pathogen, where a
  length of stay or admission fraction has no located primary source; those entries are
  marked `[UNRESOLVED]` in the source annotations and bounded rather than assigned point
  values. Diphtheria carries no ICU term at all.
- **The proprietary simulator** referred to in the manuscript's Software and
  reproducibility section is not part of this repository and is not required by it. No
  numerical result reported in the manuscript is drawn from it.

## Known gaps

Three scripts expect input directories that are not distributed here, because they were
written against an earlier working layout:

- `national_scenarios_icu.py` reads `results/australia_scenario/` and `results/us_scenario/`.
  The equivalent distributed outputs are in `results/national/`.
- `qa.py` reads `results/bd_grid_ex_ante_v2.csv`, an intermediate file that is not distributed.

Their reported outputs are present in `results/` and `results/national/`; only re-running
those three scripts from a clean checkout requires regenerating the missing inputs first.
Every other script listed under [Reproducing the results](#reproducing-the-results) runs
against this checkout as distributed.

`MANIFEST.md` also records one discrepancy found while assembling this repository, between
a computed value and a figure quoted in Extended Methods S-WBE.

## Licence

- Code (`*.py`, `requirements.txt`): MIT — see [`LICENSE`](LICENSE)
- Manuscript, supplementary material, figures and result files: CC BY 4.0 — see
  [`LICENSE-docs.md`](LICENSE-docs.md)

## Funding and competing interests

This work was supported by Avicena Systems Limited. The sponsoring organisation has a
commercial interest in one of the evaluated surveillance platforms. The competing interest
and the methodological safeguards applied in response to it are declared in the manuscript.
