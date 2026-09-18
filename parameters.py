"""
Publication-analysis parameter set.
Source: manuscript_final.docx (turkey/manuscript_final.docx) Supplementary Table S1
and Supplementary Table S2 (WBE shedding evidence), as they stood after the
manuscript's second simulated peer-review round. Point estimates are the
MIDPOINT of the manuscript-cited literature range for each parameter, unless
otherwise noted. Ranges are retained for PSA distributions.

Pathogen set restricted per Task 3: substantial, well-characterised
human-to-human transmission compatible with an SIR-type model.
Removed: Cholera, Dengue, Zika, H5N1, Yellow Fever, Hantavirus
(vector-borne / environmental / zoonotic-spillover-dominated; retained only
as "removed pathogen" notes for transparency, not run in primary analysis).
"""

def mid(lo, hi):
    return (lo + hi) / 2.0

# ---------------------------------------------------------------------------
# Pathogen-specific parameters (7 retained pathogens)
# All ranges as published in manuscript Supplementary Table S1.
# Where S1 gives multiple sub-ranges (variant/outbreak-dependent), the
# ancestral/most-general-purpose sub-range is used as the base case, and this
# choice is flagged in `notes`.
# ---------------------------------------------------------------------------
PATHOGENS = {
    "SARS-CoV-2": {
        "Rt_range": (1.2, 2.0),
        "infectious_period_range": (4, 7),
        "CFR_pct_range": (0.1, 1.4),
        "hosp_rate_pct_range": (5, 10),          # % of SYMPTOMATIC cases hospitalised
        "hosp_duration_days_range": (7, 10),
        "symptomatic_fraction_pct_range": (60, 70),
        "detectable_at_arrival_pct_range": (45, 55),
        "wbe_applicable": True,
        "wbe_evidence": "strong (++)",
        "baseline_prevalence_pct": 1.5,           # retained from prior engine constants (not overridden by manuscript S1)
        "notes": "Ancestral/pre-Omicron Rt sub-range used as base case (Omicron 5.1-8.2 noted separately in S1 but not used for base-case point estimate). "
                 "CFR denominator (SOURCE-VERIFIED, see SOURCE_VERIFICATION_REPORT.md): Table S1's CFR column is footnoted 'confirmed deaths / "
                 "confirmed cases' by default, but the SPECIFIC reference cited for SARS-CoV-2's CFR row ([2] in Table S1's reference list = "
                 "Levin AT, Hanage WP, Owusu-Boaitey N, et al. 'Assessing the age specificity of INFECTION FATALITY RATES for COVID-19...' "
                 "Eur J Epidemiol 2020;35(12):1123-1138) is explicitly an infection-fatality-rate study by its own title, not a case-based CFR "
                 "study. This is a labelling inconsistency in Table S1 (generic footnote says CFR; the cited source is IFR), verified by reading "
                 "the actual cited paper's title/abstract, not inferred from the value's magnitude. Mortality is NOT symptomatic-gated a second "
                 "time for this pathogen.",
        "mortality_already_infection_based": True,
    },
    "Influenza A/B": {
        "Rt_range": (1.1, 1.4),
        "infectious_period_range": (3, 5),
        "CFR_pct_range": (0.01, 0.1),
        "hosp_rate_pct_range": (1, 3),
        "hosp_duration_days_range": (4, 6),
        "symptomatic_fraction_pct_range": (50, 70),
        "detectable_at_arrival_pct_range": (40, 55),
        "wbe_applicable": False,                  # Table S2: "Limited" evidence, excluded from WBE arm
        "wbe_evidence": "limited (~) - excluded",
        "baseline_prevalence_pct": 4.0,
        "notes": "Seasonal sub-range used as base case (pandemic H1N1 sub-range noted separately). "
                 "CFR denominator (SOURCE-VERIFIED, see SOURCE_VERIFICATION_REPORT.md): Table S1's reference list cites [5] Dawood FS, Iuliano AD, "
                 "Reed C, et al. 'Estimated global mortality associated with the first 12 months of 2009 pandemic influenza A H1N1 virus "
                 "circulation: a modelling study.' Lancet Infect Dis 2012;12(9):687-695 for this row. Verified (web search): Dawood et al. modelled "
                 "TOTAL respiratory+cardiovascular deaths (151,700-575,400) at ~15x the number of laboratory-confirmed deaths (18,500) -- i.e. a "
                 "population/infection-based mortality estimate, not a diagnosed-case-based CFR. Cross-checked quantitatively: Dawood's estimated "
                 "death count against an estimated 700M-1.4B global 2009 H1N1 infections implies an IFR-equivalent rate of ~0.01-0.08%, which "
                 "matches Table S1's cited 0.01-0.1% (seasonal) / 0.02% (pandemic) range closely. Mortality is therefore NOT symptomatic-gated a "
                 "second time for this pathogen either (change from the prior revision, which gated Influenza's mortality -- corrected here after "
                 "citation verification, not inferred from magnitude).",
        "mortality_already_infection_based": True,
    },
    "Mpox": {
        "Rt_range": (1.2, 1.8),
        "infectious_period_range": (7, 14),
        "CFR_pct_range": (1, 10),                 # Clade I range used (higher-severity, more conservative)
        "hosp_rate_pct_range": (5, 20),
        "hosp_duration_days_range": (7, 21),
        "symptomatic_fraction_pct_range": (90, 90),
        "detectable_at_arrival_pct_range": (60, 80),
        "wbe_applicable": True,                   # Table S2: included with caveat, moderate evidence
        "wbe_evidence": "moderate (+) - included with caveat: no aircraft-specific data",
        "baseline_prevalence_pct": 0.4,
        "notes": "Clade I CFR range (1-10%) used as conservative base case; Clade IIb (<1% OECD) noted separately in S1.",
    },
    "Norovirus": {
        "Rt_range": (1.5, 2.0),
        "infectious_period_range": (1, 3),
        "CFR_pct_range": (0.0005, 0.001),         # "<0.001%" in S1; treated as range up to 0.001%
        "hosp_rate_pct_range": (0.5, 1),          # "<1%"
        "hosp_duration_days_range": (1, 3),
        "symptomatic_fraction_pct_range": (50, 70),
        "detectable_at_arrival_pct_range": (30, 45),
        "wbe_applicable": True,                   # Table S2: strong evidence, highest shedding of any modelled pathogen
        "wbe_evidence": "strong (++) - highest faecal shedding of any modelled pathogen",
        "baseline_prevalence_pct": 2.5,
        "notes": "CFR range interpreted as (0.0005%, 0.001%) from S1's '<0.001%' notation; extremely low and numerically sensitive.",
    },
    "Ebola": {
        "Rt_range": (1.2, 2.0),
        "infectious_period_range": (7, 14),
        "CFR_pct_range": (25, 90),
        "hosp_rate_pct_range": (80, 100),
        "hosp_duration_days_range": (7, 14),
        "symptomatic_fraction_pct_range": (90, 90),
        "detectable_at_arrival_pct_range": (60, 75),
        "wbe_applicable": True,                   # Table S2: included with caveat, moderate evidence
        "wbe_evidence": "moderate (+) - included with caveat: theoretically applicable, no aircraft lavatory validation",
        "baseline_prevalence_pct": 0.1,
        "notes": "CFR range very wide (25-90%, mean ~50% across outbreaks per S1); midpoint used is 57.5%, materially above the S1-stated cross-outbreak mean of ~50% - PSA should use the mean/skewed distribution, not a symmetric midpoint. Flagged in changelog.",
    },
    "Diphtheria": {
        "Rt_range": (1.5, 4.0),
        "infectious_period_range": (14, 28),
        "CFR_pct_range": (5, 10),                 # untreated sub-range used as conservative base case
        "hosp_rate_pct_range": (20, 40),
        "hosp_duration_days_range": (5, 10),
        "symptomatic_fraction_pct_range": (30, 50),
        "detectable_at_arrival_pct_range": (25, 40),
        "wbe_applicable": False,                  # Table S2: no documented faecal shedding
        "wbe_evidence": "none (x) - respiratory/contact transmission, no shedding evidence",
        "baseline_prevalence_pct": 0.02,
        "notes": "Untreated CFR sub-range (5-10%) used as conservative base case; treated sub-range (<1%) noted separately in S1 and is more representative of OECD arrival management post-detection, but base case reflects undetected-import risk.",
    },
}

