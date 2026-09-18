# Manifest — manuscript claim to file

Each row maps an item promised in the manuscript's List of supplementary items or
Data and code availability statement to the file or files that provide it.

## Manuscript

| Item | File |
|---|---|
| Manuscript, Markdown source | `manuscript/manuscript.md` |
| Manuscript, formatted | `manuscript/manuscript.docx` |

## Supplementary document

| Promised | Provided |
|---|---|
| Supplementary Methods S1–S6 | `supplementary/supplementary_material.docx` |
| Extended Methods S-BL, S-MV, S-CM, S-NPI, S-FP, S-PSA, S-Measles, S-WBE, S-90d, S-CB | same document |
| Supplementary Tables S1–S20 | same document |
| Supplementary Figures S1–S2 | same document; source images in `figures/` |
| Markdown source of the above | `supplementary/supplementary_material.md` |
| Pathogen parameter workbook (Table S1) | `supplementary/supplementary_table_S1.xlsx` |
| WBE shedding evidence workbook (Table S2) | `supplementary/supplementary_wbe_shedding.xlsx` |

## Model code and seed

| Promised | Provided |
|---|---|
| Model code | `engine.py`, `parameters.py`, `icu_parameters.py`, `runners.py` |
| Fixed random seed | base seed 20260811, offset by pathogen index — set in `psa_icu.py`, enumerated in `CONFIGURATION.md`, recorded in `results/psa_icu_metadata.json` |
| Full parameter tables with sources | `parameters.py`, `icu_parameters.py`, Supplementary Methods S1–S3, `supplementary/supplementary_table_S1.xlsx` |

## Result files

| Analysis (manuscript section) | Script | Output |
|---|---|---|
| Deterministic strategy grid (3.1–3.3, Table 3, Table S5) | `run_master.py` | `results/master_deterministic.csv` |
| Deterministic reproduction check | `primary_screening_icu_check.py` | `results/primary_screening_icu_ranking.csv` |
| Prevalence scenarios (3.4) | `run_master.py` | `results/master_deterministic.csv` (prevalence_tier column) |
| Value-of-statistical-life sensitivity (3.5) | `vsl_sensitivity.py` | `results/vsl_sensitivity.csv` |
| Countermeasure sensitivity (3.6) | `countermeasure_sensitivity.py` | `results/countermeasure_sensitivity.csv` |
| Probabilistic sensitivity analysis (3.7, Figure 4, Table S6) | `psa_icu.py` | `results/psa_icu_summary.csv`, `results/psa_icu_strategy_probabilities.csv`, `results/psa_icu_metadata.json`, `results/psa_icu_draws_*.npz` |
| PSA midpoint-cost control | `psa_icu.py --no-cost-draws` | `results/psa_icu_midpointcost_control_*` |
| PSA convergence (S-PSA, Table S17) | `psa_convergence_icu.py` | `results/psa_icu_convergence_final.csv` |
| PSA parameter decomposition (3.7) | `psa_convergence_icu.py` | `results/psa_icu_decomposition_*.csv` |
| Measles stress test (3.8, S-Measles, Table S18) | `psa_measles_stress_test.py` | `results/psa_icu_decomposition_Measles.csv`, `results/psa_icu_convergence_final.csv` (measles rows) |
| Decision surface (Figure 3, Figure S1) | `decision_surface.py`, `plot_decision_surface.py` | `results/decision_surface_grid.csv`, `results/decision_surface_pathogen_overlay.csv` |
| False-positive follow-up breakeven (2.6.1, 3.3.1, S-FP, Table S16) | `false_positive_breakeven.py` | `results/false_positive_breakeven.csv` |
| WBE gate threshold sweep (3.9, Table 4, Table S9) | `wbe_threshold_sweep_icu.py` | `results/wbe_sweep/wbe_threshold_sweep_icu_full_grid.csv`, `results/wbe_sweep/wbe_threshold_sweep_icu_metadata.json` |
| WBE favourable-fraction contours (Supplementary Figure S2) | `plot_wbe_decision_threshold_icu.py` | `results/wbe_decision_threshold_icu_figure_data.csv` |
| WBE idealised limiting case (S-WBE, Table S19) | `wbe_idealised_limit.py` | `results/wbe_sweep/wbe_idealised_limit.csv` |
| Lead-time value analysis — configuration record | `reconciliation_10k.py` | `results/reconciled_10k/reconciliation_config.md` |
| Lead-time value analysis — QA log | `qa.py`, `reconciliation_10k.py` | `results/reconciled_10k/qa_log_10k.txt`, `results/icu/qa_log.txt` |
| Lead-time value analysis — raw benefit grid | `reconciliation_10k.py` | `results/reconciled_10k/raw_grid_with_negatives_10k.csv`, `results/scenario_a_grid.csv`, `results/scenario_b_grid.csv` |
| Lead-time value analysis — mechanism decomposition (Table 5 upper panel) | `portfolio.py` | `results/mechanism_decomposition.csv`, `results/reconciled_10k/mechanism_decomposition_10k.csv` |
| Lead-time value analysis — portfolio results (Table 5 lower panel, Tables S3–S4, S10–S12) | `portfolio.py` | `results/portfolio_summary.csv`, `results/portfolio_detail.csv`, `results/reconciled_10k/portfolio_summary_10k.csv`, `results/reconciled_10k/portfolio_detail_10k.csv`, `results/icu/national_icu_portfolio.csv`, `results/icu/national_icu_key_results.json` |
| National-scale analyses, Australia (3.10) | `scenario_australia.py` | `results/national/australia_scenario_config.md`, `results/national/portfolio_summary_aus.csv`, `results/national/portfolio_detail_aus.csv` |
| National-scale analyses, United States (3.10) | `scenario_us_350m.py` | `results/national/us_scenario_config.md`, `results/national/portfolio_summary_us.csv`, `results/national/portfolio_detail_us.csv`, `results/national/mechanism_decomposition_us.csv` |
| National-scale reported thresholds, both countries (3.10, Table 6 Panel A) | `national_scenarios_icu.py` | `results/icu/national_icu_key_results.json`, `results/icu/national_icu_portfolio.csv` |
| Comparator budget, Table 6 Panel B (4.3) | no code; federal award record | Extended Methods S-CB records the award identifier, retrieval date and arithmetic |
| National-scale sensitivity | `sensitivity_icu_n10000.py`, `sensitivity_icu_unresolved.py` | `results/sensitivity_icu/` |
| ICU cost-rate sensitivity (4.6) | `icu_cost_rate_sensitivity.py` | `results/icu_cost_sensitivity/` |

