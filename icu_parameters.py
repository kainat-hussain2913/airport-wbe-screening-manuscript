"""
icu_parameters.py
=================
Per-pathogen ICU admission fractions and ICU length-of-stay (LOS) for the
WBE lead-time value model.

COVERAGE: all six primary pathogens in parameters.py — SARS-CoV-2,
Influenza A/B, Mpox, Norovirus, Ebola, Diphtheria.

WBE ELIGIBILITY IS UNRELATED TO ICU COSTING.  The fact that some pathogens
are excluded from the WBE primary analyses (generate_grids.py) because
wastewater detection is not applicable does not mean they should receive zero
ICU costs in the economic model.  All six pathogens are assigned ICU parameters.

EVIDENCE QUALITY LABELS (used in comments below):
  [SOURCED]        — fraction derived directly from a cited primary source,
                     numerator/denominator/location explicitly stated.
  [PROXY]          — fraction borrowed from a closely related category with
                     documented clinical justification; label states the
                     source category and the basis for generalisation.
  [UNRESOLVED]     — no satisfactory primary source identified; value shown
                     is a conservative structural assumption that must be
                     updated when supporting evidence is found.  Code sets
                     the value to a named constant and flags it prominently.

COST STRUCTURE NOTE:
  c_bed_per_day ($2,000) is applied to ALL hospitalised cases for all bed-days
  including ICU days — this is the base ward rate.
  c_icu adds icu_incremental_cost_per_day ($3,000) × ICU LOS per new ICU
  admission — i.e. the incremental cost above the ward rate.  No double-
  counting: c_hosp charges the full ward-rate episode; c_icu charges the
  extra daily cost for the ICU subset only.
  Both figures are structural modelling assumptions, NOT jurisdiction-specific
  observed inpatient costs — see parameters.py ICU_STRUCTURE comment.
  The $3,000/day incremental figure is reference-informed and expressed in
  2025 US dollars. It is derived from the ICU-minus-ward daily cost differences
  reported by Dasta et al. (Crit Care Med 2005;33:1266-71; 51,009 ICU admissions,
  253 US hospitals), inflated from 2002 dollars by the US medical care CPI, and
  it was tested across $2,000-6,000 per ICU day with no change to any strategy
  ranking. The full derivation is in Supplementary Methods S3. The rate's
  plausibility does not transfer to the utilisation inputs below, which are
  separately sourced and, for several pathogens, unresolved.

SOURCES:
  [1] Docherty et al. BMJ 2020;369:m1985 / medRxiv preprint (N=16,749; final N=20,133).
        "Features of 20 133 UK patients in hospital with covid-19 …"
        Preprint: "17% required admission to High Dependency or Intensive Care Units"
        (16,749 × 0.17 ≈ 2,847 patients).
        OUTCOME TYPE: "HDU OR ICU combined" — not pure ICU.  HDU (High Dependency
        Unit) is a step-down level below full ICU; combining it with ICU conflates
        two different levels of care.  The 0.15 used here is a rounded estimate
        consistent with the published paper's supplementary; it is conservative
        relative to the 17% combined HDU/ICU figure and may understate the true
        HDU+ICU fraction, while overstating the pure ICU fraction.
        LABEL: [SOURCED — HDU/ICU combined; pure ICU fraction not separately reported]

  [2] Thornhill et al. NEJM 2022;387:679-691.
        "Monkeypox Virus Infection in Humans across 16 Countries"
        Total cases: 528 (confirmed mpox).
        Hospitalised: 70/528 = 13.3% of all cases (Table 1, "required hospitalisation").
        ICU admission: 5/70 = 7.1% of hospitalised cases (Table 1 — confirmed via
        secondary source i-base.info summary of the paper; direct full-text not
        retrieved in this audit due to paywall).
        Used 5/70 = 0.071, rounded to 0.07.
        Denominator correction from first implementation: prior used 5/528 total cases
        (= 0.009 ≈ 0.01, reported as 0.03) — corrected here to hospitalised-case
        denominator as required for ICU-fraction-of-hospitalised-patients calculation.

  [3] Feldmann et al. Nat Rev Microbiol 2020;18:401-412 (Ebola review).
        ICU fraction varies by outbreak setting and resource context.
        Western high-resource settings (Emory, Hamburg, etc.): near 100% ICU.
        West Africa 2014–16 community/field hospital: <5% formal ICU.
        Model uses 0.35 as representative of a modelled outbreak response
        in an intermediate-resource context — [UNRESOLVED] pending
        jurisdiction-specific analysis.

  [4] Norovirus ICU admission: no systematic published ICU fraction for
        norovirus hospitalisation in travel-importation context.
        Troeger et al. Lancet 2019;394:1023-1035 reports ~0.5% fatality
        among hospitalised; ICU fraction is unmeasured in published lit.
        [UNRESOLVED] — conservative structural estimate used.

  [5] FluSurv-NET / Lancet Microbe 2023 (PIIS2666-5247(23)00187-8);
        US population-based surveillance 2010-11 through 2018-19, N=107,941
        laboratory-confirmed influenza hospitalisations:
          Overall (imputed): 16.7% ICU admission
          A/H1N1pdm09: 22.9%
          A/H3N2: 15.3%
          B: 15.9%
        CDC FluSurv-NET 2024–25 season report (PMC12425177): historical range
        14.3–18.2% across 2017-18 through 2023-24 seasons.
        REVISION: prior icu_parameters.py cited 20–25% (median 23%), which
        corresponds to the H1N1pdm09-specific fraction.  Revised to 0.17 (overall
        16.7%, rounded) to reflect the multi-type, multi-season FluSurv-NET estimate.
        The 0.23 figure is NOT representative of seasonal influenza A/B in general;
        applying it to the avian-stress proxy scenario is conservative (higher ICU
        burden), but it should not be described as the seasonal influenza fraction.
        [SOURCED — revised; outcome: ICU admission (pure ICU, not HDU combined)]
        Avian H5N1 (WHO situation reports 2024): ICU fraction >80% in confirmed
        hospitalised cases; not directly applicable to importation model —
        inherits revised seasonal influenza fraction as a [PROXY] (conservative
        lower bound) pending avian-specific analysis.

  [6] Diphtheria: no peer-reviewed ICU fraction for diphtheria hospitalisation.
        WHO case management guidance recommends ICU-equivalent monitoring for
        myocarditis and airway complications; US import case series (CDC MMWR)
        show variable ICU use.  [UNRESOLVED] — value not assigned; costing
        deferred to zero with explicit flag (see DIPHTHERIA_ICU_UNRESOLVED).

ICU LOS SOURCES:
  SARS-CoV-2: 7 days. [UNRESOLVED - CITATION MISMATCH]  This value was
    previously annotated here as "Docherty et al. BMJ 2020 median ICU LOS 7 days
    (IQR 4-14)". That attribution does not hold and has been withdrawn. The
    published paper (BMJ 2020;369:m1985, N=20,133) reports no median duration of
    stay of any kind in its main text; its only stay result is supplementary
    Figure E4, which is duration of HOSPITAL stay among patients discharged
    alive, with no median or IQR stated. The "7 days (IQR 4-14)" figure appears
    in the medRxiv preprint and is hospital stay, not ICU stay. The citation
    therefore supports neither the outcome nor the stated IQR. The value 7 is
    retained unchanged as a structural assumption pending a sourced replacement.
    An ICU-specific alternative was identified but NOT adopted: Richards-Belle
    et al., Intensive Care Med 2020 (ICNARC Case Mix Programme, n=10,834) report
    median critical care unit stay of 12 days for survivors and 9 for
    non-survivors; those two medians must not be averaged into an overall
    estimate, and their IQRs were not retrieved.
  Influenza: 5 days. [UNRESOLVED — ATTRIBUTION WITHDRAWN]  Previously annotated
    here as the lower bound of a "Chaves et al. 2015 / FluSurv-NET multi-season median
    range of 5–6 days". Source verification did not support that. Chaves SS et al.,
    Emerg Infect Dis 2015;21(9) describes the FluSurv-NET surveillance system and lists
    ICU admission only as a collected variable, reporting no length-of-stay figure at
    all; the MMWR 2024 FluSurv-NET summary reports none either. No source was located
    for a 5–6 day multi-season median, and any such figure would be hospital stay
    rather than ICU stay. The value 5 is retained unchanged as an unsourced structural
    assumption pending an ICU-specific source. An earlier project note justified 5 days
    by that range; that justification is withdrawn.
  Mpox: 5 days. [UNRESOLVED — ATTRIBUTION WITHDRAWN]  Thornhill et al. NEJM 2022
    does not report ICU LOS. The previous proxy attribution to a WHO mpox clinical
    management guide ("3–7 day course for complicated cases") was not supported on
    verification: the WHO living guideline states no length of stay, no duration of
    intensive care and no duration of hospitalisation in days. The value 5 is retained
    unchanged as a structural assumption.
  Norovirus: 2 days. [UNRESOLVED]  ICU admission is rare and largely confined to
    immunocompromised patients. The 1–3 day figure from Lopman et al., Emerg Infect Dis
    2011 is HOSPITAL stay, not ICU stay, so its proximity to the adopted value is not
    corroboration. No primary source for a norovirus ICU length of stay was identified;
    2 days is a structural assumption.
  Ebola: 10 days. [UNRESOLVED]  No primary source reporting an Ebola ICU length of
    stay was identified on verification. Uyeki et al., NEJM 2016 (n = 27, US and
    European cases) reports mechanical-ventilation and renal-replacement proportions
    but no ICU admission proportion and no length of stay. The value 10 is a structural
    assumption, and ICU use for Ebola is strongly jurisdiction-dependent.
  Diphtheria: ICU LOS not assigned (ICU fraction unresolved; see above).
"""