STRESS_TEST_PATHOGENS = {
    "Measles": {
        "Rt_range": (2, 8),
        "infectious_period_range": (8, 10),
        "CFR_pct_range": (0.1, 0.2),
        "hosp_rate_pct_range": (10, 20),
        "hosp_duration_days_range": (5, 7),
        "symptomatic_fraction_pct_range": (95, 95),
        "detectable_at_arrival_pct_range": (70, 85),
        "wbe_applicable": False,
        "wbe_evidence": "limited (~) - excluded from flight-level WBE, sewage used only for coverage monitoring",
        "baseline_prevalence_pct": 2.0,
        "notes": "DEMOTED FROM PRIMARY SET (see FINAL_MODEL_AUDIT.md): with Rt=5 (midpoint) and a "
                 "21-day population-wide response delay, the pre-response growth factor is ~11,300x "
                 "(r = gamma*(Rt-1) = 0.444/day). No post-response suppression strength recovers "
                 "plausible outbreak sizes at this delay -- VERIFIED via dedicated reproducible sweep "
                 "(measles_countermeasure_stress_sweep.py, Issue 2 audit): cumulative infections = "
                 "2,563,970 (25.6% attack rate in the 10M catchment) under laboratory PCR or "
                 "high-throughput molecular screening at BOTH 95% and 99% post-response suppression "
                 "(identical because post-intervention Rt is floored at 0.3 -- see time_varying_rt() -- "
                 "and both suppression levels fall below this floor from a baseline Rt of 5). Real "
                 "measles outbreak control operates via case-level contact tracing / ring vaccination "
                 "within days, a mechanism this homogeneous-mixing, population-wide-delayed-response "
                 "SIR cannot represent at any parameter setting. Retained ONLY as a labelled "
                 "stress-test / boundary scenario illustrating this limitation, not as a primary "
                 "decision-relevant comparator.",
    },
}

