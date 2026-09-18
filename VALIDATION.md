# Validation record

Environment: Python 3.11.15, numpy 2.4.4, matplotlib 3.10.9.
File digests for everything distributed here are in `CHECKSUMS.txt`.

## 1. Engine validation: per-test cost propagation

Thirty-six scenario cases were checked across all six pathogens and four screening
modalities, plus the WBE-gated runner:

- **T2** Supplying the per-test cost override at the range midpoint is a no-op: every
  returned field is identical to the default call.
- **T3** Changing only the override moves `screening_cost` and `total_societal_cost` by
  exactly `n_tested x delta_cost`, verified at x0.5, x2.0 and +7.25.
- **T4** No health outcome and no non-programme cost component changes with the override.
- **T5** The `none` modality ignores the override; programme cost stays at zero.

All checks passed. A fifth check (**T1**) compared the current engine field-by-field
against an earlier engine revision that predates the override parameter, and reproduced
it bit-for-bit when the override is omitted. That baseline copy is a development
artefact and is not distributed here, so the script that runs T1–T5 is not included;
T2–T5 are properties of the distributed engine and can be re-derived from it directly.

## 2. Deterministic reproduction

`primary_screening_icu_check.py`, re-run against the distributed engine, reproduced
`results/primary_screening_icu_ranking.csv` byte-identically.

## 3. PSA stream identity

`psa_convergence_icu.py` asserts that its per-iteration cost vectors equal those saved
by `psa_icu.py` in `results/psa_icu_draws_*.npz`. The assertion passed for influenza A/B,
diphtheria, mpox and norovirus. Measles is a stress-test stream with no headline `.npz`
and is excluded from this check.

## 4. Structural checks on the transmission and cost model

Reported in full in Extended Methods S-MV (Table S14) of the supplementary document:
reduction to the no-screening case at zero sensitivity; monotonicity of missed
infections in sensitivity and of false positives in specificity; epidemic decline under
Rt < 1 with no continuing importation; consistent propagation of infectious-period
changes; and non-repetition of mortality and hospitalisation costs within a case's
infectious period. All passed.

Population conservation is not exact under the open-population importation formulation,
by construction. The observed drift over the 365-day horizon is at most 0.004% of N,
with under 0.005% effect on total cost or strategy ranking (Table S15).

## 5. ICU cost-rate linearity

The ICU cost term is linear in the daily rate and feeds back into no other model
quantity. `icu_cost_rate_sensitivity.py` verified this against the engine over 32 cases;
the largest relative deviation from exact rescaling was 1.6e-15, and no health outcome
varied with the rate.

## 6. Portfolio and lead-time QA

Assertion log: `results/reconciled_10k/qa_log_10k.txt` and `results/icu/qa_log.txt`.