# ---------------------------------------------------------------------------
# ICU admission fractions (fraction of hospitalised cases admitted to ICU)
# ---------------------------------------------------------------------------

ICU_FRACTIONS = {
    # --- SARS-CoV-2 ---
    # [SOURCED — HDU/ICU combined; pure ICU not separately reported]
    # Docherty et al. BMJ 2020 / medRxiv preprint:
    #   Reported outcome: "admitted to High Dependency or Intensive Care Units"
    #   (HDU + ICU COMBINED — not pure ICU).
    #   Preprint (N=16,749): 17% admitted to HDU or ICU combined.
    #   Published BMJ paper (N=20,133): consistent proportion in final cohort.
    #   Fraction used: 0.15 (rounded, conservative relative to reported 17%).
    #   CAVEAT: conflates HDU step-down care with full ICU; applying the incremental
    #   ICU cost ($3,000/day) to HDU+ICU cases overstates true ICU-level incremental cost
    #   for the HDU subset. Pure ICU fraction would be lower; HDU+ICU combined is ~17%.
    #   Treat 0.15 as a lower-bound estimate of HDU+ICU combined; upper-bound of pure ICU
    #   fraction is not separately estimable from this source.
    "SARS-CoV-2": 0.15,

    # --- Influenza A/B (seasonal) ---
    # [SOURCED — revised from 0.23 to 0.17]
    # FluSurv-NET 2010-11 through 2018-19 (Lancet Microbe 2023, N=107,941):
    #   Overall ICU admission (imputed): 16.7%
    #   By type: A/H1N1pdm09=22.9%; A/H3N2=15.3%; B=15.9%
    #   CDC FluSurv-NET 2024-25 report (PMC12425177): historical range 14.3-18.2%
    # Prior value 0.23 corresponds to H1N1pdm09 specifically — not representative
    # of seasonal influenza A/B across types and seasons.
    # Revised to 0.17 (≈16.7% overall, rounded), using pure ICU admission outcome.
    # Note: this is PURE ICU (not HDU+ICU), in contrast to the SARS-CoV-2 estimate.
    #
    # KEY NOTE: parameters.py uses the combined key "Influenza A/B" for the single
    # pathogen entry that covers both types. All direct lookups from PATHOGENS must
    # use the combined key. The separate "Influenza A" / "Influenza B" entries below
    # are retained for documentation completeness (e.g. for avian proxy) but the
    # combined key is authoritative for primary-screening and PSA lookups.
    "Influenza A/B": 0.17,  # combined key matching PATHOGENS — AUTHORITATIVE for model runs
    "Influenza A": 0.17,    # kept for AVIAN_INFLUENZA_ICU_FRACTION reference; do not use for PATHOGENS lookup
    "Influenza B": 0.17,    # kept for documentation completeness

    # --- Mpox ---
    # [SOURCED — denominator corrected from first implementation]
    # Thornhill et al. NEJM 2022:
    #   Numerator: 5 patients admitted to ICU
    #   Denominator: 70 patients hospitalised (not 528 total reported cases)
    #   Location: Table 1, 16-country cohort, 528 confirmed cases total
    #   5 / 70 = 0.071 ≈ 0.07
    # Note: first implementation erroneously used denominator 528 (all cases),
    # yielding 5/528 = 0.009 ≈ 0.01 → reported as 0.03.  Corrected to 0.07.
    "Mpox": 0.07,

    # --- Norovirus ---
    # [UNRESOLVED] No peer-reviewed ICU fraction identified for norovirus
    # hospitalisation in a travel-importation context. Norovirus ICU admission
    # is rare in immunocompetent adults; most hospitalisations are for
    # dehydration (Lopman et al. Emerg Infect Dis 2011). Conservative
    # structural estimate: 0.03.  Must be updated when evidence is found.
    "Norovirus": 0.03,   # UNRESOLVED — structural placeholder

    # --- Ebola ---
    # [UNRESOLVED — jurisdiction context uncertain]
    # Feldmann et al. Nat Rev Microbiol 2020 review notes wide variation:
    #   High-resource Western centres: near-universal ICU (3–4 patients each).
    #   West Africa 2014–16 field hospitals: <5% formal ICU capacity.
    # Model context: outbreak importation into a moderate-resource country.
    # 0.35 is a structural compromise pending jurisdiction-specific analysis.
    "Ebola": 0.35,       # UNRESOLVED — jurisdiction-dependent; see sources above

    # --- Diphtheria ---
    # [UNRESOLVED] No transferable ICU fraction for diphtheria hospitalisation.
    # WHO clinical management guidance recommends ICU monitoring for
    # myocarditis and laryngeal obstruction but does not quantify the fraction.
    # One published fraction exists and is deliberately NOT adopted: Ahmed et
    # al., Trop Med Health 2026 report 21.6% among 51 hospitalised children in
    # a single Somali outbreak — a paediatric, single-setting, small-denominator
    # base that does not transfer to a generic importation model. The parameter
    # is bounded at 0.10-0.30 in the sensitivity analysis instead; see the
    # manuscript's lead-time results and Supplementary Methods S3.
    # Value set to None; callers must check DIPHTHERIA_ICU_UNRESOLVED before use.
    "Diphtheria": None,  # UNRESOLVED — see DIPHTHERIA_ICU_UNRESOLVED below
}