REMOVED_PATHOGENS = {
    "Cholera": "Predominantly waterborne/environmental transmission (V. cholerae); R0 range in S1 (2.0-6.0) reflects environmental transmission dynamics, not person-to-person, which the SIR importation-reseeding model cannot represent.",
    "Dengue": "Vector-borne (Aedes mosquito); no sustained human-to-human transmission. S1 R0 explicitly flagged as reflecting 'transmission in endemic vector settings.'",
    "Zika": "Vector-borne (Aedes mosquito) with secondary sexual transmission route; not compatible with airport-importation SIR reseeding structure.",
    "H5N1 Avian Influenza": "Zoonotic spillover-dominated; sustained human-to-human transmission not established (R0 < 1.0 endemic per S1). Pandemic-scenario sub-range (1.5-2.5) is a hypothetical stress-test, not an observed transmission parameter.",
    "Yellow Fever": "Vector-borne (Aedes/Haemagogus mosquito); no human-to-human transmission.",
    "Hantavirus": "Primarily zoonotic (rodent-to-human); human-to-human transmission essentially absent for most strains (R0 < 1.0 per S1, Andes strain the rare exception at ~1.0-1.2).",
}

# ---------------------------------------------------------------------------
# Route / airport configuration (manuscript Supplementary Methods S2.1, S4.1)
# ---------------------------------------------------------------------------
ROUTE_TIERS = {
    "low":  {"share": 0.60, "multiplier": 0.50},
    "mid":  {"share": 0.30, "multiplier": 1.00},
    "high": {"share": 0.10, "multiplier": 2.00},
}
N_TOTAL_ARRIVALS_PER_DAY = 10_000     # manuscript base configuration (S2.1)
DOWNSTREAM_POPULATION = 10_000_000    # manuscript S1.2, "generic large metropolitan catchment"

