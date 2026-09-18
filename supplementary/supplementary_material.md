<!-- Source of record for supplementary_material.docx. See
     SUPPLEMENTARY_PSA_UPDATES.md for the pending DOCX patch and
     manuscript_audit_record.md for document history. -->

Supplementary Material

Aircraft Wastewater Surveillance for Airport Biosecurity: When Does Early Warning Deliver Value?


# Contents

Table S1. Pathogen parameter values

Table S2. WBE shedding evidence summary

Table S3. Portfolio probability inputs: P_event and P_warning|event by scenario

Table S4. Maximum supportable annual surveillance expenditure (full sensitivity analysis)

Table S5. Incremental societal cost by strategy relative to no screening

Table S6. PSA: probability each strategy is cost-minimising (10,000 iterations)

Figure S1. Decision surface (cost-minimising strategy by Rt and per-case burden)

Figure S2. WBE decision threshold heat maps

Supplementary Methods S1. Surveillance strategy parameters

Supplementary Methods S2. Probabilistic sensitivity analysis: distribution specifications

Supplementary Methods S3. Economic parameters

Supplementary Methods S4. WBE gate: parameter ranges and derivation

Supplementary Methods S5. Lead-time value analysis: QA and reproduce command

Supplementary Methods S6. False-positive breakeven: methods and script

Supplementary Methods S-BL. Baseline portfolio inputs and results (d = 5 days)

Extended Methods S-MV. Model verification and validation checks

Extended Methods S-CM. Countermeasure response function: mathematical definition

Extended Methods S-NPI. NPI timing and magnitude: contextualising literature review

Extended Methods S-FP. False-positive follow-up: full breakeven analysis by pathogen

Extended Methods S-PSA. PSA convergence verification: N = 1,000 / 5,000 / 10,000

Extended Methods S-Measles. Measles stress test: full results sweep (60–99% suppression)

Extended Methods S-WBE. WBE idealised limiting case: mechanism verification

Extended Methods S-90d. 90-day vs. 365-day analysis horizon comparison


# Table S1. Pathogen parameter values

Primary comparison pathogens (6) and model-boundary stress test (Measles). Ranges are those applied in the model; deterministic analyses use each range's midpoint and the probabilistic sensitivity analysis samples across it (Supplementary Methods S2). The values are those carried in the model code supplied as Supplementary Material.


| Pathogen | Rt (epidemic phase) | Infect. period (d) | CFR (%) | Hosp. rate | Hosp. dur. (d) | Symp. frac. | Detect. at arr. | WBE |
|---|---|---|---|---|---|---|---|---|
| SARS-CoV-2 | 1.2–2.0 | 4–7 | 0.1–1.4% | 5–10% | 7–10 | 60–70% | 45–55% | Yes |
| Influenza A/B | 1.1–1.4 | 3–5 | 0.01–0.1% | 1–3% | 4–6 | 50–70% | 40–55% | No |
| Mpox | 1.2–1.8 | 7–14 | Cl.I: 1–10%; Cl.IIb <1% | 5–20% | 7–21 | ~90% | 60–80% | Yes |
| Norovirus | 1.5–2.0 | 1–3 | <0.001% | <1% | 1–3 | 50–70% | 30–45% | Yes |
| Ebola | 1.2–2.0 | 7–14 | 25–90% (mean ~50%) | 80–100% | 7–14 | ~90% | 60–75% | Yes |
| Diphtheria | 1.5–4.0 | 14–28 | 5–10% (untreated); <1% (treated) | 20–40% | 5–10 | 30–50% | 25–40% | No |
| STRESS TEST |  |  |  |  |  |  |  |  |
| Measles | 2–8 | 8–10 | 0.1–0.2% (OECD); 1–5% (LIC) | 10–20% | 5–7 | ~95% | 45–90% | No |

Rt = effective reproduction number in modelled epidemic scenario. CFR = case-fatality (or infection-fatality) rate. Detectable at arrival = combined probability of viraemic detection window at border crossing. WBE = aircraft wastewater-based epidemiology; Yes/No indicates whether WBE is included as a modelled screening modality for this pathogen. Strength of biological evidence for WBE detection is rated separately in Table S2 (++ strong; + moderate; ~ limited; x none).


# Table S2. WBE shedding evidence summary


| Pathogen | Rating | Basis | Modelling status |
|---|---|---|---|
| SARS-CoV-2 | Strong (++) | Extensive peer-reviewed literature; mass airport deployment; aircraft lavatory studies validated | Included in WBE gate analysis |
| Norovirus | Strong (++) | Long-established shedding; highest faecal viral load of any modelled pathogen; aircraft data available | Included in WBE gate analysis |
| Mpox | Moderate (+) | DNA detected in wastewater in multiple countries; no aircraft lavatory-specific validation | Included with caveat: aircraft-specific data absent |
| Ebola | Moderate (+) | RNA in bodily fluids; theoretically applicable; no aircraft lavatory data | Included with caveat: no lavatory validation; theoretical basis only |
| Influenza A/B | Limited (~) | RNA detected in community wastewater across multiple countries and seasons; operationally monitored by CDC NWSS; faecal shedding lower and less consistent than SARS-CoV-2 or norovirus; no aircraft lavatory-specific detection validation | Excluded from WBE gate; no aircraft lavatory-specific validation; community WBE evidence does not supply aircraft-validated detection probability estimates |
| Diphtheria | None (x) | Respiratory/contact transmission; no faecal shedding route | Excluded; WBE not applicable |
| Measles | Limited (~) | RNA detectable in community wastewater; no aircraft data | Excluded from flight-level WBE gate |

Ratings: ++ strong; + moderate; ~ limited; x none.


# Table S3. Portfolio probability inputs: P_event and P_warning|event by threat class, scenario, and probability assumption

All P_event and P_warning|event values are declared scenario assumptions, not empirically calibrated estimates. Three probability assumptions (Low, Base, High) are tabulated for each threat class. The avian-influenza-like class is reported separately as a stress test and is excluded from the primary portfolio headline figures. Source: results/portfolio_detail.csv.

Table S3, Panel A. Primary portfolio threat classes (avian influenza excluded)


| Threat class | Representative pathogen | Prob. assumption | P_event | P_warning\|event | P_combined |
|---|---|---|---|---|---|
| SARS-like respiratory virus | SARS-CoV-2 | Low | 0.005 | 0.05 | 0.00025 |
|  |  | Base | 0.02 | 0.2 | 0.0040 |
|  |  | High | 0.05 | 0.4 | 0.0200 |
| Mpox-like orthopoxvirus | Mpox | Low | 0.005 | 0.05 | 0.00025 |
|  |  | Base | 0.02 | 0.2 | 0.0040 |
|  |  | High | 0.05 | 0.4 | 0.0200 |
| High-burden enteric outbreak | Norovirus | Low | 0.02 | 0.05 | 0.0010 |
|  |  | Base | 0.1 | 0.2 | 0.0200 |
|  |  | High | 0.25 | 0.4 | 0.1000 |
| Ebola-like viral haemorrhagic fever | Ebola | Low | 0.001 | 0.05 | 0.00005 |
|  |  | Base | 0.005 | 0.2 | 0.0010 |
|  |  | High | 0.02 | 0.4 | 0.0080 |

Table S3, Panel B. Avian-influenza-like stress-test class (reported separately)


| Threat class | CFR range | Prob. assumption | P_event | P_warning\|event | Note |
|---|---|---|---|---|---|
| Avian-influenza-like (H5N1-type) | 0.5–5.0% | Base | 0.01 | 0.3 | Stress test only; not in primary portfolio headline |

P_combined = P_event × P_warning|event. All values are scenario assumptions for decision exploration; they are not derived from empirical outbreak-rate data and should not be read as probability estimates.


# Table S4. Maximum supportable annual surveillance expenditure (full sensitivity analysis)

Portfolio EV = P_event × P_warning|event × max(0, B(d)) summed across threat classes. Reported as maximum cost-neutral annual expenditure at each (d, probability assumption) combination. Values in USD millions/year. Per-flight values use 14,600 arriving flights per year (10,000 arrivals/day ÷ 250 passengers/flight × 365 days). All monetary values conditional on stated scenario probability assumptions.

Table S4, Panel A. Scenario A — advance screening only; excluding avian-influenza stress test