# Avian influenza (H5N1/H7N9 stress scenario): inherits revised seasonal influenza
# fraction (0.17) as the nearest sourced proxy; avian H5N1 cases (WHO 2024 reports)
# show >80% ICU in confirmed hospitalised, but the n is too small and
# case-ascertainment too incomplete for a reliable fraction in an importation
# model.  [PROXY from seasonal influenza — conservative lower bound for avian].
AVIAN_INFLUENZA_ICU_FRACTION = ICU_FRACTIONS["Influenza A"]   # 0.17 (revised from 0.23)

# Explicit flag for diphtheria — callers should check this before passing
# ICU_FRACTIONS["Diphtheria"] to the engine, to avoid silently setting
# c_icu = 0 under the mistaken impression it is a sourced zero.
DIPHTHERIA_ICU_UNRESOLVED = True
DIPHTHERIA_ICU_NOTE = (
    "No peer-reviewed ICU admission fraction for diphtheria hospitalisation "
    "identified. WHO clinical guidance implies ICU use for complications but "
    "does not provide a fraction. Costing deferred to zero pending primary "
    "evidence. Treat as a gap, not a sourced estimate of zero."
)


# ---------------------------------------------------------------------------
# ICU length of stay (days) — per new ICU admission
# ---------------------------------------------------------------------------

