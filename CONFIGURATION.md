# Run configuration

Machine-readable equivalent: `results/psa_icu_metadata.json`.

## Baseline

| Item | Value |
|---|---|
| International arrivals per day | 10,000 |
| Downstream population | 10,000,000 |
| Analysis horizon | 365 days |
| Discount rate / start day | `ECON["discount_rate_annual"]`, `ECON["discount_start_day"]` (parameters.py) |
| Base-case VSL | USD 3,500,000 |
| Countermeasure response | delay 21 d, ramp 14 d, reduction strength 0.6 |
| Pathogen scope | SARS-CoV-2, Influenza A/B, Mpox, Norovirus, Ebola, Diphtheria (+ Measles stress test) |
| Strategies | none, Rapid Antigen Test, Laboratory PCR, High-throughput molecular |
| Diagnostic-performance distributions | Beta, moment-matched to Table 1 ranges |


## ICU parameters

| Pathogen | ICU fraction of hospitalised | ICU LOS (days) |
|---|---|---|
| SARS-CoV-2 | 0.15 | 7 |
| Influenza A/B | 0.17 | 5 |
| Mpox | 0.07 | 5 |
| Norovirus | 0.03 | 2 |
| Ebola | 0.35 | 10 |
| **Diphtheria** | **unresolved — none identified; c_icu = 0** | **n/a** |
| Measles (stress test) | none identified; c_icu = 0 | n/a |

Incremental ICU cost USD 3,000 per ICU patient-day, additive to the USD 2,000
ward bed-day rate charged to all hospitalised bed-days. Both are structural
modelling assumptions.

The configuration is defined once, in `icu_parameters.scenario_icu_kwargs`, and
applied by every analysis: the deterministic grid, the prevalence, VSL and
countermeasure sensitivity analyses, the false-positive breakeven analysis, the
PSA, the WBE threshold sweep and the lead-time portfolios. The decision-surface
grid is the one exception and a structural one: its synthetic pathogen has
hosp_rate = 0, so it generates no ICU admissions whatever fraction is supplied;
its pathogen overlay does carry each pathogen's ICU cost per hospitalised case.

## PSA

| Item | Value |
|---|---|
| Iterations | 10,000 per pathogen |
| Base seed | 20260811 |
| Seed convention | `np.random.default_rng(SEED + 0-based index in parameters.PATHOGENS)` |
| Per-pathogen seeds | SARS-CoV-2 20260811, Influenza A/B 20260812, Mpox 20260813, Norovirus 20260814, Ebola 20260815, Diphtheria 20260816 |
| Measles stress-test stream | SEED + 100 = 20260911 |
| Per-test cost distribution | Gamma, moment-matched to `cost_per_test_range` (mean = midpoint, sd = range/4) |
| Per-test cost propagation | each drawn cost is passed to `engine.run_scenario(cost_per_test_override=...)` |

## Reproduce

```
python3 check_consistency.py                           # documents vs saved outputs
python3 run_master.py                                  # deterministic grid           (~3 min)
python3 vsl_sensitivity.py                             # VSL anchors                  (~1 min)
python3 countermeasure_sensitivity.py                  # 4x3x3 sweep + no-CM rows     (~4 min)
python3 decision_surface.py && python3 plot_decision_surface.py   # Figure 3
python3 primary_screening_icu_check.py                 # deterministic ranking check
python3 psa_icu.py                                     # authoritative PSA        (~15 min)
python3 psa_icu.py --no-cost-draws \
        --out-prefix psa_icu_midpointcost_control      # midpoint-cost control    (~15 min)
python3 psa_convergence_icu.py --with-measles          # convergence + decomposition (~12 min)
python3 make_fig4.py                                   # Figure 4 from the saved CSV
```

Every script resolves imports relative to its own directory; no absolute paths.
Dependencies: Python 3.11, numpy, matplotlib (see requirements.txt).