# ---------------------------------------------------------------------------
# Modality performance (manuscript Table 1, main text)
# NOTE: Table 1 does NOT report specificity for any modality - a documentation
# gap in the manuscript. Specificity values below are RETAINED from the prior
# engine (src/engine/methodProfiles.js) since they are not contradicted by
# the manuscript and are standard high-specificity assay values; flagged as
# carried over, not manuscript-sourced.
# ---------------------------------------------------------------------------
MODALITIES = {
    "none": {
        "label": "No systematic screening",
        "sensitivity_range": (0.0, 0.0),
        "specificity_range": (1.0, 1.0),
        "cost_per_test_range": (0, 0),
        "source": "n/a",
    },
    "rapid": {
        "label": "Rapid Antigen Test (RAT)",
        "sensitivity_range": (0.45, 0.90),        # manuscript Table 1: "45-90% (pathogen-dependent)"
        # CORRECTED (final-locked-model audit, controlled specificity-only
        # unlock, Reference Issue 1 resolution): the previous range
        # (0.973, 0.995) was NOT an antigen-test estimate at all -- it was the
        # Dinnes et al. RAPID MOLECULAR assay pooled specificity (see "lab"
        # below), mislabelled here as "pooled ANTIGEN test specificity" in an
        # earlier, unverified pass. Directly read (not search-snippet-derived)
        # from the actual cited 2021 CD013705.pub2 full text (PMC8078597):
        # antigen-test specificity is reported stratified by symptom status,
        # not as a single unstratified pooled figure in the formal
        # Summary-of-Findings table -- Symptomatic: 99.5% (95% CI 98.5-99.8%;
        # 37 evaluations/27 studies/15,530 samples/4,410 confirmed cases);
        # Asymptomatic: 98.9% (95% CI 93.6-99.8%; 12 evaluations/10
        # studies/1,581 samples/295 confirmed cases). The review's own
        # abstract "Main results" narrative additionally states an overall
        # summary figure across most brands/participant groups: "overall
        # summary specificity 99.6%, 95% CI 99.0% to 99.8%" -- this narrative
        # figure is used here as the single point/range value (consistent
        # with how this model uses one range per modality), since it is the
        # review's own stated aggregate rather than an average I computed.
        # Point estimate (mid of range) accordingly moves from 0.984 to 0.994.
        "specificity_range": (0.990, 0.998),
        "specificity_source": "SOURCE-VERIFIED (direct full-text read of PMC8078597, the actual cited 2021 CD013705.pub2 version, not a search "
                               "snippet): Dinnes J, Deeks JJ, Berhane S, et al. 'Rapid, point-of-care antigen tests for diagnosis of SARS-CoV-2 "
                               "infection.' Cochrane Database Syst Rev 2021, CD013705.pub2. Abstract/Main results: 'overall summary specificity "
                               "99.6%, 95% CI 99.0% to 99.8%' for antigen tests across most brands and participant groups (Summary-of-Findings "
                               "table gives the same evidence stratified: symptomatic 99.5% [98.5-99.8%], asymptomatic 98.9% [93.6-99.8%]). This "
                               "REPLACES a prior mislabelled figure that was actually the review's rapid-molecular-assay statistic, not an "
                               "antigen-test one (see FINAL_MODEL_AUDIT.md / CHANGELOG.md Correction 9 for the full trace).",
        "cost_per_test_range": (5, 20),
        "source": "Manuscript Table 1",
    },
    "lab": {
        "label": "Laboratory PCR",
        "sensitivity_range": (0.95, 0.99),
        "specificity_range": (0.973, 0.995),
        "specificity_source": "PROVENANCE CORRECTED (final-locked-model audit, Reference Issue 1): this range (unchanged) is Dinnes J, Deeks JJ, "
                               "Berhane S, et al. 'Rapid, point-of-care antigen and molecular-based tests for diagnosis of SARS-CoV-2 infection.' "
                               "Cochrane Database Syst Rev. 2020 Aug 26;2020(8):CD013705 (the ORIGINAL 2020 review, PMID 32845525, PMCID "
                               "PMC8078202) -- NOT the 2021 .pub2 update, which was previously (incorrectly) cited as the source of this exact "
                               "figure. Directly verified in that source's Summary of Findings table: rapid molecular assays, 13 evaluations in "
                               "11 studies, 2,255 samples, pooled specificity 98.9% (95% CI 97.3-99.5%). This is explicitly a RAPID MOLECULAR "
                               "POINT-OF-CARE assay estimate (ID NOW, Xpert Xpress-type platforms), not a centralised reference-laboratory RT-PCR "
                               "estimate -- standard lab-based RT-PCR was not separately pooled in this review. Applying this molecular-POC range "
                               "to 'Laboratory PCR' and 'Sentinel RT-LAMP' (below) is a DELIBERATE SYMMETRIC STRUCTURAL ASSUMPTION for this "
                               "comparative analysis, not a claim that these three technologies are empirically identical or that this figure "
                               "was measured on laboratory PCR itself. Numerical value unchanged from the prior (mislabelled-provenance) version.",
        "cost_per_test_range": (50, 150),
        "source": "Manuscript Table 1",
    },
    "molecular": {
        "label": "High-throughput molecular screening",
        # Base case: Sentinel RT-LAMP is intentionally parameterised with
        # PCR-COMPARABLE analytical performance (shared (0.95, 0.99)
        # sensitivity range and shared (0.973, 0.995) specificity range,
        # identical to "lab" below) per explicit project specification. This
        # is NOT an attempt to flatter Sentinel: sensitivity/specificity are
        # kept SYMMETRIC with PCR so that any MODELLED cost difference
        # between the two is attributable to cost_per_test alone -- not to
        # an assumed detection-performance edge.
        #
        # CORRECTION 16 (documentation clarification, turnaround-time
        # framing revision): the sentence previously here listed "cost,
        # throughput, turnaround time, and scalability" together as though
        # all four drove the modelled cost-effectiveness difference. Only
        # cost_per_test_range (below) is actually read by engine.py's cost
        # calculation and therefore drives any computed result. Throughput
        # is documented in the manuscript (Table 1, Section 2.3) as a
        # feasibility descriptor but is NOT enforced as a capacity
        # constraint anywhere in the cost function. Turnaround time and
        # operational scalability are not represented as parameters
        # anywhere in this codebase at all -- they do not enter Eq. 1,
        # the SIR transmission step, or any of the four cost terms in
        # Section 2.6 of the manuscript -- and are discussed in the
        # manuscript (Methods 2.7; Discussion 4.2; Limitations 4.8) purely
        # as unmodelled operational considerations, not as drivers of any
        # numerical result. See CHANGELOG.md CORRECTION 16. No parameter
        # value, dict key, or computational logic changed by this edit.
        # CORRECTION 10 (documentation cleanup, Reference Issue 1 follow-up):
        # a stray "specificity": 0.997 point key previously existed here.
        # It was never read by any analysis script (all deterministic/PSA/
        # WBE code computes specificity from specificity_range via mid()/
        # Beta-sampling) and had no defensible source -- see CHANGELOG.md
        # CORRECTION 10 for the full provenance trace and verification that
        # its removal changes no computed result. Removed, not replaced.
        "sensitivity_range": (0.95, 0.99),
        "specificity_range": (0.973, 0.995),      # kept IDENTICAL to "lab" (symmetric performance, see module notes)
        "specificity_source": "PROVENANCE CORRECTED (final-locked-model audit, Reference Issue 1): held symmetric with laboratory PCR per project "
                               "specification -- same corrected source as 'lab' above (Dinnes et al. 2020 original review, rapid-molecular-assay "
                               "pooled specificity 98.9%, 95% CI 97.3-99.5%, n=2255; NOT the 2021 .pub2 update). Same deliberate symmetric "
                               "structural-assumption framing and same molecular-POC-vs-Sentinel-RT-LAMP caveat as PCR applies here: this figure "
                               "was not measured on the Sentinel RT-LAMP platform itself. Numerical value unchanged.",
        "cost_per_test_range": (10, 30),
        "source": "Base-case molecular-performance assumption, held symmetric with laboratory PCR per project specification. Sentinel RT-LAMP's point performance is MANUFACTURER-REPORTED (Avicena). A peer-reviewed but company-affiliated evaluation exists (Dewhurst et al., Sci Rep 2022;12:5936: 98.7% sensitivity, 97.6% specificity on the actual Sentinel/Hayat system at its reported 22-minute cutoff, broadly consistent with the modelled ranges), but independent third-party validation remains absent (see manuscript Reference Issue 2 audit). PCR performance (95-99% per manuscript Table 1) is the peer-reviewed, non-proprietary reference-standard value.",
        "manufacturer_reported": True,
        "performance_symmetric_with": "lab",
        # Documentation list only (not read by any script). Of these four:
        # cost_per_test is the sole MODELLED economic differentiator (drives
        # C_prog); throughput is a documented FEASIBILITY DESCRIPTOR (Table
        # 1) not enforced as a constraint; turnaround time and operational
        # scalability are UNMODELLED operational considerations with no
        # representation anywhere in engine.py (see CORRECTION 16 above).
        "differentiators_vs_lab": ["cost_per_test ($10-30 vs $50-150)", "throughput (>3,000 pax/hr vs 50-150 pax/hr)", "turnaround time", "operational scalability"],
    },
}