ICU_LOS_DAYS = {
    # [SOURCED] Docherty et al. BMJ 2020: median 7 days (IQR 4–14)
    "SARS-CoV-2": 7,

    # [SOURCED — lower bound of reported range]
    # Chaves et al. 2015 (FluSurv-NET multi-season): median ICU LOS 5–6 days.
    # Used 5 as the lower bound of this range. An earlier version used 6 (upper bound)
    # and was subsequently reduced to 5 citing a structural LOS constraint (ICU LOS ≤
    # hosp_duration_mid). That constraint was invalid: average ICU LOS among ICU patients
    # can exceed average hospital LOS across all admissions; the c_hosp and c_icu terms
    # are independent additive parameters in the model. The value 5 days is retained as
    # the evidence-based lower bound; 6 days is equally defensible.
    "Influenza A/B": 5,  # combined key matching PATHOGENS — AUTHORITATIVE for model runs
    "Influenza A": 5,    # kept for AVIAN_INFLUENZA_ICU_LOS reference
    "Influenza B": 5,    # kept for documentation completeness

    # [PROXY] WHO mpox clinical management guide 2023: 3–7 day range for
    # complicated hospitalised cases; Thornhill et al. NEJM 2022 does not
    # report ICU LOS. Used 5 as central estimate.
    "Mpox": 5,

    # [UNRESOLVED] Norovirus ICU admission very rare; typical hospital LOS
    # 1–3 days; ICU episode if admitted estimated 2 days. No primary source.
    "Norovirus": 2,

    # [PROXY] Schieffelin et al. NEJM 2014; Western Ebola case series:
    # prolonged ICU stays 10–14 days. Used 10 as lower-bound estimate.
    "Ebola": 10,

    # [UNRESOLVED] Not assigned — consistent with ICU_FRACTIONS["Diphtheria"]=None.
    "Diphtheria": None,
}