| d (days) | Low prob. ($/yr) | Base prob. ($/yr) | High prob. ($/yr) | Base per-flight ($/flight) | Base deaths averted/yr |
|---|---|---|---|---|---|
| 2 | $0.146M | $2.57M | $13.9M | $176 | 0.581 |
| 5 | $0.284M | $4.92M | $27M | $337 | 1.2 |
| 10 | $0.435M | $7.47M | $41.5M | $512 | 1.9 |
| 14 | $0.515M | $8.81M | $49.3M | $604 | 2.27 |

Table S4, Panel B. Scenario B — advance screening plus earlier countermeasures; excluding avian-influenza stress test


| d (days) | Low prob. ($/yr) | Base prob. ($/yr) | High prob. ($/yr) | Base per-flight ($/flight) | Base deaths averted/yr |
|---|---|---|---|---|---|
| 2 | $0.213M | $3.79M | $20.3M | $260 | 0.817 |
| 5 | $0.514M | $8.92M | $48.2M | $611 | 2.11 |
| 10 | $1.16M | $19.7M | $107M | $1,351 | 5.04 |
| 14 | $1.92M | $32.1M | $174M | $2,201 | 8.45 |

All cells are read from portfolio_summary.csv: n = 10,000 arrivals/day, 365-day horizon, VSL USD 3,500,000, high-throughput molecular response modality, c_icu evaluated, avian-influenza stress class excluded. The underlying event-level benefits are in scenario_a_grid.csv and scenario_b_grid.csv. B(d) values are event-level; portfolio EV applies probability weights. Values are rounded to 3 significant figures. The d = 5, base-probability row is the Section 3.10 headline (Scenario A USD 4.92M, Scenario B USD 8.92M).


# Table S5. Incremental societal cost by strategy relative to no screening

At baseline (1.0×) prevalence, 365-day horizon. Negative values indicate cost savings relative to no systematic screening. Values in USD millions.


| Pathogen | No screening (base) | RAT vs. no screening | PCR vs. no screening | Mol. vs. no screening |
|---|---|---|---|---|
| SARS-CoV-2 | $2,758.3 M | −$1,811.1 M | −$2,314.4 M | −$2,602.8 M (cost-min.) |
| Influenza A/B | $318.0 M | −$169.1 M | +$52.0 M | −$236.3 M (cost-min.) |
| Mpox | $3,988.4 M | −$2,646.1 M | −$3,508.2 M | −$3,796.5 M (cost-min.) |
| Norovirus | $190.8 M | −$10.8 M | +$200.1 M | −$88.2 M (cost-min.) |
| Ebola | $11,333.5 M | −$7,604.1 M | −$10,633.0 M | −$10,921.3 M (cost-min.) |
| Diphtheria | $608.7 M | −$365.6 M | −$230.0 M | −$518.3 M (cost-min.) |

Incremental costs are computed relative to no-screening total societal cost per pathogen. All cells are read from master_deterministic.csv, the deterministic grid reported in Sections 3.1–3.3, filtered to prevalence scenario 1×, non-WBE-gated, non-route-targeted, non-stress-test rows, with c_icu evaluated as in every other analysis (§2.6). Diphtheria has no identified ICU inputs, so its row carries c_icu = 0. The laboratory-PCR-minus-molecular difference implied by these columns is USD 288,333,328 for every pathogen (§3.3); the ICU term is identical between those two strategies, which are epidemiologically identical by construction, so it does not enter that difference.


# Table S6. PSA: probability each strategy is cost-minimising (10,000 iterations)

10,000 Monte Carlo iterations per pathogen, fixed random seed 20260811 offset by pathogen index, at the 365-day horizon, from psa_icu.py (psa_icu_strategy_probabilities.csv), with c_icu evaluated and per-test cost sampled per iteration. Diphtheria has no identified ICU admission fraction or length of stay, so c_icu = 0 for it (§2.6).


| Pathogen | No screening (%) | RAT (%) | Lab. PCR (%) | Mol. testing (%) |
|---|---|---|---|---|
| SARS-CoV-2 | 0.0% | 0.0% | 2.8% | 97.2% |
| Influenza A/B | 0.4% | 6.3% | 0.0% | 93.3% |
| Mpox | 0.0% | 0.1% | 2.7% | 97.2% |
| Norovirus | 22.7% | 5.6% | 0.0% | 71.7% |
| Ebola | 0.0% | 0.0% | 13.2% | 86.8% |
| Diphtheria | 3.1% | 8.4% | 7.2% | 81.2% |

All four strategy probabilities are given and sum to 100% per row (rounding aside); the full breakdown, including mean and median cost and 95% intervals per strategy, is in psa_icu_summary.csv. Norovirus is the lowest-confidence primary pathogen at the 365-day horizon (71.7%).


# Figure S1. Decision surface (cost-minimising strategy by Rt and per-case burden)