# ---------------------------------------------------------------------------
# Economic parameters (manuscript Supplementary Methods S3)
# ---------------------------------------------------------------------------
# ICU COST: EXPLICITLY OMITTED FROM THE PRIMARY CALCULATION.
# ICU-specific cost is NOT modelled for any of the 6 primary pathogens, for
# the reason stated plainly here: neither the manuscript's Supplementary
# Methods nor Table S1 provides a pathogen-specific ICU-fraction-of-
# hospitalised or ICU-duration parameter, and per "do not invent values" no
# generic/illustrative substitute is used in the base case either (an earlier
# revision of this file exposed a generic 10-30% severity band for
# sensitivity purposes only; on review that framing risked being read as "ICU
# burden is zero," which is NOT the claim -- ICU burden is UNKNOWN and
# UNMODELLED here, not zero). Total societal cost in this analysis should be
# read as a LOWER BOUND on true health-system burden for any pathogen with a
# non-trivial ICU admission rate (plausibly SARS-CoV-2, Ebola, Diphtheria
# with airway obstruction, severe Mpox). The structural code path for an
# ICU cost term still exists (engine.py: icu_fraction_of_hosp_override
# parameter) but defaults to None / $0 and is not used by any of the
# primary/PSA/decision-surface scripts in this package.
ICU_STRUCTURE = {
    "icu_cost_status": "OMITTED - not separately modelled. See comment above. Do not report as evidence of zero ICU burden.",
    "icu_incremental_cost_per_day_IF_EVER_PARAMETERISED": 3000,  # retained only as a placeholder for future work; unused by default
}