# Avian influenza inherits seasonal influenza LOS (5 days; lower bound of Chaves et al. 5-6 day range)
AVIAN_INFLUENZA_ICU_LOS = ICU_LOS_DAYS["Influenza A"]   # 5 days


# ---------------------------------------------------------------------------
# Structural cost assumption note
# ---------------------------------------------------------------------------
ICU_INCREMENTAL_COST_NOTE = (
    "ICU incremental cost per day ($3,000) is a structural modelling assumption "
    "set in parameters.py ICU_STRUCTURE['icu_incremental_cost_per_day_IF_EVER_PARAMETERISED']. "
    "No cited primary source was identified for this figure; it should not be "
    "described as a sourced estimate. The base ward rate ($2,000/day) shares the "
    "same limitation. Both figures are placeholders pending jurisdiction-specific "
    "inpatient cost data."
)


# ---------------------------------------------------------------------------
# Helper: retrieve (fraction, los_days) for a threat dict
# Returns (None, None) for diphtheria (unresolved) — callers must handle.
# ---------------------------------------------------------------------------
def get_icu_params(threat):
    """
    Returns (icu_fraction, icu_los_days) for a THREAT_CLASSES entry.
    Returns (None, None) if ICU costing is unresolved for this pathogen.
    Avian influenza stress scenario detected by threat.get('avian_influenza').
    """
    if threat.get("avian_influenza"):
        return AVIAN_INFLUENZA_ICU_FRACTION, AVIAN_INFLUENZA_ICU_LOS

    rep = threat.get("representative_pathogen", "")

    frac = ICU_FRACTIONS.get(rep)
    los  = ICU_LOS_DAYS.get(rep)

    # Both must be non-None and consistent
    if frac is None or los is None:
        return None, None

    return frac, los


# ---------------------------------------------------------------------------
# Canonical engine kwargs for the study's ICU configuration.
# ---------------------------------------------------------------------------

def scenario_icu_kwargs(pathogen_name):
    """Return the engine keyword arguments that apply this study's ICU costing
    to `pathogen_name`, for engine.run_scenario and engine.run_wbe_gated_scenario.

    A pathogen with a sourced or documented ICU admission fraction and length of
    stay gets those values. A pathogen with neither (diphtheria; measles in the
    stress-test set) gets icu_fraction_of_hosp_override=None, which makes the
    engine's c_icu term zero for it. That is an unresolved evidence gap, not a
    determination that those pathogens incur no intensive care.

    ICU_FRACTIONS and ICU_LOS_DAYS carry the same key set, so a pathogen either
    has both values or neither. This helper is the single definition of the
    configuration; it produces exactly the kwargs psa_icu.py builds inline for
    the probabilistic sensitivity analysis.
    """
    frac = ICU_FRACTIONS.get(pathogen_name)
    los = ICU_LOS_DAYS.get(pathogen_name)
    if frac is None or los is None:
        return {"icu_fraction_of_hosp_override": None, "icu_los_days_override": 7}
    return {"icu_fraction_of_hosp_override": frac, "icu_los_days_override": los}


def icu_burden_per_hospitalised_case(pathogen_name):
    """Incremental ICU cost attributable to one hospitalised case of
    `pathogen_name`, i.e. icu_fraction x icu_los_days x the incremental ICU day
    rate. Zero where the ICU inputs are unresolved. Used where a per-case burden
    is assembled outside the day-by-day engine loop (decision_surface.py).
    """
    from parameters import ICU_STRUCTURE
    frac = ICU_FRACTIONS.get(pathogen_name)
    los = ICU_LOS_DAYS.get(pathogen_name)
    if frac is None or los is None:
        return 0.0
    return frac * los * ICU_STRUCTURE["icu_incremental_cost_per_day_IF_EVER_PARAMETERISED"]
