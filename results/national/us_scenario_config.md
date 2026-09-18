# United States Scenario — Configuration Record

Companion to `australia_scenario_config.md`. Produced by `scenario_us_350m.py`.

## Overrides from the manuscript baseline (reconciliation_10k.py)
  n_total (arrivals/day): 10,000 → 300,000 (30×)
  N (downstream pop):     10,000,000 → 350,000,000 (35×)
  flights/year:           14,600 → 438,000 (300,000 ÷ 250 pax/flight × 365)

## United States input provenance
  N_TOTAL_US = 300,000: international air arrivals per day.
    PROVISIONAL. Supplied as a working figure for the illustrative scaling
    exercise; no published statistical source was adopted for it, and it is not
    derived from a cited arrivals series. It is a round order-of-magnitude
    figure, not an estimate. This is the weakest input in the US scenario and
    differs in kind from the Australian arrivals figure, which is derived from
    a published BITRE series.
  N_DOWNSTREAM_US = 350,000,000: United States national population, rounded.
    No specific vintage or release is cited.

## Unchanged parameters
  avg_pax_per_flight: 250 (locked parameters.py)
  horizon_days:       365
  lead_days:          [2, 5, 10, 14]
  modality:           molecular (high-throughput)
  prevalence:         1.0 × pathogen-specific baseline
  CM parameters:      delay 21 d, ramp 14 d, reduction strength 0.6
  VSL (base_case):    USD 3,500,000  [NOT adjusted for United States income levels;
                      published US agency VSL figures are substantially higher,
                      in the region of USD 10-12 million. Using the unadjusted
                      base-case VSL makes the US thresholds conservative relative
                      to a US-specific valuation.]
  P_event/P_warning:  UNSOURCED SCENARIO ASSUMPTIONS — unchanged from THREAT_CLASSES

## Reported figures and which file backs them
  The thresholds reported in the manuscript (Scenario A USD 154.2 million/year,
  Scenario B USD 282.6 million/year, at d = 5, base probability assumptions,
  excluding the avian-influenza stress test) are the ICU-enabled values in
  `../icu/national_icu_key_results.json` and `../icu/national_icu_portfolio.csv`.

  `portfolio_summary_us.csv` and `portfolio_detail_us.csv` in this folder are the
  PRE-ICU baseline run (USD 152,897,745 and USD 279,968,707 for the same cells).
  They are retained because the ICU key-results file reports the ICU effect as a
  delta against them (+0.86% Scenario A, +0.94% Scenario B). They are not the
  reported figures and should not be cited as such.

## Modelling caveat
  N = 350,000,000 in a single-compartment SIR assumes the entire United States
  population is one homogeneous mixing pool. The model was designed for a
  metropolitan catchment (N = 10,000,000); this configuration is an extrapolation
  well beyond that design. Outputs are order-of-magnitude illustrations of how
  thresholds scale with arrival volume and catchment size, not national forecasts.
  The downstream population scaling is the dominant driver of the difference from
  the baseline.

## Files NOT modified
  engine.py, parameters.py (locked). The script writes only its own outputs.