ECON = {
    # CORRECTION 12 (economic-reference reconciliation, Reference Issue 4):
    # the inline comments below previously attributed several of these
    # values to WHO, US EPA, and OECD sources that could not be verified on
    # direct audit (WHO does not publish a monetary VSL at all; EPA's own
    # stated default is $7.4M in 2006 dollars updated to the analysis year,
    # not a fixed $11.6M headline figure; no specific OECD dataset/year was
    # ever identified for the $250/day wage figure). Numeric values are
    # UNCHANGED -- only these provenance comments were corrected, to match
    # the corresponding manuscript wording. See CHANGELOG.md CORRECTION 12
    # for the full audit trail.
    "VSL_base_case": 3_500_000,     # pre-specified structural base-case VSL assumption for this decision model, NOT a WHO estimate (no WHO monetary VSL exists to reference)
    "VSL_low_resource": 300_000,    # lower sensitivity-analysis anchor (stated assumption), NOT an externally estimated VSL
    "VSL_high_income": 11_600_000,  # upper sensitivity-analysis anchor; NOT verified as EPA's own stated central estimate (EPA's official default is $7.4M in 2006 dollars, updated to the analysis year -- see manuscript Section 2.6/2.10 for this distinction)
    "c_bed_per_day": 2000,          # pre-specified structural/order-of-magnitude assumption, NOT a jurisdiction-specific observed inpatient cost
    "w_avg_per_day": 250,           # pre-specified structural/order-of-magnitude assumption; NOT verified against a specific OECD dataset/year (do not describe as "OECD average" without that citation)
    "epsilon_friction": 0.70,       # additional productivity-loss multiplier (structural modelling assumption); NOT an empirically estimated friction-cost parameter in the sense of the friction-cost method literature, which the manuscript no longer describes this as (key name retained for code compatibility only -- see engine.py/decision_surface.py/psa.py references)
    "discount_rate_annual": 0.03,   # 3% p.a.; consistent with historical WHO economic-evaluation practice (WHO-CHOICE), NOT NICE reference case (NICE specifies 3.5%, a different rate not used here)
    "discount_start_day": 30,       # discounting applied to costs accruing beyond day 30; a modelling convention adopted for this analysis, NOT a WHO or NICE recommendation. Value unchanged by the horizon revision (CORRECTION 17) that extended horizon_days from 90 to 365; retained as the same within-horizon grace-period convention rather than re-derived for the longer horizon.
    "horizon_days": 365,            # T = 365 days (CORRECTION 17: extended from the original 90-day base case, manuscript S1.3, to test whether conclusions are horizon-sensitive; see CHANGELOG.md CORRECTION 17 and manuscript Section 2.5/2.6/4.8 for full rationale and the assumptions this extension does and does not carry forward)
    # NOTE: the old flat "WBE_cost_per_day_range" (500, 2000) surcharge has
    # been REMOVED as part of the WBE rebuild (see engine.py CORRECTION 7 /
    # WBE_REBUILD.md). WBE costing is now per-flight/per-sample plus
    # per-follow-up-test, via WBE_PARAMS below, not a flat daily add-on.
}