## Validation scripts

| Purpose | Script | Record |
|---|---|---|
| Engine validation, per-test cost override (T1–T5) | `validate_cost_override.py` | `VALIDATION.md` §1 |
| Deterministic reproduction | `primary_screening_icu_check.py` | `VALIDATION.md` §2 |
| PSA stream identity between the headline and convergence runs | `psa_convergence_icu.py` | `VALIDATION.md` §3 |
| Portfolio and lead-time QA assertions | `qa.py` | `results/reconciled_10k/qa_log_10k.txt` |

## Figures

The manuscript carries Figures 1-4. An earlier Figure 5 (WBE favourable-fraction
contours) was replaced by Table 4; its image is retained as Supplementary Figure S2.


| Figure | File | Produced by |
|---|---|---|
| Figure 1. Transmission-chain schematic | `figures/fig_transmission_chain_schematic.png` | drawn, not model-generated |
| Figure 2. Model architecture | `figures/fig1_model_architecture.png` | drawn, not model-generated |
| Figure 3 / Figure S1. Decision surface | `figures/decision_surface.png`, `.svg` | `plot_decision_surface.py` |
| Figure 4. PSA probabilities | `figures/psa_probability_bar.png`, `.svg` | `make_fig4.py` |
| Supplementary Figure S2. WBE decision thresholds | `figures/wbe_decision_threshold.png`, `.svg` | `plot_wbe_decision_threshold_icu.py` |
| Portfolio and mechanism figures (supplementary) | `figures/fig1_portfolio_revised.png`, `figures/fig2_mechanism_revised.png` | `portfolio.py` |

## Not included

The proprietary simulator referred to in the manuscript's Software and reproducibility
section is deliberately excluded, consistent with its status as a commercial product.
No numerical result in the manuscript is drawn from it.

Two scripts used during preparation are also excluded because neither runs against a
clean checkout: one validates the engine against an earlier engine revision that is not
distributed, and one asserts the presence of a superseded-file archive that is not
distributed. Their outcomes are recorded in `VALIDATION.md`.

## Discrepancy found while assembling this repository

`results/wbe_sweep/wbe_idealised_limit.csv` was computed to substantiate Extended
Methods S-WBE. It confirms the section's central claim and contradicts one of its
numbers.

**Confirmed.** At the idealised limit the gate's epidemiological outcomes and health
costs match universal screening to floating-point rounding across all 36 cases (four
pathogens x three prevalence scenarios x three follow-up modalities); the largest
relative difference in any health outcome or health cost is 1.4e-15. The gate's entire
economic effect at this limit is a reduction in testing volume, exactly as the section
argues.

**Contradicted.** Table S19 states that at the idealised limit roughly 1,800-2,200
passengers per day are tested instead of 10,000, an approximate 80% reduction, for
SARS-CoV-2 at base prevalence. The computed value for that cell is a 28.3% reduction:
71.7% of passengers are still tested, because at q = 1.0 most flights carry at least
one detectable infected passenger at that prevalence and are therefore flagged. An
approximately 80% reduction does occur in the grid, but at low arrival prevalence --
Ebola virus disease reaches 87.6% at base prevalence and 93.5% at 0.5x. Across all 36
cases the reduction ranges from 6.0% to 93.5%.

The qualitative conclusion drawn in S-WBE does not depend on the 80% figure, but the
figure itself and the "approx. 1/5" phrasing need correcting before submission.