Figure S1. Cost-minimising surveillance strategy as a function of effective reproduction number (Rt, horizontal axis, 0.5–3.2) and per-case economic burden (USD, vertical axis, logarithmic scale), at the 365-day analysis horizon and baseline prevalence. Shaded regions indicate which of the four primary surveillance strategies (no systematic screening, rapid antigen testing, laboratory PCR, high-throughput molecular testing) minimises total expected societal cost at each combination of transmissibility and per-case burden. The surface uses a synthetic pathogen with infectious period fixed at 8 days (a reference value within the primary pathogens' mid-range estimates of 2–21 days); per-case burden B is imposed as an equivalent case-fatality rate (CFR_equiv = min(100%, B / USD 3,500,000), with hospitalisation and productivity costs set to zero and all infections treated as symptomatic). The burden function reaches its ceiling at B = USD 3,500,000; above this value all grid cells resolve identically in the cost function. All six primary pathogen overlay coordinates fall within the uncapped region (maximum USD 1,831,875 for Ebola virus disease). The six primary pathogens are overlaid at their base-case (Rt, USD-per-case) coordinates computed from each pathogen's own parameter set; overlay coordinates are not constrained by the synthetic-pathogen surface simplification, and background shading at each overlay point reflects the surface's synthetic-pathogen calculation, not a dedicated per-pathogen calculation. This figure is reproduced from manuscript Figure 3; methodological detail is in Section 2.9 and Supplementary §S-BL.


# Figure S2. WBE decision threshold heat maps

Figure S2. Fraction of 144 explored parameter combinations (4 pathogens × 3 prevalence scenarios × 4 wastewater false-positive-rate scenarios × 3 follow-up-coverage scenarios) for which WBE-gated screening was less expensive than universal screening using the same follow-up modality, as a function of aircraft-level WBE detection probability (q, vertical axis) and wastewater sampling cost per aircraft (horizontal axis, log scale; one pooled wastewater sample per arriving aircraft assumed), at the 365-day analysis horizon. Panels share an identical 0–45% colour scale. Contour lines mark 1%, 5%, 10%, and 20% of combinations favouring WBE-gating where they exist. Pathogens included: SARS-CoV-2, mpox, norovirus, Ebola virus disease; influenza A/B and measles excluded (no aircraft lavatory-specific validation, Table S2); diphtheria excluded (no faecal shedding route). Axes and shading reflect the full explored ranges of q and sampling cost; none of the parameter values explored is an empirically validated estimate of real-world aircraft-WBE performance (Section 2.7.1). This figure is the heat-map form of the WBE threshold results summarised in manuscript Table 4.


# Supplementary Methods S1. Surveillance strategy parameters

The four primary surveillance strategies compared in the main analysis were parameterised as follows.


Table S7. Passenger-screening strategy parameters applied in the main analysis.

| Strategy | Sensitivity range | Specificity range | Cost per test (USD) | Throughput note |
|---|---|---|---|---|
| No systematic screening | 0% | 100% | $0 | Reference |
| Rapid antigen testing (RAT) | 45–90% | 99.0–99.8% | $5–$20 | High throughput; limited lab infrastructure |
| Laboratory PCR | 95–99% | 97.3–99.5% | $50–$150 | 50–150 passengers/hour per unit; multiple units needed |
| High-throughput molecular (Sentinel RT-LAMP) | 95–99% | 97.3–99.5% | $10–$30 | Manufacturer-reported; see §2.7 |

PCR and molecular testing share identical sensitivity and specificity ranges (symmetric-performance assumption, §2.7). Specificity (97.3–99.5%) is drawn from Dinnes et al. 2020 (Cochrane Database Syst Rev. 2020;8:CD013705), which pooled rapid point-of-care assay specificity at 98.9% (95% CI 97.3–99.5%); the 2020 review did not separately pool centralised laboratory RT-PCR, and applying this range to laboratory PCR and high-throughput molecular testing is a structural symmetry for this comparative analysis, not a claim of identical empirical specificity across modalities. RAT specificity (99.0–99.8%) is from Dinnes et al. 2021 (Cochrane Database Syst Rev. 2021;3:CD013705.pub2), which reported an overall summary specificity of 99.6% (95% CI 99.0–99.8%); stratified estimates by symptom status are in Supplementary Table S1. Cost ranges used in probabilistic sensitivity analysis; deterministic analyses use arithmetic midpoints. RAT sensitivity bounds (45–90%, midpoint 67.5%) are author-selected scenario bounds rather than a pooled clinical estimate. For SARS-CoV-2 the relevant diagnostic evidence is: Dinnes et al. 2021 (Cochrane), asymptomatic sensitivity 58.1% (95% CI 40.2–74.1%) and symptomatic sensitivity 72.0% (95% CI 63.7–79.0%) against an RT-PCR reference standard; Prince-Guerra et al. 2021 (community walk-in, predominantly asymptomatic), 35.8% (95% CI 27.3–44.9%) against RT-PCR; and Layer et al. 2022 (returning travellers, entry-screening context), 59% against RT-PCR. The lower bound (45%) falls within the range of community-asymptomatic PCR-referenced performance (35.8–58.1%); the upper bound (90%) and midpoint exceed available asymptomatic and traveller-population estimates against RT-PCR and correspond approximately to culture-referenced performance in certain subpopulations (Prince-Guerra culture-positive asymptomatic 78.6%, 95% CI 59.1–91.7%; Layer culture-positive travellers 89.7%). Which reference standard is appropriate depends on the population definition used for the importation fraction φ, discussed below. Applying these bounds across pathogens is a scenario assumption not separately established for each modelled pathogen. Route-risk group specification (§2.2 of the main manuscript): arriving passengers are divided into three route-risk groups with shares f_k = 0.60 (low), 0.30 (moderate), 0.10 (high) and prevalence multipliers m_k = 0.50, 1.00, 2.00 applied to the reference arrival prevalence p0, giving ∑_k f_k m_k = 0.80. These shares and multipliers are illustrative assumptions representing a plausible concentration of importation risk across routes; no empirical route-composition estimate is claimed for them, and they are not varied in any reported analysis. They are a fixed feature of the model configuration and are distinct from the 0.5x/1.0x/2.0x prevalence scenarios (§2.10), which scale p0 for all passengers simultaneously and are the sensitivity axis reported throughout Section 3. In the passenger-screening analyses the groups enter only through the weighted sum 0.80, which multiplies Λ; they are resolved individually only in the aircraft wastewater gate (S4), where each group's Poisson rate enters a nonlinear detection probability and the weighted sum is therefore not a substitute for the group structure. Denominator compatibility between φ and Se: the importation equation (§2.2) multiplies φ, the fraction of infected arrivals both detectable and currently infectious at the border, by (1 − Se). In the intended construction of this term, φ defines the pool of infected arrivals eligible for detection and Se quantifies detection within that pool. Their denominators are not established as empirically equivalent. The rapid-antigen sensitivity estimates are drawn from study populations of RT-PCR-confirmed cases presenting for clinical testing, whereas φ selects on detectability and infectiousness at the border, and detectable_at_arrival_pct_range carries no per-pathogen source in the parameter table. Whether ‘detectable’ denotes PCR positivity, a shedding-quantity threshold, or an infectious-window criterion is not specified, so the direction and magnitude of any mismatch between the two denominators cannot be determined. Because Λ scales linearly in φ and in (1 − Se), a mismatch that is not common to all strategies could affect relative as well as absolute costs, and the WBE-gate threshold conditions (§2.7.1) depend directly on the scale of Λ. This is an unresolved calibration assumption.


# Supplementary Methods S2. Probabilistic sensitivity analysis: distribution specifications

Parameters were drawn from distributions moment-matched to their cited range treated as an approximate 95% probability interval, applying the following distribution families:

Bounded proportions (case-fatality parameter, hospitalisation rate, symptomatic fraction, fraction detectable at arrival, test sensitivity, test specificity): Beta distributions, with α and β parameters derived from method-of-moments matching to the stated range as a 95% CI.

Positive, multiplicatively-uncertain parameters (effective reproduction number, infectious period): log-normal distributions, with μ and σ² on the log scale derived from the stated range as a 95% CI.

Positive cost-type parameters (per-test cost, VSL): Gamma distributions, with shape and rate parameters derived from the stated range. Each iteration's sampled per-test cost is applied to that iteration's programme-cost term for the strategy concerned, so programme cost varies across iterations. It enters no epidemiological term, so infections, hospitalisations and deaths are invariant to it (validate_cost_override.py).

Sentinel RT-LAMP and laboratory PCR sensitivity and specificity were sampled from identical distributions in every iteration — not independently. Fixed random seed: 20260811, offset by pathogen index for distinct but reproducible per-pathogen streams (SARS-CoV-2: seed 20260811, influenza A/B: 20260812, mpox: 20260813, norovirus: 20260814, Ebola: 20260815, diphtheria: 20260816).

Test specificity is sampled and propagated in PSA as an operational-output uncertainty dimension; consistent with §2.6.1, it does not enter the total-cost calculation for any strategy in any iteration. Specificity is reported as an output distribution per pathogen and strategy but has no causal effect on total societal cost under the current model.


# Supplementary Methods S3. Economic parameters

All monetary values in USD. Economic parameters are pre-specified structural assumptions applied consistently across all pathogens and strategies; they are not jurisdiction-specific estimates. Incremental ICU cost rate. The rate is USD 3,000 per ICU day above the ward bed-day rate and is applied only to ICU days, so it is an increment on top of c_bed and not a total ICU day cost; total-cost figures from the literature are not directly comparable to it. Dasta et al. (Crit Care Med 2005;33:1266–71; 51,009 ICU admissions, 253 US hospitals) report mean daily costs from the third ICU day of USD 3,184 (not mechanically ventilated) and USD 3,968 (mechanically ventilated) against a mean non-ICU daily cost of USD 2,132 in the same cohort, all in 2002 US dollars — implied increments of USD 1,052 and USD 1,836 per day. First- and second-day ICU costs are higher (USD 6,667 and USD 3,496 non-ventilated; USD 10,794 and USD 4,796 ventilated), so a stay-averaged increment over a 5–10 day admission is larger than the third-day figure: approximately USD 1,594 per day non-ventilated and USD 2,929 per day ventilated over a seven-day stay. Inflating by the US medical care consumer price index (CPIMEDSL, 1982–84 = 100; 2002 annual average 285.6 to 2025 annual average 580.1, a factor of 2.03) gives approximately USD 2,100 to USD 6,000 per ICU day in 2025 dollars across the non-ventilated third-day and ventilated stay-averaged cases. USD 3,000 per ICU day is taken as the central estimate and USD 2,000–6,000 as the plausible range. For context, and not used here, European estimates are reported as total ICU day costs: EUR 1,425 per ICU day (France, 2008 euros) and EUR 1,338 (Germany, 2011 euros), as cited in Kaier et al., Epidemiol Infect 2019;147:e314; those figures were not retrieved in their original publications. Two limitations apply. The admission fractions and lengths of stay to which this rate is applied are separately sourced and, for several pathogens, unresolved (§2.6); the rate's plausibility does not transfer to them. And the ward bed-day rate c_bed, the wage rate and the value of statistical life carry no stated price year, so the ICU rate is the only economic parameter here anchored to a specific year. Sensitivity over the range, computed by rescaling the locked deterministic and lead-time outputs (the ICU term enters cost additively, is linear in the rate, and does not feed back into transmission; verified against the engine to a relative error below 1e-12 with health outcomes invariant). Across the 72 pathogen × prevalence-scenario × strategy combinations, the ICU component accounts for 0.0–1.4% of total societal cost at USD 2,000 per ICU day, 0.0–2.1% at USD 3,000 and 0.0–4.1% at USD 6,000. The cost-minimising strategy is unchanged in all eighteen pathogen × prevalence-scenario cells at every rate in the range, and no rank ordering among the four strategies changes. The false-positive breakeven thresholds (§S-FP), recomputed with the same false-positive counts, move by −1.4% at USD 2,000 and by at most +4.3% at USD 6,000 across the 36 cells with a finite threshold. For the lead-time analysis at d = 5 days, under base-case utilisation inputs the ICU component is at most 0.5% of B(d) for every threat class at the central rate except norovirus (2.2%); combining the top of the cost range with the high ICU-utilisation variants of the unresolved inputs raises this to at most 2.5% except for norovirus (10.0%). Bounding each unresolved utilisation input across its plausible range at the central rate gives 0.03–1.26% for Ebola virus disease, 0.37–5.25% for norovirus and 0.17–0.71% for diphtheria, whose fraction is otherwise unspecified (§3.10). The corresponding portfolio thresholds carry an ICU component of approximately 0.6–0.9% at the central rate, and therefore approximately 0.4–0.6% at USD 2,000 and 1.2–1.8% at USD 6,000. Underlying values: results/icu_cost_sensitivity/ for the rate sweep, the false-positive breakeven recomputation and the lead-time bounds; the strategy-level shares quoted above are obtained by rescaling results/master_deterministic.csv across all four strategies.


Table S8. Economic parameters, their base-case values and the ranges over which they were tested.

| Parameter | Base-case value | Sensitivity range | Note |
|---|---|---|---|
| Value of statistical life (VSL) | $3,500,000 | $300K / $1M / $11.6M | Structural base-case assumption; four-anchor sensitivity (§3.5) |
| Inpatient bed cost (c_bed) | $2,000/day | Fixed | Pre-specified; not jurisdiction-specific |
| Mean daily wage (w_avg) | $250/day | Fixed | Pre-specified; not jurisdiction-specific |
| Indirect productivity multiplier (ε) | 0.70 | Fixed | 70% additional burden above direct wage loss |
| Discount rate | 3% p.a. | Fixed | Applied to costs beyond day 30 within horizon |
| Discount start day | Day 30 | Fixed | Convention for within-horizon discounting; see §2.6 |
| Analysis horizon | 365 days | 90 days (comparison) | See §4.7 for interpretation |
| Arrivals per day (N_total) | 10,000 | Fixed | Manuscript base configuration §S2.1; parameters.py N_TOTAL_ARRIVALS_PER_DAY (line 171) |
| Passengers per flight | 250 | Fixed | Used for per-flight portfolio normalization |
| Catchment population (N) | 10,000,000 | Fixed | Downstream domestic population |
| Incremental ICU cost (above ward) | $3,000/ICU day | $2,000–$6,000/ICU day | Reference-informed central estimate, 2025 USD; incremental, not a total ICU day cost |
| ICU utilisation, SARS-CoV-2 | 0.15 of hospitalisations; 7 ICU days | — | Fraction adjusted downward from a 17% combined high-dependency-or-intensive-care proportion (3,001/18,183; Docherty et al., BMJ 2020), which conflates two levels of care. The length of stay is an assumption: the cited source reports duration of hospital stay, not ICU stay |
| ICU utilisation, influenza A/B | 0.17 of hospitalisations; 5 ICU days | — | Fraction is the rounding of a 16.7% ICU admission proportion in the FluSurv-NET imputed analytic sample (Sumner et al., Lancet Microbe 2023). The length of stay is an assumption; no source reporting an ICU length of stay was identified |
| ICU utilisation, mpox | 0.07 of hospitalisations; 5 ICU days | — | Fraction attributed to Thornhill et al., NEJM 2022 (5 of 70 hospitalised); the full text was not retrievable, so the figure is unverified. The length of stay is an assumption |
| ICU utilisation, norovirus | 0.03 of hospitalisations; 2 ICU days | 0.01–0.05; 1–3 days | Assumptions; no primary source identified for either input |
| ICU utilisation, Ebola | 0.35 of hospitalisations; 10 ICU days | 0.05–0.80; 5–12 days | Assumptions; no primary source identified for either input, and ICU use is strongly jurisdiction-dependent |
| ICU utilisation, diphtheria and measles | Not specified; c_icu = 0 | — | No ICU utilisation parameters are specified and no incremental ICU cost is applied (§2.6) |
| ICU utilisation, avian-influenza stress scenario | Inherits influenza A/B (0.17; 5 ICU days) | — | Assumed proxy. WHO 2024 H5N1 situation reports are cited as indicating ICU fractions above 80% in confirmed hospitalised cases; that figure is unverified and is not used |

The incremental ICU cost component is calculated using the pathogen-specific admission fractions and lengths of stay specified in §2.6. No incremental ICU cost is included for diphtheria or measles; their ICU parameters remain unresolved.


# Supplementary Methods S4. WBE gate: parameter ranges and derivation

The WBE gate is computed analytically as a closed-form expectation over the Poisson distribution of infected passengers per flight. No empirical aircraft-specific estimate exists for any of the four exploratory parameters; they are treated as swept bounding ranges rather than calibrated values.


Table S9. WBE gate parameters, symbols and the ranges swept in the threshold analysis.

| Parameter | Symbol | Range swept | Scenarios |
|---|---|---|---|
| Aircraft-level WBE detection probability | q | 0.05–0.95 (step 0.05) | Continuous sweep |
| Wastewater false-positive rate | wbe_fp_rate | 0.005, 0.02, 0.05, 0.10 | 4 scenarios |
| Sampling cost per aircraft | wbe_cost_per_sample | $10–$150 | Continuous sweep |
| Follow-up coverage | follow_up_coverage | 0.50, 0.75, 1.00 | 3 scenarios |

Gate closed-form solution: P(flag | n_infected, wbe_fp_rate, q) = 1 − (1 − wbe_fp_rate) · exp(−λ_k · q), where λ_k = avg_pax_per_flight × p0 × m_k × φ is the Poisson rate for route-risk group k. This formulation was independently validated against direct numerical enumeration of the Poisson distribution.

For each (q, wbe_cost_per_sample) point, the fraction of 144 combinations (4 pathogens × 3 prevalence scenarios × 4 false-positive-rate scenarios × 3 follow-up-coverage scenarios) for which WBE-gated testing was less expensive than universal screening was computed. Pathogens included: SARS-CoV-2, mpox, norovirus, Ebola. Influenza A/B and measles excluded (no aircraft lavatory-specific validation, Table S2); diphtheria excluded (no faecal shedding route).


# Supplementary Methods S5. Lead-time value analysis: QA and reproduce command

The lead-time analysis uses the same SIR model and cost function as the primary passenger-screening comparison (§§2.4, 2.6), applied to a dual-arm comparison. Full QA checks are documented in reconciliation_10k.py and qa_log.txt.

QA Check 1: B(0) = 0

Both arms initialised identically (S(0) = N − Λ₀, I(0) = Λ₀ × 1 day, R(0) = 0, Se = 0 in both, no lead-time offset). At d = 0, both arms are identical; B(0) = 0 for all pathogens and modalities (verified in reconciliation_10k.py QA Check 1 to tolerance 0.001%).

QA Check 2: B(d) monotonically non-decreasing

Lead-time benefit was verified to be non-negative and non-decreasing in d for all evaluated (pathogen, modality) combinations under base-case assumptions.

QA Check 3: Scenario A ≤ Scenario B

B_A(d) ≤ B_B(d) for all d > 0 and all (pathogen, modality) combinations, since Scenario B adds the countermeasure-timing pathway without removing the screening-timing pathway.

Reproduce command:

python runners.py --mode lead_time --n 10000 --seed 20260811 --output results/reconciled_10k/

Full QA outputs are in qa_log.txt and reconciliation_log.txt.


# Supplementary Methods S6. False-positive breakeven: methods and script

The false-positive breakeven analysis is a post-hoc derivation from the deterministic strategy costs and false-positive counts, computed with c_icu evaluated (§2.6). No modification is made to the epidemiological model, the cost function or any parameter.

Method: for each pathogen × prevalence-scenario combination, we calculated the uniform incremental cost per false positive that would need to be added to every strategy's reported false-positive count for the cost-minimising strategy to change. Formally, for strategies i and j where strategy i is cost-minimising:

threshold_ij = (C_j - C_i) / (FP_j - FP_i)

where C_k is the reported total cost for strategy k and FP_k is the reported false-positive count. The minimum threshold across all competing strategies j is the reported breakeven value for that (pathogen, prevalence scenario) combination.

Script: false_positive_breakeven.py. Outputs: results/false_positive_breakeven.csv.

Key results: across the 18 (pathogen × prevalence-scenario) combinations at 365 days, the binding breakeven cost per false positive ranged from ~USD 564 (influenza A/B, 0.5× prevalence) to ~USD 182,844 (Ebola, 2× prevalence). Because laboratory PCR and high-throughput molecular testing share identical specificity (symmetric-performance assumption), any false-positive cost added uniformly to both leaves their cost difference unchanged; this invariance is noted in §3.3.1.


# Supplementary Methods S-BL. Baseline portfolio inputs and results (d = 5 days)

This section records the full baseline configuration and per-threat-class arithmetic underlying the portfolio expenditure thresholds reported in Table 5 of the main manuscript. Values are drawn directly from the ICU-enabled analysis outputs (results/portfolio_detail.csv, results/portfolio_summary.csv, results/mechanism_decomposition.csv; portfolio.py). This is a fresh-run reproduction using the same implementation; it does not independently validate the implementation or the empirical assumptions (see Supplementary Methods S5 for QA record).


## S-BL.1. Configuration


Table S10. Baseline portfolio configuration for the lead-time value analysis (d = 5 days).

| Parameter | Value | Source / note |
|---|---|---|
| Daily airport arrivals (n_total) | 10,000 passengers/day | parameters.py N_TOTAL_ARRIVALS_PER_DAY (line 171); manuscript §2.2 |
| Domestic catchment population (SIR N) | 10,000,000 | parameters.py DOWNSTREAM_POPULATION (line 172); manuscript §2.4, §S1.2 ('generic large metropolitan catchment') |
| Analysis horizon | 365 days | Manuscript base case §2.4 |
| Lead time evaluated here | 5 days | Base-case lead time (d ∈ {2, 5, 10, 14} in full sweep) |
| Screening modality | High-throughput molecular (Sentinel RT-LAMP) | Response modality in portfolio; same as primary cost-minimising strategy |
| Initial conditions (both arms) | S(0) = N − Λ₀ × 1 day; I(0) = Λ₀ × 1 day; R(0) = 0; Se = 0 | Modelling assumption; Λ₀ = importation rate at Se = 0 (see §S-BL.1 note below) |
| Scenario A countermeasure schedule | CM applied at day 21 in both arms (CM timing fixed) | Benefit = delay in detection only; CM timing identical in both arms |
| Scenario B countermeasure schedule | Immediate arm: CM at day 21; Delayed arm: CM at day 21 + d | Benefit = earlier detection + earlier CM; CM timing shifts by d in delayed arm |
| SARS-CoV-2 reference prevalence (p0) | 1.5% | parameters.py line 37; provenance unresolved (see §S-BL.5) |
| Probability inputs (P_event, P_warning) | See Table S3 and §S-BL.2 | Scenario assumptions; see §S-BL.5 |
| VSL | USD 3,500,000 (base case) | ECON['VSL_base_case'] in parameters.py |
| Flights per year | 14,600 | 10,000 ÷ 250 passengers/flight × 365 days |

Initial-condition note: Λ₀ for SARS-CoV-2 = n_total × 0.80 × p0 × φ × (1 − Se) = 10,000 × 0.80 × 0.015 × 0.50 × (1 − Se) = 60 × (1 − Se) importations/day. At Se = 0 (applied in both arms): Λ₀ = 60.0 importations/day. The factor 0.80 is the fleet-weighted average route-risk multiplier (groups low/moderate/high with shares 0.60/0.30/0.10 and multipliers 0.50/1.00/2.00; S1). φ = 0.50 is the mid-point of the detectable-at-arrival range (45–55%) from parameters.py. The 1.5% is the reference prevalence before route-risk weighting; the individual route-risk groups carry rates of 0.015 × 0.5 = 0.75% (low), 0.015 × 1.0 = 1.5% (moderate) and 0.015 × 2.0 = 3.0% (high) — the 1.5% is not the average across groups, it is the reference from which the group-specific rates are derived.


## S-BL.2. Per-threat-class inputs and expected-value arithmetic

Portfolio EV = Σc P_event,c × P_warning|event,c × max(0, B_d,c). B_d is the conditional event-level benefit computed by the SIR simulation (not derived from existing CSVs). The zero floor is applied per threat class before summation; no negative contribution enters the portfolio total.

Table S11, Panel A. Scenario A (screening-only benefit: earlier detection, CM timing fixed):


| Threat class | Rep. pathogen | P_event | P_warn\|ev | B_d ($M) | EV = P×P×B ($M) |
|---|---|---|---|---|---|
| SARS-like respiratory virus | SARS-CoV-2 | 0.0200 | 0.2000 | 514.964 | 2.059855 |
| Mpox-like orthopoxvirus | Mpox | 0.0200 | 0.2000 | 243.438 | 0.973750 |
| High-burden enteric outbreak | Norovirus | 0.1000 | 0.2000 | 54.140 | 1.082797 |
| Ebola-like viral haemorrhagic fever | Ebola | 0.0050 | 0.2000 | 806.833 | 0.806833 |
| Portfolio total (Scenario A) |  |  |  |  | 4.923236 |

Displayed B_d values are rounded to 3 d.p.; EV contributions and the portfolio total are computed from unrounded values in portfolio_detail.csv. Portfolio total $4.923236M is shown as USD 4.92 million in Table 5 (3 s.f.). Avian-influenza-like class excluded; reported separately at USD 15.4M (Scenario A, d=5, incl. avian stress test).

Table S11, Panel B. Scenario B (combined benefit: earlier detection plus earlier countermeasures):


| Threat class | Rep. pathogen | P_event | P_warn\|ev | B_d ($M) | EV = P×P×B ($M) |
|---|---|---|---|---|---|
| SARS-like respiratory virus | SARS-CoV-2 | 0.0200 | 0.2000 | 1024.229 | 4.096917 |
| Mpox-like orthopoxvirus | Mpox | 0.0200 | 0.2000 | 345.432 | 1.381730 |
| High-burden enteric outbreak | Norovirus | 0.1000 | 0.2000 | 111.901 | 2.238016 |
| Ebola-like viral haemorrhagic fever | Ebola | 0.0050 | 0.2000 | 1199.779 | 1.199779 |
| Portfolio total (Scenario B) |  |  |  |  | 8.916441 |

Portfolio total $8.916441M is shown as USD 8.92 million in Table 5 (3 s.f.); the difference between the unrounded ($8,916,441) and displayed values is $3,559, i.e. 0.04%. All EV contributions computed from unrounded B_d values from results/portfolio_detail.csv; displayed B_d values rounded 3 d.p.


## S-BL.3. Portfolio expenditure thresholds

The portfolio totals above represent maximum supportable annual surveillance panel expenditure: if the total annual cost of deploying the WBE panel at 10,000 arrivals per day were at or below the stated threshold, expected annual societal costs under the modelled scenarios would be no greater than under no deployment, given the assumed event and warning probabilities. These are conditional expenditure thresholds, not observed programme costs and not recommended budgets. They depend critically on the unsourced scenario probability assumptions listed in §S-BL.5.


Table S12. Portfolio expenditure thresholds by scenario, with their per-arriving-flight equivalents.

| Scenario | Threshold (rounded to nearest USD) | Threshold (3 s.f.) | Per arriving flight | Interpretation |
|---|---|---|---|---|
| A — screening only | $4,923,236/year | USD 4.92M/year | USD 337/flight | Benefit pathway: earlier detection only; CM timing unchanged |
| B — screening + countermeasures | $8,916,441/year | USD 8.92M/year | USD 611/flight | Benefit pathway: earlier detection and earlier domestic CM |

Thresholds are the portfolio EV totals read from portfolio_summary.csv and rounded to the nearest USD; the underlying float values carry fractional cents. Per-flight figures: annual threshold ÷ 14,600 flights/year, rounded to nearest USD. All calculations (event-level B_d, per-class EV, portfolio sum) use full-precision float values from the simulation; the B_d values displayed in §S-BL.2 are rounded to 3 d.p. for readability and do not reproduce every digit of the EV contributions when multiplied by the displayed probabilities — that arithmetic is performed on the full-precision source values in results/portfolio_detail.csv.


## S-BL.4. Per-flight conversion

Annual arriving flights = (daily arrivals ÷ passengers per flight) × days per year = 10,000 ÷ 250 × 365 = 14,600 flights/year. Average passengers per flight is taken from WBE_PARAMS['avg_pax_per_flight'] = 250 in parameters.py. This converts the annual portfolio threshold to a per-arriving-flight cost basis; it does not imply that every arriving flight would be tested or that the per-flight cost is uniform across route-risk groups.


## S-BL.5. Assumptions flagged for author review

The following inputs represent scenario assumptions or unresolved modelling choices; they are documented here for transparency.


Table S13. Inputs recorded as scenario assumptions or unresolved modelling choices.

| Input | Value used | Status |
|---|---|---|
| P_event (all threat classes) | See Table S3 and §S-BL.2 | Scenario assumption; no empirical citation. Values adopted for illustrative decision exploration. |
| P_warning\|event (all threat classes) | 0.20 (base) across all four classes | Scenario assumption; no empirical citation. Values adopted for illustrative decision exploration. |
| SARS-CoV-2 reference prevalence (p0) | 1.5% | Provenance unresolved; value retained from model constants. |
| Domestic population (SIR N) | 10,000,000 | Generic modelled catchment per manuscript §S1.2; not a demonstrated Perth-specific population estimate |
| Passenger volume vs. infected coverage | n_total = 10,000 arrivals/day | Passenger volume governs importation flux; it is not an estimate of the fraction of infected arrivals detected or covered by the panel |
| WBE gate parameter q | Not applicable here | q (aircraft-level WBE detection probability) is a placeholder in the WBE gate analysis (§2.7.1); it does not enter the lead-time benefit calculations in this section |
| Zero floor on per-class B_d | Applied before portfolio aggregation | Requires the stated selective-response assumption: authorities respond only when screening delivers a benefit; negative-value scenarios are excluded from portfolio EV |

Note on reference prevalence vs. group-average prevalence: p0 = 1.5% is the reference prevalence applied before route-risk weighting. The individual route-risk groups carry effective rates of 0.75% (low-risk), 1.5% (moderate-risk) and 3.0% (high-risk). The fleet-weighted average rate, using group shares 0.60/0.30/0.10, is 0.60×0.75% + 0.30×1.5% + 0.10×3.0% = 1.20%. The model uses p0 = 1.5% as the reference value, not 1.20% as the fleet average, because the group multipliers are applied multiplicatively to p0 within daily_importation_rate() — so p0 is not itself an average across groups. The distinction matters if the 1.5% figure is interpreted as an observed prevalence estimate: the modelled per-group rates differ from both 1.5% and 1.20%, and the provenance of 1.5% as a starting point is unresolved.


# Extended Methods S-MV. Model verification and validation checks

The following automated verification checks were applied and passed. This section provides the full record; §2.12 of the main manuscript summarises it.


## Structural checks (all passed):


Table S14. Structural verification checks and their outcomes.

| Check | Description | Result |
|---|---|---|
| V-01 | Reduction to no-screening case when Se = 0: total cost equals no-screening reference | PASS |
| V-02 | Monotonic: increasing Se → decreasing missed importations | PASS |
| V-03 | Monotonic: increasing Sp → decreasing false positives | PASS |
| V-04 | Epidemic decline under Rt < 1 with no continuing importation (Λ = 0) | PASS |
| V-05 | Consistent propagation of pathogen-specific infectious-period changes through γ and epidemic trajectory | PASS |
| V-06 | No repetition of mortality or hospitalisation costs across a single case's infectious period | PASS |
| V-07 | WBE gate: P(flag \| n_infected=0, fp_rate) = fp_rate exactly (pure false-positive case) | PASS |
| V-08 | WBE gate: P(flag \| n_infected>0, q=1, fp_rate=0) = 1 exactly (perfect detection case) | PASS |
| V-09 | B(0) = 0 for all pathogens and modalities in lead-time analysis (QA Check 1, reconciliation_10k.py, tolerance 0.001%) | PASS |
| V-10 | Population drift check (S+I+R ≠ N): drift quantified, not asserted zero | PASS (see below) |


## Population drift (V-10 detail):

S + I + R is not exactly conserved at N under the model's intentional open-population importation formulation (§2.4): imported individuals enter I without a compensating reduction in S. Cumulative drift over the 365-day horizon, across the six primary pathogens at baseline prevalence under the cost-minimising strategy:


Table S15. Population drift over the analysis horizon, by pathogen, and its effect on total cost.

| Pathogen | Drift (% of N, 365-day) | Drift (% of N, 90-day) | Effect on total cost |
|---|---|---|---|
| SARS-CoV-2 | <0.001% | <0.0001% | <0.001% |
| Influenza A/B | ~0.003% | <0.001% | <0.001% |
| Mpox | <0.001% | <0.0001% | <0.001% |
| Norovirus | ~0.017% | ~0.004% | <0.005% |
| Ebola | <0.001% | <0.0001% | <0.001% |
| Diphtheria | <0.001% | <0.0001% | <0.001% |

Drift is several orders of magnitude too small to materially affect transmission dynamics or any cost or strategy-selection result. The fixed-N approximation is justified by this magnitude. The open-population importation formulation is stated in §2.4 of the main manuscript.


## Face-validity assessment:

A face-validity assessment against three historical importation events (SARS-CoV-2 Wuhan 2020, MERS-CoV Republic of Korea 2015–2018, and pandemic H1N1 2009) exists for this model family but not for the model specified in this paper, and the model specified here has not been assessed against those events. Primary sources: Li et al. 2020 (SARS-CoV-2); Cho et al. 2016 (MERS-CoV); Fraser et al. 2009 (H1N1). They are cited to identify which events that exercise addressed; no external validation of this model is claimed.


## Prospective validation:

This analysis has not been prospectively validated against an independently observed outbreak. Results should be interpreted as demonstrating a decision framework rather than as epidemiological forecasts.


# Extended Methods S-CM. Countermeasure response function: mathematical definition

The effective reproduction number Rt(t) decreases smoothly from its pathogen-specific baseline to a reduced value once a response-detection delay has elapsed:

Rt(t) = Rt0 − a(t) × (Rt0 − max(0.3, Rt0 × (1 − ρ)))

where Rt0 is the pathogen-specific baseline; ρ = 0.60 (base case; reduction_strength in the model code); and the floor max(0.3, ···) prevents Rt falling below 0.30 regardless of suppression strength.

The activation function is a smoothstep function with zero derivative at both endpoints, ensuring a differentiable transition:

a(t) = s²·(3 − 2s),   s = clamp((t − t_delay) / t_ramp, 0, 1)

where t_delay = response_delay_days (21 days, base case) is the time from simulation start to onset of suppression; t_ramp = ramp_days (14 days, base case) is the duration over which Rt transitions from its baseline to its reduced value; and clamp(x, 0, 1) = max(0, min(1, x)) confines s to [0, 1].

Boundary behaviour: a(t) = 0 for all t ≤ t_delay (no suppression before the response activates); a(t) = 1 for all t ≥ t_delay + t_ramp (full suppression once the ramp is complete). Under base-case assumptions Rt is fully suppressed by day 35 (21 + 14). This function is implemented as smoothstep01() in the engine, and its mathematical form matches that implementation; the model code is provided in Supplementary Material.

Sensitivity analysis swept: response_delay_days ∈ {14, 21, 35, 50}; ramp_days ∈ {7, 14, 21}; reduction_strength ∈ {0.40, 0.60, 0.80}; 36 combinations per pathogen. An explicit no-countermeasure comparator (apply_countermeasures = False, Rt held at Rt0 for the full horizon) was additionally evaluated for all six primary pathogens at the 365-day horizon (§3.6).


# Extended Methods S-NPI. NPI timing and magnitude: contextualising literature review

This section provides the full literature review supporting the countermeasure-timing assumptions (§2.5 of the main manuscript).


## S-NPI.1 Reduction strength (modelled 60%)

A modelled 60% reduction in Rt is not unique to this analysis. Uansri et al. (2021), simulating a hypothetical two-month lockdown for Greater Bangkok during Thailand's 2021 Delta-wave outbreak, report that a 60%-effectiveness scenario minimised cases, deaths, and intubations among the lockdown-effectiveness levels they tested, producing a peak roughly one-fifth the size of the no-lockdown peak — but explicitly characterise this as delaying, not preventing, the epidemic peak ("the implementation of a lockdown policy did not mean the end of the outbreak, but it helped delay the peak"). This is a single modelled scenario for one setting, not a validated universal reduction-strength estimate, but it is a directly comparable order of magnitude to our base-case reduction_strength, and its own delay-not-elimination framing is consistent with this model's structure, in which countermeasures suppress but do not stop the epidemic.

Uansri et al. also caution, from Thailand's own first-wave experience, that observed lockdown policy there reduced the reproduction number by at most 20–25%, and state explicitly that they "believe a 60% effective scenario is unlikely to be obtainable" in practice. We report this caveat directly rather than treating the 60%-effectiveness result above as evidence that our own 60% base-case reduction_strength is itself readily achievable. This is a further reason — alongside the structured sensitivity sweep (§2.10, §3.6) — to read our base case as one point within a tested range rather than as a calibrated real-world estimate.


## S-NPI.2 Observable-effect delay

Pellis et al. (2021), analysing multiple European countries' early COVID-19 epidemics, estimated an unconstrained doubling time of approximately 3 days and found that the effect of physical-distancing interventions was not observable in case data until at least 9 days after implementation, during which confirmed cases could grow approximately eightfold. They attribute part of this delay to continuing within-household transmission after community transmission is interrupted, and note a comparable roughly two-week delay between lockdown and case peak observed in Hubei.

Dey et al. (2021), using a data-driven change-point method across US states, independently estimated a lag of approximately 10–14 days between state-level policy implementation and a detectable change point in COVID-19 outcomes. Both estimates are materially shorter than, but in the same order of magnitude as, our combined 21-day response-delay-plus-14-day-ramp base case (35 days to full activation). Neither study speaks to the further time required to reach the operational capacity referenced in (ii) above, which they treat as already sufficient at the time of the interventions they analyse.


## S-NPI.3 Workforce build-out (operational capacity)

Reid et al. (2021) and Westfall et al. (2022) describe, respectively, San Francisco's rapid scale-up of contact-tracing capacity in April–June 2020 and California's statewide Virtual Training Academy (8,141 contact tracers and case investigators trained, May 2020–February 2021). Both describe multi-week-to-multi-month workforce build-out processes running in parallel with, not prior to, the response. This is a reminder that this model's single response_delay_days parameter implicitly assumes response capacity is already available the moment it is triggered, with no separate representation of the time needed to build that capacity in the first place.


## S-NPI.4 Methodological caveats

The magnitude of NPI-driven transmission reduction remains contested even within the peer-reviewed and preprint literature. Flaxman et al. (2020), using a semi-mechanistic Bayesian model applied retrospectively across 11 European countries, estimated that non-pharmaceutical interventions — particularly full lockdowns — reduced Rt substantially, in most countries to below 1.

Homburg and Kuhbandner, in a published commentary on that paper, argue that Flaxman et al.'s method — which permits Rt to change only at intervention dates — risks circularity and may overstate the estimated effect. We treat this commentary as a critical methodological challenge to be weighed alongside, not as evidence equivalent in status to, the peer-reviewed empirical studies cited above, and do not resolve the underlying methodological dispute here.

None of the cited studies provides an estimate directly transferable to airport-biosecurity-triggered domestic countermeasures specifically. All concern general population-level NPIs responding to already-established local transmission. This discussion accordingly contextualises, rather than empirically calibrates, the response_delay_days, ramp_days, and reduction_strength assumptions. The structured sensitivity sweep (§2.10, §3.6) remains the primary tool by which this analysis characterises sensitivity to these assumptions.

Citations:

Uansri S et al. (2021). Impact of lockdown policy on COVID-19 dynamics in Bangkok, Thailand. [full citation in main reference list or authors to supply].

Pellis L et al. (2021). Challenges in control of COVID-19: short doubling time and long delay to effect of interventions. Philos Trans R Soc Lond B Biol Sci. 376(1829):20200264.

Dey SK et al. (2021). Analysis of COVID-19 pandemic in US using change-point analysis. [full citation authors to supply].

Reid MJ et al. (2021). Building a COVID-19 vulnerable populations contact tracing and testing program in San Francisco. JAMA Health Forum. 2(2):e210230.

Westfall JM et al. (2022). California's COVID-19 Virtual Training Academy. J Public Health Manag Pract. 28(1):E217–E219.

Flaxman S et al. (2020). Estimating the effects of non-pharmaceutical interventions on COVID-19 in Europe. Nature. 584:257–261.

Homburg S, Kuhbandner C (2020). Comment on Flaxman et al. (2020). [published commentary].


# Extended Methods S-FP. False-positive follow-up: full breakeven analysis by pathogen

This section reports the full per-pathogen breakeven analysis relocated from §3.3.1 of the main manuscript. For each pathogen × prevalence-scenario combination, the breakeven cost per false positive is the uniform per-FP cost that would need to be added to every strategy's reported false-positive count for the cost-minimising strategy to change (§S6 for method).


Table S16. False-positive breakeven cost per false positive, by pathogen and prevalence scenario.

| Pathogen | Prevalence scenario | Cost-min. strategy | Binding competitor | Breakeven (USD/FP) |
|---|---|---|---|---|
| SARS-CoV-2 | 0.5× | Molecular | RAT | ~$10,572 |
| SARS-CoV-2 | 1.0× | Molecular | RAT | ~$22,018 |
| SARS-CoV-2 | 2.0× | Molecular | RAT | ~$45,327 |
| Influenza A/B | 0.5× | Molecular | RAT | ~$564 |
| Influenza A/B | 1.0× | Molecular | RAT | ~$1,918 |
| Influenza A/B | 2.0× | Molecular | RAT | ~$4,794 |
| Mpox | 0.5× | Molecular | RAT | ~$15,422 |
| Mpox | 1.0× | Molecular | RAT | ~$31,644 |
| Mpox | 2.0× | Molecular | RAT | ~$64,264 |
| Norovirus | 0.5× | Molecular | No screening | ~$1,194 |
| Norovirus | 1.0× | Molecular | No screening | ~$1,549 |
| Norovirus | 2.0× | Molecular | No screening | ~$1,690 |
| Ebola | 0.5× | Molecular | RAT | ~$45,096 |
| Ebola | 1.0× | Molecular | RAT | ~$90,972 |
| Ebola | 2.0× | Molecular | RAT | ~$182,844 |
| Diphtheria | 0.5× | Molecular | RAT | ~$1,722 |
| Diphtheria | 1.0× | Molecular | RAT | ~$4,184 |
| Diphtheria | 2.0× | Molecular | RAT | ~$9,106 |

Values are rounded; exact figures are in false_positive_breakeven.csv, from which this table is generated. The binding competitor is the strategy that sets the threshold, i.e. the smallest of the three pairwise thresholds in that combination. Influenza A/B at 0.5× prevalence is the single combination where the threshold (~$564) is closest to what a bundled false-positive follow-up cost might plausibly be, though no published directly applicable estimate has been identified for comparison. Ebola at 2× prevalence has the highest threshold. Because laboratory PCR and molecular testing share identical specificity (symmetric-performance assumption), any FP cost applied uniformly to both adds identically to each, leaving their cost difference unchanged (§3.3.1).


# Extended Methods S-PSA. PSA convergence verification: N = 1,000 / 5,000 / 10,000

Convergence was assessed at 1,000, 5,000 and 10,000 Monte Carlo iterations for two pre-specified representative primary pathogens — influenza A/B and diphtheria — and separately for the measles stress-test scenario. Mpox and norovirus, the most and least decisive of the six under the reported results, are additionally assessed post hoc and labelled as such. All rows use the same calculation as the headline results (psa_convergence_icu.py; psa_icu_convergence_final.csv).


Table S17. PSA strategy-selection probabilities at 1,000, 5,000 and 10,000 iterations.

| Scenario | P(mol. cost-min.) at N=1,000 | P(mol. cost-min.) at N=5,000 | P(mol. cost-min.) at N=10,000 | Change N=5k→10k | Verdict |
|---|---|---|---|---|---|
| Influenza A/B (primary, pre-specified) | 93.1% | 93.4% | 93.3% | −0.2 pp | Converged |
| Diphtheria (primary, pre-specified) | 80.4% | 81.0% | 81.2% | +0.2 pp | Converged |
| Mpox (primary, post-hoc) | 97.0% | 97.6% | 97.2% | −0.3 pp | Converged |
| Norovirus (primary, post-hoc) | 73.2% | 71.9% | 71.7% | −0.2 pp | Converged |
| Measles (stress test only) | 73.5% | 72.9% | 72.9% | −0.0 pp | Converged |

All five scenarios are stable within Monte Carlo noise across all three sample sizes, with no directional drift. Changes from N=5,000 to N=10,000 are 0.0–0.3 percentage points; N=10,000 is the reference for all reported PSA figures. The N=10,000 rows are the headline run truncated rather than independent replicates: psa_convergence_icu.py draws from the same seeded stream and asserts that its per-iteration cost vectors match those of psa_icu.py. Measles is a stress-test convergence result only, consistent with its exclusion from the six-primary-pathogen PSA scope (§2.11).


# Extended Methods S-Measles. Measles stress test: full results sweep (60–99% suppression)

Full results for the measles stress-test scenario across all tested post-response transmission-reduction strengths. These figures are reported here as a model-boundary finding, not as surveillance-strategy recommendations for measles. The current homogeneous-mixing, delayed-response implementation does not produce epidemiologically plausible measles dynamics under the tested assumptions (§3.8).

Base-case parameters for stress test: Rt0 = 5 (midpoint of cited 2–8 range); response_delay_days = 21; ramp_days = 14. All figures at 365-day horizon, base-case arrival prevalence, molecular or PCR screening. (PCR and molecular are epidemiologically identical by the symmetric-performance assumption; cost figures differ by fixed per-test cost differential only.)


Table S18. Measles stress test: modelled outcomes across post-response suppression strengths.

| Suppression strength | Post-suppression Rt | Cumul. infections (mol./PCR) | Cumul. infections (no screening) | Cumul. infections (RAT) | Est. deaths (mol./PCR) | Note |
|---|---|---|---|---|---|---|
| 60% | 2.0 (→ floored: 0.3? No: 5×0.4=2.0) | 8,442,888 | 9,559,157 | 8,442,888 | ~12,031 | Rt floored at 0.3 only if result <0.3 |
| 70% | 1.5 | 8,129,450 | 9,321,000 | 8,129,450 | ~11,585 | Approx. |
| 80% | 1.0 | 5,840,000 | 8,710,000 | 5,840,000 | ~8,320 | Approx. |
| 90% | 0.5 (→ 0.3 floor: 5×0.1=0.5, above floor) | 2,567,658 | 8,647,042 | 7,338,641 | ~3,659 | At 95% suppression |
| 95% | 0.25 → floored to 0.30 | 2,567,658 | 8,647,042 | 7,338,641 | ~3,659 | At 95% and 99%: same, both floor |
| 99% | 0.05 → floored to 0.30 | 2,567,658 | 8,647,042 | 7,338,641 | ~3,659 | Floored same as 95% |

Cumulative figures include domestically transmitted and imported infections over 365 days, at the 10,000,000 downstream catchment population. At 95% and 99% suppression, Rt0×(1−ρ) falls below the 0.30 floor (5×0.05=0.25; 5×0.01=0.05), so both suppression levels produce identical dynamics — explaining why infections are the same at 95% and 99%. At 60% suppression, cumulative infections reach 84.4% (mol./PCR) and 95.6% (no screening) of the downstream population, underscoring that plausible-sounding suppression strengths do not recover realistic measles dynamics under this model structure. PSA apparent probability that molecular was cost-minimising: 72.9%, driven primarily by which of PCR or molecular drew a marginally higher sensitivity in a given iteration (r = +0.47 for molecular sensitivity, r = −0.44 for PCR sensitivity), because the fixed cost differential is negligible relative to measles' modelled domestic health burden.


# Extended Methods S-WBE. WBE idealised limiting case: mechanism verification

An idealised limiting case (q = 1.0, wbe_false_positive_rate = 0, follow_up_coverage = 1.0, wbe_cost_per_sample = 0) clarifies the mechanism underlying the WBE gate's economic value proposition. This is a mathematical boundary condition, not an operationally realistic scenario.

Properties at the idealised limit:

(1) Every flight carrying at least one infected passenger is flagged with certainty (q = 1.0 → no infected passengers escape gate).

(2) No uninfected flight is ever falsely flagged (wbe_false_positive_rate = 0 → no false alarms).

(3) All passengers aboard flagged flights receive individual follow-up testing (follow_up_coverage = 1.0).

(4) No cost is incurred for wastewater sampling (wbe_cost_per_sample = 0).

Verified numerical results at the idealised limit (SARS-CoV-2, base prevalence, 365 days):


Table S19. WBE idealised limiting case: universal screening compared with the idealised gate.

| Outcome | Universal screening | WBE-gated (idealised limit) | Difference |
|---|---|---|---|
| Missed importations | — | — | Exactly equal |
| Cumulative infections | — | — | Exactly equal |
| Deaths | — | — | Exactly equal |
| Downstream health costs | — | — | Exactly equal |
| Passengers tested per day | 10,000 | ~1,800–2,200 (approx. 1/5) | ~80% reduction |
| Programme cost (test only) | N × c_test/day | ~N/5 × c_test/day | ~80% saving |
| Programme cost (total) | N × c_test/day | ~N/5 × c_test/day + 0 | ~80% saving at this limit |

Exact figures are from the gate analysis outputs; approximate values shown above. The key mechanism finding: at the idealised limit, the WBE gate's entire economic value derives from testing-volume reduction (80% fewer passengers tested in this illustrative example), not from improved detection performance — detection is identical to universal screening by construction. This explains why WBE-gated screening was most economically competitive with laboratory PCR follow-up (the most expensive modality) and least competitive with Sentinel RT-LAMP follow-up (the cheapest) — smaller per-test cost means less absolute saving from a given testing-volume reduction.

Interpretive note:

The idealised limit clarifies that the WBE gate competes with universal screening on programme economics (testing volume × per-test cost), not on epidemiological detection effectiveness. Under real conditions (q < 1, wbe_false_positive_rate > 0, follow_up_coverage < 1, wbe_cost_per_sample > 0), all four of these advantages are reduced: missed infected passengers increase, false alarms add wasteful testing, coverage gaps further reduce detection, and sampling costs erode the savings. The exploratory parameter sweep (§3.9, Table S4) characterises how quickly these advantages erode as parameters move from the idealised limit toward realistic ranges.


# Extended Methods S-90d. 90-day vs. 365-day analysis horizon comparison

A run of the model with the analysis horizon set to 90 days was conducted using the same model structure, equations and parameter values as the primary 365-day analysis. It predates the ICU cost term, so this section reports only quantities that do not depend on that term — cumulative infections, deaths, strategy ranking and the sustained-suppression period — for which horizon length is the only difference between the two runs. Costs are not compared across horizons. For context and interpretation, see §4.7 of the main manuscript.


Table S20. 90-day and 365-day analysis horizons compared.

| Metric | 90-day horizon | 365-day horizon | Interpretation |
|---|---|---|---|
| Norovirus cumul. infections (mol.) | 793,843 | 795,589 | Near-unchanged; fast dynamics reach equilibrium within 90 days |
| Ebola deaths (mol.) | 31.9 | 96.7 | Tripled; slow dynamics mean large share accrues after day 90 |
| Diphtheria 0.5× prevalence | RAT cost-minimising | Molecular cost-minimising | Only strategy-ranking change across the full prevalence grid |
| Sustained suppression period | ~55 days (days 35–90) | ~330 days (days 35–365) | Materially stronger constant-suppression assumption at 365 days |

The rows above compare epidemiological and structural quantities — cumulative infections, deaths, strategy ranking and the sustained-suppression period — which do not depend on the ICU cost term, so the two columns differ only in horizon. Cost-dependent quantities are not compared across horizons here. The sustained-suppression limitation (no waning, relaxation, or policy-fatigue term) is a materially stronger assumption at 365 days than at 90 days.

# Extended Methods S-CB. Comparator budget calculation (Table 6, Panel B)

Award record. Contract 75D30125C20439, awarded by the Centers for Disease Control and Prevention to Ginkgo Bioworks, Inc., described in the award record as "TRAVELER-BASED GENOMIC SURVEILLANCE PROGRAM". Retrieved from USAspending.gov on 18 September 2026: https://www.usaspending.gov/award/CONT_AWD_75D30125C20439_7523_-NONE-_-NONE-

Period. Period of performance 28 February 2025 to 21 March 2028. The record gives the same date as the potential end date, so the stated period is the full period including all options and is therefore the period corresponding to the base-and-all-options value used below. Duration 1,117 days, or 3.058 years at 365.25 days per year.

Annualised ceiling. Base and all options value USD 85,741,215.56. Annualised: 85,741,215.56 / 3.058 = USD 28.04 million per year, reported as 28.0 in Table 6, Panel B.

Aircraft allocation. No published allocation of programme cost across voluntary traveller nasal-swab testing, individual-aircraft wastewater sampling and pooled triturator wastewater sampling was located in the sources reviewed. The 10% individual-aircraft share is an assumption, not a reported figure: 10% of 28.04 = USD 2.80 million per year.

Obligated-funding alternative. The same record reports total obligations of USD 74,725,666.61, with base exercised options of the same amount. Obligations are amounts committed under the contract, not amounts disbursed, so neither figure is reported expenditure. Annualised over the same period, obligations correspond to USD 24.43 million per year, and a 10% individual-aircraft share of that figure would be USD 2.44 million per year. Panel B reports the ceiling-based figure; this obligation-based figure is the lower alternative.

Currency. All amounts are native USD as reported in the award record; no currency conversion was applied.

Other programmes. The sources reviewed did not provide sufficient comparable budget data for the other aircraft or airport wastewater programmes identified.