# ---------------------------------------------------------------------------
# WBE (aircraft wastewater-based epidemiology) GATE parameters.
# Rebuilt per post-submission audit ("WBE Issue"): WBE is modelled as an
# aircraft-level analytical gate that triggers targeted individual follow-up
# testing, NOT a standalone passenger diagnostic modality, NOT a flat cost
# surcharge on universal screening, and NOT an early-warning/lead-time
# mechanism. Full derivation: engine.py CORRECTION 7 docstring and
# WBE_REBUILD.md.
#
# *** ALL VALUES BELOW ARE STRUCTURAL PLACEHOLDERS, NOT VALIDATED
# AIRCRAFT-LEVEL PERFORMANCE PARAMETERS. ***
# They exist so the gate architecture is runnable and unit-testable. They
# are explicitly NOT the historical 0.88 / 0.95 sensitivity, 0.98
# specificity, or 0.1% prevalence-threshold values from the archived
# simulator or the superseded whitepaper, and must NOT be interpreted as
# literature-supported or used to generate a headline WBE cost-effectiveness
# claim. A dedicated threshold/breakeven sweep (a separate, not-yet-built
# analysis) is required before any WBE result is reported quantitatively.
# ---------------------------------------------------------------------------
WBE_PARAMS = {
    "avg_pax_per_flight": 250,
    # PLACEHOLDER. passengers/flight. Also shapes the burden-dependent
    # detection curve (larger assumed aircraft -> higher expected infected
    # burden per flight at the same prevalence -> easier pooled detection),
    # so it is epidemiologically live, not just a costing constant. Flagged
    # as a candidate for later sensitivity analysis (see WBE audit Point 8).
    "wbe_detection_prob_per_infected_passenger": 0.5,
    # PLACEHOLDER "q": the effective probability that an infected passenger
    # ALREADY WITHIN the model's existing phi-eligible (currently
    # infectious/shedding) population generates a genuine detectable
    # aircraft-wastewater signal. Encompasses shedding, aircraft toilet use,
    # sample recovery, and analytical detection jointly, undecomposed unless
    # evidence requires it. This is NOT the historical flight-level 0.88/0.95
    # sensitivity figures, which were bare, uncited constants.
    "wbe_false_positive_rate": 0.02,
    # PLACEHOLDER: P(false-positive WBE flag | no genuine detectable signal
    # occurred), NOT P(false positive | zero infected passengers) -- see
    # engine.py CORRECTION 7 for the distinction. NOT the historical 0.98
    # specificity figure (different conditioning, different quantity).
    "wbe_cost_per_sample": 50,
    # PLACEHOLDER, USD per pooled aircraft wastewater sample. One sample per
    # arriving flight is the initial modelling assumption (explicitly
    # labelled as such, not an established operational protocol). NOT the
    # historical $500-2,000/day flat figure.
    "follow_up_coverage": 1.0,
    # PLACEHOLDER: fraction of a WBE-flagged flight's passengers who receive
    # individual follow-up testing. 1.0 = full-flight follow-up. Structurally
    # supports partial coverage (0 < coverage < 1) and capacity-limited
    # regimes via override; no single value is asserted as scientifically
    # correct.
}
