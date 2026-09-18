"""
Publication-analysis engine.
Implements the model specified in manuscript_final.docx Supplementary Methods
(S1-S6), WITH TWO CORRECTIONS to the manuscript's own formulas, made after
scientific review per the user's explicit instruction to verify (not blindly
implement) the manuscript spec. Both corrections are documented here and in
CHANGELOG.md.

CORRECTION 1 (symptomatic gating): Supplementary Methods S3.3 and S3.4 define
C_hosp(t) = I(t) x h_rate x d_hosp x c_bed and C_prod(t) analogously, where
h_rate is explicitly defined (Table S1 header) as "% of SYMPTOMATIC cases"
hospitalised. Applying it directly to I(t) - the full infectious compartment,
symptomatic + asymptomatic - overstates hospital and productivity burden by
a factor of 1/symptomatic_fraction. This is exactly the P(hosp|infection) vs
P(hosp|symptomatic infection) confusion flagged in the original audit brief.
CORRECTED: C_hosp(t) = I(t) x symptomatic_fraction x h_rate x d_hosp x c_bed.

CORRECTION 2 (CFR vs IFR): Supplementary Methods S3.5 defines
C_mort(t) = I(t) x CFR x VSL. Table S1's CFR values are sourced from WHO fact
sheets, which report case-fatality among confirmed (overwhelmingly symptomatic)
cases, not infection-fatality across the full infected compartment. Applying
case-based CFR to I(t) (symptomatic+asymptomatic) systematically overstates
mortality burden for pathogens with large asymptomatic fractions.
CORRECTED: C_mort(t) = I(t) x symptomatic_fraction x CFR x VSL, treating the
manuscript's CFR values as fatality-among-symptomatic rather than re-deriving
true IFR values that are not available/sourced for most of these pathogens.
This is a conservative, explicit, documented modelling choice - not an
attempt to invent new parameter values.

Both corrections reduce absolute cost estimates versus a literal
implementation of the manuscript's stated formulas. They do NOT change which
pathogens are modelled, gamma, Rt, or any other input parameter.

CORRECTION 3 (countermeasure suppression - ADDITIVE, not in manuscript S1-S6):
The manuscript's Supplementary Methods S1.1 governing equations and S6
pseudocode hold Rt CONSTANT for the entire T=90-day horizon with no public-
health response term. Verified empirically: this produces mathematically
correct but scientifically implausible results (e.g. SARS-CoV-2, Rt=1.6, no
screening -> 49% cumulative attack rate and ~$570M/day hospital cost alone by
day 90), 3-4 orders of magnitude larger than the manuscript's own Table 1
figures for the same scenarios. No unmitigated real-world outbreak of a
sustained-Rt>1 pathogen is left completely unmanaged for 90 days; public
health systems respond. A countermeasure-suppression term was therefore
ADDED (this is a deviation from the literal manuscript text, done with the
user's explicit approval after reviewing the raw SIR trajectory) so that Rt
declines smoothly toward a controlled target after a response-detection
delay. This mirrors the mechanism the PRE-manuscript JS engine already had
(computeTimeVaryingTransmission in outbreak.js) which was dropped when the
Supplementary Methods were formalised for peer review - very plausibly an
unintentional omission rather than a deliberate modelling choice.
Parameters (response_delay_days=21, ramp_days=14, reduction_strength=0.6)
are STRUCTURAL ASSUMPTIONS, not manuscript-sourced, and are documented as
such in CHANGELOG.md and flagged for sensitivity analysis.

CORRECTION 4 (incidence-based costing, not stock-based - fixes QC test 8/9
failure): Supplementary Methods S3.3-S3.5 define C_hosp(t), C_prod(t), and
C_mort(t) as functions of I(t), the STANDING infectious stock. Verified
empirically: this charges every hospitalisation/productivity/mortality cost
to the same case on EVERY day that case remains infectious (~4-28 days
depending on pathogen), i.e. a 3.5%-CFR pathogen with an 8-day infectious
period would have ~8x too much mortality cost attributed to it. This is
precisely the double-counting error the user's QC checklist (items 8-9)
explicitly requires be excluded. CORRECTED: health-economic costs are now
attributed to DAILY INCIDENCE (new infections entering I that day = domestic
transmission flow + imported flow), not to the standing stock I(t). This is
standard practice in dynamic-transmission cost-effectiveness models (each
case's downstream cost is counted once, at the time of infection).

CORRECTION 6 (cumulative-infection accounting, added during post-submission
methodological audit, Issue 1): the model retains an OPEN-POPULATION
importation formulation -- dS/dt = -beta*S*I/N, dI/dt = beta*S*I/N - gamma*I
+ Lambda, dR/dt = gamma*I, with Lambda added to I but NOT subtracted from S,
and N held fixed as the transmission denominator throughout. This means
S+I+R drifts upward from N over the horizon by an amount equal to
cumulative Lambda (verified: +0.000014% to +0.004104% of N across the six
primary pathogens at baseline prevalence over 90 days -- negligible relative
to N, and confirmed to have no material effect, <0.005% in every case, on
total societal cost or on which strategy is cost-minimising). This
open-population choice is retained deliberately: imported infectious
travellers are genuinely new arrivals to the downstream catchment
population, not conversions of pre-existing local susceptibles, so it is
scientifically appropriate that they enter I without first being drawn from
S. HOWEVER, this formulation means the previously used
`cumulative_infections = N - S` metric silently EXCLUDED imported
infections from the reported case count, because those individuals never
depleted S. CORRECTED: cumulative_infections is now an explicit running sum
of daily incidence (domestic transmission-caused depletion of S, plus
imported arrivals Lambda) accumulated once per day, with no double-counting
(verified against an independent closed-population diagnostic
cross-check). This changes reported cumulative-infection and
cases-averted-vs-no-screening figures (by 9.6-27.6% at baseline prevalence,
except Norovirus at -0.02%, where the epidemic is large enough that the
correction is negligible in relative terms) but does NOT change total
societal cost, deaths, or the cost-minimising strategy for any pathogen,
since those were already correctly computed from the same
incidence-inclusive-of-Lambda quantity before this correction.

CORRECTION 7 (WBE rebuild -- aircraft-level analytical gate, replacing the
prior flat-cost placeholder): the previously implemented WBE mechanism
(dead `Se_wbe = 0.95` variable, a bare `wbe_threshold = 0.001` prevalence
cutoff, and a flat `c_wbe` daily surcharge added on top of universal
molecular screening) did not implement a gate at all -- it never changed
`n_test`, never reduced screening volume, and never affected missed
infections. It has been REMOVED in full (including the dead sensitivity
constant and the 0.1% threshold) and replaced with `wbe_gate_flow()` and
`run_wbe_gated_scenario()` below, implementing WBE as a genuine aircraft-
level surveillance GATE that determines whether a flight's passengers
receive targeted individual follow-up testing -- not a standalone
diagnostic modality, not a cost layered on universal screening, and not an
early-warning/lead-time mechanism (no detection-lag or earlier-
countermeasure-activation logic exists anywhere in this rebuild).

Architecture (single authoritative analytical pathway; no discrete
per-flight stochastic simulation, no RNG, no duplicated code path -- this
is a deliberate response to the archived JS simulator's RNG-desynchronisation
parity bug documented in WBE_PARITY_REPORT.md):

  - Daily arrivals are converted to an expected flights/day figure via
    `avg_pax_per_flight` (WBE_PARAMS). Tier passenger share f_k (ROUTE_TIERS)
    is reused as tier flight-share (equal average aircraft occupancy across
    tiers is an explicit simplifying assumption, not tier-specific data).
  - Expected infected-passenger burden per flight, tier k:
        lambda_k = avg_pax_per_flight * p0 * m_k * phi
    `phi` (the model's existing infectiousness/detectable-window fraction,
    unchanged in meaning) is RETAINED here so the WBE arm is evaluated
    against the identical epidemiological denominator as the RAT/PCR/
    molecular arms -- infected-but-not-currently-infectious passengers are
    excluded from Lambda everywhere in this model, WBE included, because
    they cannot seed transmission, not because of any diagnostic modality's
    reach.
  - Burden-dependent true-signal probability (infected passengers modelled
    as N ~ Poisson(lambda_k); a flight is genuinely WBE-positive if at
    least one infected passenger's contribution registers, each
    independently with probability q):
        P_true_signal_k = 1 - exp(-lambda_k * q)
    q = wbe_detection_prob_per_infected_passenger (WBE_PARAMS) is an
    explicit, swept, NOT-assumed-validated parameter -- it is NOT the
    historical flight-level 0.88/0.95 sensitivity figures, and it does NOT
    replace phi; q operates only on the phi-eligible infectious population.
  - False positives are represented as P(false-positive flag | no genuine
    detectable signal occurred), NOT P(false positive | zero infected
    passengers) -- these differ, because a truly infected flight can also
    fail to generate a genuine signal (probability (1-q)^n) and still be
    caught by the false-positive mechanism:
        P_flag_k = 1 - (1 - wbe_false_positive_rate) * exp(-lambda_k * q)
    Variable name is `wbe_false_positive_rate`, not `phi_fp`, since `phi`
    already has a distinct, unrelated epidemiological meaning in this model.
  - Expected infected passengers aboard flagged flights (closed form, via
    the Poisson probability-generating function; independently re-derived
    and verified, not accepted on assertion -- see WBE_REBUILD.md and the
    accompanying test suite for the full derivation):
        Infected_flagged_k = flights_per_day_k * lambda_k *
            [1 - (1-wbe_false_positive_rate)*(1-q)*exp(-lambda_k*q)]
  - Follow-up testing volume, TP/FP, and missed infections are all computed
    from this flagged-flight COMPOSITION (both infected and uninfected
    passengers aboard flagged flights), not from population-average
    prevalence applied to the follow-up-tested count -- see
    `wbe_gate_flow()` for the exact formulas.
  - Missed infected passengers (gate misses + follow-up misses, shown
    algebraically equivalent to `Infected_total_k - TP_followup_k` in
    WBE_REBUILD.md) are summed across tiers into `Lambda_WBE(t)` and fed
    into the SAME `sir_rk4_step()` used by every other strategy -- there is
    no separate WBE transmission model.
  - Programme cost is `flights_per_day * wbe_cost_per_sample` (one pooled
    sample per arriving flight, an explicit initial assumption) plus
    `n_followup * cost_per_test(follow_up_modality)` -- follow-up testing
    cost is incurred ONLY for passengers on flagged flights. No universal-
    screening cost is applied to passengers who were never flagged.

All WBE_PARAMS values are explicitly labelled placeholders (see
parameters.py), not validated aircraft-level performance figures. No
headline WBE cost-effectiveness result should be generated from these
defaults; they exist to make the gate architecture runnable and testable
ahead of a dedicated threshold/breakeven sweep.

CORRECTION 17 (analysis horizon extended 90 -> 365 days, requested revision):
ECON["horizon_days"] changed from 90 to 365 (parameters.py); both
`run_scenario()` and `run_wbe_gated_scenario()` read this single value as
their loop bound (`for t in range(1, horizon_days + 1)`), so no other code
change was required to propagate the extension. This was done to directly
test whether the 90-day base case's cost-minimising strategy and reported
infection/death reductions partly reflect infections displaced beyond the
horizon rather than permanently averted (see the horizon-sensitivity
diagnostic preceding this correction). Three things are explicitly NOT
changed as part of this correction, each a scientific decision rather than
a mechanical one:
  (a) Importation prevalence (p0) is still held CONSTANT for the full
      horizon by `daily_importation_rate()`. This was already a
      simplification at 90 days; holding source-country prevalence fixed
      for a full year is a materially stronger assumption, not introduced
      or validated here, and is flagged as a limitation (Section 4.8)
      rather than replaced with time-varying prevalence, which is out of
      scope for this revision.
  (b) `time_varying_rt()` is unchanged: once its smoothstep activation
      reaches 1 (response_delay_days + ramp_days after simulation start),
      the countermeasure-suppressed Rt is held at that constant reduced
      level for the REMAINDER of the horizon, with no waning, relaxation,
      or policy-fatigue term. At 90 days this meant sustained suppression
      for roughly the final 55 days; at 365 days it means sustained
      suppression for roughly the final 330 days -- a substantially
      stronger real-world claim, since no actual public-health response is
      held at constant strength for a year. Not modelled here; flagged as
      a limitation and discussed against the supplied literature on
      real-world intervention timing/ramp-up (Section 4.2).
  (c) The base-case countermeasure parameters themselves
      (response_delay_days=21, ramp_days=14, reduction_strength=0.6) are
      UNCHANGED from the 90-day analysis, specifically so that this
      correction isolates the effect of the horizon extension alone. The
      manuscript's prior justification for these values ("shortened...to
      remain meaningful within this analysis's 90-day horizon") no longer
      applies at 365 days and has been removed/recontextualised in
      Section 2.5 using the supplied literature and the existing swept
      sensitivity range (countermeasure_sensitivity.csv), not by silently
      reverting to the pre-publication engine's 60-day/21-day defaults.
`countermeasure_sensitivity.csv` additionally gains explicit "no
countermeasure" rows (apply_countermeasures=False, i.e. Rt(t)=Rt0 for
every t, using the same simulation pipeline and initial conditions as
every other row), labelled via a `countermeasure_status` column rather
than left as blank/missing trigger-day or ramp-day fields.
"""

import numpy as np
from parameters import (
    PATHOGENS, ROUTE_TIERS, N_TOTAL_ARRIVALS_PER_DAY, DOWNSTREAM_POPULATION,
    MODALITIES, ECON, WBE_PARAMS, ICU_STRUCTURE, mid,
)


def compute_downstream_health_costs(incidence_today, symptomatic_fraction, hosp_rate,
                                     hosp_duration, CFR, vsl,
                                     mortality_already_infection_based=False,
                                     icu_fraction_of_hosp_override=None,
                                     icu_los_days_override=7):
    """
    SHARED downstream health-cost calculation (hospitalisation, productivity,
    mortality, ICU), used identically by run_scenario() and
    run_wbe_gated_scenario() (post-CORRECTION-7-cleanup). Previously this
    logic was duplicated inline in both functions; the ICU term specifically
    contained a pre-existing latent bug (referencing ECON["ICU_STRUCTURE"],
    which was never actually merged into ECON) that the WBE-rebuild copy
    patched defensively while the original was left unpatched -- an
    asymmetry between the two pathways. Both now call this single function,
    which references the correct top-level `ICU_STRUCTURE` import. Since
    `icu_fraction_of_hosp_override` is None in every currently exercised
    scenario (no caller anywhere in this package passes a non-None value),
    c_icu remains exactly 0.0 in both pathways for every currently exercised
    scenario -- this refactor changes no numerical output, only removes the
    asymmetry and the latent crash risk (verified by the full regression
    diff in the accompanying report).

    Formulas are Corrections 1, 2, 4, 5 (see module docstring), unchanged:
      c_hosp = incidence x symptomatic_fraction x hosp_rate x hosp_duration x c_bed
      c_prod = incidence x symptomatic_fraction x hosp_rate x hosp_duration x w_avg x (1+epsilon)
      c_mort = incidence x mortality_symptomatic_gate x CFR x VSL
      c_icu  = icu_cases x icu_los_days x icu_incremental_cost_per_day, if icu_fraction given, else 0

    Targeted change (ICU LOS configurable, 2026-09): `icu_los_days_override` replaces the
    previously hard-coded literal 7. Default=7 preserves backward-compatible outputs
    when called without this argument. Setting icu_fraction_of_hosp_override=None (the
    default) still yields c_icu=0.0 regardless of icu_los_days_override, reproducing
    all pre-ICU outputs exactly.

    Cost structure (parameters.py):
      c_bed_per_day = $2,000 applied to ALL hospitalised cases (ward rate, all bed-days).
      icu_incremental_cost_per_day = $3,000 applied to ICU subset x ICU LOS only (additive;
      no double-counting since c_hosp already covers the full ward-rate episode).
      Note: both figures are structural modelling assumptions, not jurisdiction-specific
      observed inpatient costs — see parameters.py ICU_STRUCTURE comment.
    """
    c_hosp = incidence_today * symptomatic_fraction * hosp_rate * hosp_duration * ECON["c_bed_per_day"]
    c_prod = incidence_today * symptomatic_fraction * hosp_rate * hosp_duration * ECON["w_avg_per_day"] * (1 + ECON["epsilon_friction"])
    mortality_symptomatic_gate = 1.0 if mortality_already_infection_based else symptomatic_fraction
    c_mort = incidence_today * mortality_symptomatic_gate * CFR * vsl
    if icu_fraction_of_hosp_override is not None:
        icu_cases_today = incidence_today * symptomatic_fraction * hosp_rate * icu_fraction_of_hosp_override
        c_icu = icu_cases_today * icu_los_days_override * ICU_STRUCTURE["icu_incremental_cost_per_day_IF_EVER_PARAMETERISED"]
    else:
        c_icu = 0.0
    return c_hosp, c_prod, c_mort, c_icu


def smoothstep01(x):
    t = max(0.0, min(1.0, x))
    return t * t * (3 - 2 * t)


def time_varying_rt(Rt0, day, response_delay_days=21, ramp_days=14, reduction_strength=0.6):
    """CORRECTION 3 (additive, see module docstring). Countermeasure ramp:
    Rt declines smoothly from Rt0 toward Rt0*(1-reduction_strength) starting
    response_delay_days after day 0, over ramp_days."""
    target_rt = max(0.3, Rt0 * (1 - reduction_strength))
    x = (day - response_delay_days) / ramp_days
    activation = smoothstep01(x)
    return Rt0 - activation * (Rt0 - target_rt)


def weighted_avg_multiplier(route_tiers=ROUTE_TIERS):
    return sum(v["share"] * v["multiplier"] for v in route_tiers.values())


def daily_importation_rate(p0_frac, phi_frac, sensitivity, route_targeted=False,
                            route_tiers=ROUTE_TIERS, n_total=N_TOTAL_ARRIVALS_PER_DAY):
    """Lambda(t): manuscript Supplementary Methods S2.3 / S4.1-S4.2."""
    if route_targeted:
        high = route_tiers["high"]
        return n_total * high["multiplier"] * p0_frac * phi_frac * (1 - sensitivity)
    else:
        wavg = weighted_avg_multiplier(route_tiers)
        return n_total * wavg * p0_frac * phi_frac * (1 - sensitivity)


def sir_rk4_step(S, I, R, beta, gamma, lam, N, dt=1.0):
    def deriv(S, I, R):
        dS = -beta * S * I / N
        dI = beta * S * I / N - gamma * I + lam
        dR = gamma * I
        return dS, dI, dR

    k1 = deriv(S, I, R)
    k2 = deriv(S + dt / 2 * k1[0], I + dt / 2 * k1[1], R + dt / 2 * k1[2])
    k3 = deriv(S + dt / 2 * k2[0], I + dt / 2 * k2[1], R + dt / 2 * k2[2])
    k4 = deriv(S + dt * k3[0], I + dt * k3[1], R + dt * k3[2])

    S_new = S + dt / 6 * (k1[0] + 2 * k2[0] + 2 * k3[0] + k4[0])
    I_new = I + dt / 6 * (k1[1] + 2 * k2[1] + 2 * k3[1] + k4[1])
    R_new = R + dt / 6 * (k1[2] + 2 * k2[2] + 2 * k3[2] + k4[2])

    S_new = max(0.0, S_new)
    I_new = max(0.0, I_new)
    R_new = max(0.0, R_new)
    # CORRECTION 4: incidence = domestic new infections this step (S depletion)
    # + imported infections (lam). Used for incidence-based cost attribution.
    domestic_incidence = max(0.0, S - S_new)
    incidence_today = domestic_incidence + lam
    return S_new, I_new, R_new, incidence_today


def run_scenario(pathogen_params, modality_key, prevalence_multiplier=1.0,
                  route_targeted=False,
                  sensitivity_override=None, cfr_override=None,
                  rt_override=None, gamma_override=None,
                  symptomatic_fraction_override=None,
                  hosp_rate_override=None, hosp_duration_override=None,
                  phi_override=None, prevalence_override=None,
                  vsl=ECON["VSL_base_case"], sensitivity_specificity_pair=None,
                  n_total=N_TOTAL_ARRIVALS_PER_DAY, N=DOWNSTREAM_POPULATION,
                  horizon_days=ECON["horizon_days"], discount_rate_annual=ECON["discount_rate_annual"],
                  discount_start_day=ECON["discount_start_day"], apply_countermeasures=True,
                  cm_response_delay_days=21, cm_ramp_days=14, cm_reduction_strength=0.6,
                  mortality_already_infection_based=False, icu_fraction_of_hosp_override=None,
                  icu_los_days_override=7, cost_per_test_override=None):
    """
    Deterministic (or single Monte-Carlo draw) run of one pathogen x modality
    x prevalence-tier scenario. Returns a dict of all QC / master-dataset
    fields required by Task 4.

    icu_los_days_override: ICU length of stay in days per new admission (default=7,
      backward-compatible). Only used when icu_fraction_of_hosp_override is not None.

    cost_per_test_override: per-test unit cost (currency units) for the screening
      modality. Targeted change (test-cost uncertainty, 2026-09): when None (the
      default) the midpoint of MODALITIES[modality_key]["cost_per_test_range"] is
      used exactly as before, so every existing deterministic call reproduces its
      previous output bit-for-bit. When supplied (e.g. a PSA Gamma draw) it replaces
      the midpoint in the programme-cost term c_prog = n_test x cost_per_test.
      It affects ONLY screening_cost and, through it, total_societal_cost; it enters
      no epidemiological term, so infections, hospitalisations, deaths and all
      health-outcome costs are invariant to it. For modality_key == "none" the
      programme cost is zero regardless (there is no test to price), and the
      override is ignored.
    """
    p = pathogen_params
    if mortality_already_infection_based is False and p.get("mortality_already_infection_based"):
        mortality_already_infection_based = True
    Rt = rt_override if rt_override is not None else mid(*p["Rt_range"])
    infectious_days = mid(*p["infectious_period_range"])
    gamma = gamma_override if gamma_override is not None else (1.0 / infectious_days)
    CFR = (cfr_override if cfr_override is not None else mid(*p["CFR_pct_range"])) / 100.0
    hosp_rate = (hosp_rate_override if hosp_rate_override is not None else mid(*p["hosp_rate_pct_range"])) / 100.0
    hosp_duration = hosp_duration_override if hosp_duration_override is not None else mid(*p["hosp_duration_days_range"])
    symptomatic_fraction = (symptomatic_fraction_override if symptomatic_fraction_override is not None
                             else mid(*p["symptomatic_fraction_pct_range"]) / 100.0)
    phi = (phi_override if phi_override is not None else mid(*p["detectable_at_arrival_pct_range"]) / 100.0)
    p0 = (prevalence_override if prevalence_override is not None
          else p["baseline_prevalence_pct"] / 100.0) * prevalence_multiplier

    mod = MODALITIES[modality_key]
    if sensitivity_specificity_pair is not None:
        sensitivity, specificity = sensitivity_specificity_pair
    else:
        sensitivity = sensitivity_override if sensitivity_override is not None else mid(*mod["sensitivity_range"])
        specificity = mid(*mod["specificity_range"])
    cost_per_test = (cost_per_test_override if cost_per_test_override is not None
                     else mid(*mod["cost_per_test_range"]))

    beta = Rt * gamma
    lam0 = daily_importation_rate(p0, phi, sensitivity, route_targeted=route_targeted, n_total=n_total)

    S = N - lam0
    I = lam0
    R = 0.0

    r_daily = discount_rate_annual / 365.0
    total_cost = 0.0
    total_prog = total_hosp = total_prod = total_mort = total_icu = 0.0
    cum_infections = 0.0
    cum_hosp_cases = 0.0
    cum_deaths = 0.0
    true_pos_cum = false_pos_cum = 0.0

    daily_deaths_undiscounted = 0.0
    daily_hosp_cases_undiscounted = 0.0
    for t in range(1, horizon_days + 1):
        lam = daily_importation_rate(p0, phi, sensitivity, route_targeted=route_targeted, n_total=n_total)
        Rt_today = time_varying_rt(Rt, t, response_delay_days=cm_response_delay_days,
                                    ramp_days=cm_ramp_days, reduction_strength=cm_reduction_strength) if apply_countermeasures else Rt
        beta_today = Rt_today * gamma
        S, I, R, incidence_today = sir_rk4_step(S, I, R, beta_today, gamma, lam, N)

        if route_targeted:
            n_test = n_total * ROUTE_TIERS["high"]["share"]
        else:
            n_test = n_total

        c_prog = n_test * cost_per_test * (1.0 if modality_key != "none" else 0.0)

        # --- CORRECTED cost terms (Corrections 1, 2, 4, 5 - see module docstring) ---
        # Costs attributed to today's INCIDENT cases (Correction 4).
        # Hospitalisation/productivity: symptomatic-gated for all pathogens
        # (Table S1 header "% symptomatic" is unambiguous -- HIGH confidence).
        # CORRECTION 5 (denominator audit, SARS-CoV-2 mortality only): the
        # manuscript's SARS-CoV-2 CFR range (0.1-1.4%) sits inside published
        # infection-fatality-ratio estimates (e.g. Meyerowitz-Katz & Merone
        # 2020 pooled IFR ~0.68%, cited by peer review as the standard
        # reference), not typical pandemic-era case-based CFR figures (which
        # ran far higher, 1-7%+, under limited testing). This suggests the
        # source value is already infection-based for SARS-CoV-2 specifically,
        # so symptomatic-gating it again would double-correct. For the other
        # 5 primary pathogens, CFR is judged case/symptomatic-based with HIGH
        # confidence (see DENOMINATOR_AUDIT.md) and IS gated. This is an
        # inference, not a certainty -- flagged, reversible if the
        # manuscript's actual cited references [1,2,3] are consulted directly.
        # ICU (adversarial-audit addition): structure present, base-case
        # increment is $0 for all 6 primary pathogens (no pathogen-specific
        # ICU-fraction/duration data in Table S1). icu_fraction_of_hosp_override
        # is None in the base case (and every currently exercised scenario).
        # See compute_downstream_health_costs() -- SHARED with
        # run_wbe_gated_scenario() as of the WBE-rebuild cleanup pass.
        c_hosp, c_prod, c_mort, c_icu = compute_downstream_health_costs(
            incidence_today, symptomatic_fraction, hosp_rate, hosp_duration, CFR, vsl,
            mortality_already_infection_based=mortality_already_infection_based,
            icu_fraction_of_hosp_override=icu_fraction_of_hosp_override,
            icu_los_days_override=icu_los_days_override,
        )

        c_t = c_prog + c_hosp + c_prod + c_mort + c_icu

        if t > discount_start_day:
            disc_days = t - discount_start_day
            discount_factor = 1.0 / ((1 + r_daily) ** disc_days)
        else:
            discount_factor = 1.0

        total_cost += c_t * discount_factor
        total_prog += c_prog * discount_factor
        total_hosp += c_hosp * discount_factor
        total_prod += c_prod * discount_factor
        total_mort += c_mort * discount_factor
        total_icu += c_icu * discount_factor

        # CORRECTION 8 (deaths/mortality-cost denominator consistency,
        # final-locked-model audit Finding 1): deaths must use the SAME
        # mortality_gate convention as c_mort in compute_downstream_health_costs()
        # above -- gate=1.0 when CFR is already infection-based (SARS-CoV-2,
        # Influenza A/B), gate=symptomatic_fraction otherwise. Previously this
        # line always applied symptomatic_fraction regardless of
        # mortality_already_infection_based, silently undercounting deaths by
        # a factor of symptomatic_fraction for the two infection-based-CFR
        # pathogens (verified: SARS-CoV-2 baseline molecular scenario reported
        # 8.22 deaths vs. ~12.65 implied by its own mortality cost). See
        # FINAL_MODEL_AUDIT.md / chat record for the audit finding.
        mortality_gate_for_deaths = 1.0 if mortality_already_infection_based else symptomatic_fraction
        daily_deaths_undiscounted += incidence_today * mortality_gate_for_deaths * CFR
        daily_hosp_cases_undiscounted += incidence_today * symptomatic_fraction * hosp_rate
        true_pos_cum += n_test * sensitivity * p0 if modality_key != "none" else 0.0
        false_pos_cum += n_test * (1 - specificity) * (1 - p0) if modality_key != "none" else 0.0

        # CORRECTION 6 (cumulative-infection accounting, Issue 1 audit):
        # incidence_today already equals (domestic transmission-caused
        # depletion of S) + (imported arrivals, lam) -- see sir_rk4_step,
        # where lam is added to I but NOT subtracted from S (the retained
        # open-population importation formulation; see engine docstring and
        # manuscript Section 2.4). Summing incidence_today over the horizon
        # therefore counts every new infection exactly once, whether
        # domestically transmitted or imported, with no double-counting.
        # This REPLACES the prior `cum_infections = N - S` metric, which
        # silently excluded imported infections because they never deplete S
        # under the open-population formulation, undercounting cumulative
        # infections by up to ~28% for some pathogens at baseline prevalence
        # (verified by cross-check against an independent closed-population
        # diagnostic formulation; see chat record of this audit).
        cum_infections += incidence_today

    cum_hosp_cases = daily_hosp_cases_undiscounted
    cum_deaths = daily_deaths_undiscounted

    return {
        "Rt": Rt, "gamma": gamma, "infectious_period_days": infectious_days,
        "CFR_pct": CFR * 100, "hosp_rate_pct": hosp_rate * 100,
        "symptomatic_fraction_pct": symptomatic_fraction * 100,
        "sensitivity": sensitivity, "specificity": specificity,
        "cost_per_test": cost_per_test, "prevalence_frac": p0,
        "route_targeted": route_targeted,
        "final_S": S, "final_I": I, "final_R": R,
        "true_positives_cum": true_pos_cum, "false_positives_cum": false_pos_cum,
        "cumulative_infections": cum_infections, "cumulative_hosp_cases": cum_hosp_cases,
        "cumulative_deaths": cum_deaths,
        "screening_cost": total_prog, "hospital_cost": total_hosp,
        "productivity_cost": total_prod, "mortality_cost": total_mort, "icu_cost": total_icu,
        "total_societal_cost": total_cost,
    }


# ===========================================================================
# WBE GATE (CORRECTION 7) -- single authoritative analytical implementation.
# See module docstring for the full architecture description and the
# derivation of every formula below (independently re-derived and verified
# across the design conversation preceding this implementation; also see
# WBE_REBUILD.md and test_wbe_gate.py).
# ===========================================================================

def wbe_gate_flow(p0, phi, avg_pax_per_flight, wbe_detection_prob,
                   wbe_false_positive_rate, follow_up_coverage,
                   follow_up_sensitivity, follow_up_specificity,
                   n_total=N_TOTAL_ARRIVALS_PER_DAY, route_tiers=ROUTE_TIERS):
    """
    THE single authoritative WBE gate computation. Called both to initialise
    day-0 state and inside the daily loop of run_wbe_gated_scenario() -- one
    function, one formula set, no duplicated/parallel implementation (this
    is the direct, deliberate response to the archived JS simulator's
    RNG-desynchronisation parity bug: there is nothing here to desynchronise,
    since there is no RNG and no second code path).

    Per tier k (route_tiers): infected-passenger burden per flight,
        lambda_k = avg_pax_per_flight * p0 * m_k * phi
    (phi retained -- see module docstring CORRECTION 7 -- so this arm shares
    the identical epidemiological denominator with the RAT/PCR/molecular
    arms; only currently-infectious/phi-eligible passengers are represented,
    consistent with the rest of this model.)

    N_infected_on_flight ~ Poisson(lambda_k). A flight is genuinely
    WBE-positive if at least one infected passenger's shedding contribution
    registers, each independently with probability
    wbe_detection_prob ("q"):
        P_true_signal_k = 1 - exp(-lambda_k * q)
    False positives are P(flag+ | no genuine signal occurred), not
    P(flag+ | zero infected passengers):
        P_flag_k = 1 - (1 - wbe_false_positive_rate) * exp(-lambda_k * q)
    Expected infected passengers aboard flagged flights (closed form via the
    Poisson probability-generating function):
        Infected_flagged_k = flights_per_day_k * lambda_k *
            [1 - (1-wbe_false_positive_rate)*(1-q)*exp(-lambda_k*q)]

    Returns per-day, SUMMED-ACROSS-TIERS quantities:
        lam                 : missed infected passengers/day (feeds SIR lam)
        n_followup          : passengers/day receiving follow-up testing
        true_positives      : follow-up true positives/day
        false_positives     : follow-up false positives/day
        flights_per_day     : total flights/day (for sampling cost)
        infected_total      : total truly-infected arrivals/day (QC/reporting)
        infected_flagged    : total infected arrivals/day on flagged flights (QC/reporting)
    """
    q = wbe_detection_prob
    flights_per_day = n_total / avg_pax_per_flight

    lam_total = 0.0
    n_followup_total = 0.0
    tp_total = 0.0
    fp_total = 0.0
    infected_total_all = 0.0
    infected_flagged_all = 0.0

    for tier in route_tiers.values():
        f_k = tier["share"]
        m_k = tier["multiplier"]
        flights_per_day_k = flights_per_day * f_k

        lambda_k = avg_pax_per_flight * p0 * m_k * phi

        exp_neg_lambda_q = np.exp(-lambda_k * q)
        P_flag_k = 1.0 - (1.0 - wbe_false_positive_rate) * exp_neg_lambda_q

        Infected_total_k = flights_per_day_k * lambda_k
        Infected_flagged_k = flights_per_day_k * lambda_k * (
            1.0 - (1.0 - wbe_false_positive_rate) * (1.0 - q) * exp_neg_lambda_q
        )

        Total_flagged_passengers_k = n_total * f_k * P_flag_k
        Uninfected_flagged_k = max(0.0, Total_flagged_passengers_k - Infected_flagged_k)

        n_followup_k = follow_up_coverage * Total_flagged_passengers_k
        TP_followup_k = follow_up_coverage * Infected_flagged_k * follow_up_sensitivity
        FP_followup_k = follow_up_coverage * Uninfected_flagged_k * (1.0 - follow_up_specificity)

        Missed_k = Infected_total_k - TP_followup_k

        lam_total += Missed_k
        n_followup_total += n_followup_k
        tp_total += TP_followup_k
        fp_total += FP_followup_k
        infected_total_all += Infected_total_k
        infected_flagged_all += Infected_flagged_k

    return {
        "lam": max(0.0, lam_total),
        "n_followup": n_followup_total,
        "true_positives": tp_total,
        "false_positives": fp_total,
        "flights_per_day": flights_per_day,
        "infected_total": infected_total_all,
        "infected_flagged": infected_flagged_all,
    }


def run_wbe_gated_scenario(pathogen_params, follow_up_modality_key, prevalence_multiplier=1.0,
                            wbe_detection_prob=None, wbe_false_positive_rate=None,
                            follow_up_coverage=None, avg_pax_per_flight=None,
                            wbe_cost_per_sample=None, cost_per_test_override=None,
                            sensitivity_override=None, cfr_override=None,
                            rt_override=None, gamma_override=None,
                            symptomatic_fraction_override=None,
                            hosp_rate_override=None, hosp_duration_override=None,
                            phi_override=None, prevalence_override=None,
                            vsl=ECON["VSL_base_case"],
                            n_total=N_TOTAL_ARRIVALS_PER_DAY, N=DOWNSTREAM_POPULATION,
                            horizon_days=ECON["horizon_days"], discount_rate_annual=ECON["discount_rate_annual"],
                            discount_start_day=ECON["discount_start_day"], apply_countermeasures=True,
                            cm_response_delay_days=21, cm_ramp_days=14, cm_reduction_strength=0.6,
                            mortality_already_infection_based=False, icu_fraction_of_hosp_override=None,
                            icu_los_days_override=7, route_tiers=ROUTE_TIERS):
    """
    WBE-gated strategy: aircraft-level wastewater gate triggers targeted
    individual follow-up testing (follow_up_modality_key: "rapid", "lab", or
    "molecular", reusing the SAME MODALITIES sensitivity/specificity/cost
    values as the standalone strategies -- no separately invented follow-up
    diagnostic performance). NOT a standalone modality, NOT a surcharge on
    universal screening: n_test for the general population does not exist in
    this function at all -- only n_followup (passengers on flagged flights).

    NO early-warning/lead-time mechanism: apply_countermeasures/
    cm_response_delay_days/cm_ramp_days/cm_reduction_strength behave
    IDENTICALLY to run_scenario -- WBE has no effect on countermeasure
    timing anywhere in this function.

    Pathogen/econ parameter resolution mirrors run_scenario() exactly
    (duplicated intentionally, not refactored into a shared helper, so that
    run_scenario()'s existing behaviour for the four standalone strategies
    is provably untouched by this addition). The daily SIR update and the
    hospitalisation/productivity/mortality/ICU cost formulas are the
    IDENTICAL formulas used in run_scenario() (Corrections 1, 2, 4, 5),
    applied to incidence_today from the SAME sir_rk4_step() function -- no
    separate transmission or downstream-cost model.
    """
    p = pathogen_params
    if not p.get("wbe_applicable", False):
        raise ValueError(f"Pathogen is not wbe_applicable; WBE-gated scenario not defined for this pathogen.")

    wp = WBE_PARAMS
    wbe_detection_prob = wbe_detection_prob if wbe_detection_prob is not None else wp["wbe_detection_prob_per_infected_passenger"]
    wbe_false_positive_rate = wbe_false_positive_rate if wbe_false_positive_rate is not None else wp["wbe_false_positive_rate"]
    follow_up_coverage = follow_up_coverage if follow_up_coverage is not None else wp["follow_up_coverage"]
    avg_pax_per_flight = avg_pax_per_flight if avg_pax_per_flight is not None else wp["avg_pax_per_flight"]
    wbe_cost_per_sample = wbe_cost_per_sample if wbe_cost_per_sample is not None else wp["wbe_cost_per_sample"]

    if mortality_already_infection_based is False and p.get("mortality_already_infection_based"):
        mortality_already_infection_based = True
    Rt = rt_override if rt_override is not None else mid(*p["Rt_range"])
    infectious_days = mid(*p["infectious_period_range"])
    gamma = gamma_override if gamma_override is not None else (1.0 / infectious_days)
    CFR = (cfr_override if cfr_override is not None else mid(*p["CFR_pct_range"])) / 100.0
    hosp_rate = (hosp_rate_override if hosp_rate_override is not None else mid(*p["hosp_rate_pct_range"])) / 100.0
    hosp_duration = hosp_duration_override if hosp_duration_override is not None else mid(*p["hosp_duration_days_range"])
    symptomatic_fraction = (symptomatic_fraction_override if symptomatic_fraction_override is not None
                             else mid(*p["symptomatic_fraction_pct_range"]) / 100.0)
    phi = (phi_override if phi_override is not None else mid(*p["detectable_at_arrival_pct_range"]) / 100.0)
    p0 = (prevalence_override if prevalence_override is not None
          else p["baseline_prevalence_pct"] / 100.0) * prevalence_multiplier

    mod = MODALITIES[follow_up_modality_key]
    follow_up_sensitivity = sensitivity_override if sensitivity_override is not None else mid(*mod["sensitivity_range"])
    follow_up_specificity = mid(*mod["specificity_range"])
    # cost_per_test_override: see run_scenario docstring. None => midpoint (unchanged).
    cost_per_test = (cost_per_test_override if cost_per_test_override is not None
                     else mid(*mod["cost_per_test_range"]))

    beta = Rt * gamma

    flow0 = wbe_gate_flow(p0, phi, avg_pax_per_flight, wbe_detection_prob,
                           wbe_false_positive_rate, follow_up_coverage,
                           follow_up_sensitivity, follow_up_specificity,
                           n_total=n_total, route_tiers=route_tiers)
    lam0 = flow0["lam"]

    S = N - lam0
    I = lam0
    R = 0.0

    r_daily = discount_rate_annual / 365.0
    total_cost = 0.0
    total_prog = total_hosp = total_prod = total_mort = total_icu = 0.0
    total_wbe_sampling = total_followup_testing = 0.0
    cum_infections = 0.0
    true_pos_cum = false_pos_cum = 0.0

    daily_deaths_undiscounted = 0.0
    daily_hosp_cases_undiscounted = 0.0
    for t in range(1, horizon_days + 1):
        flow = wbe_gate_flow(p0, phi, avg_pax_per_flight, wbe_detection_prob,
                              wbe_false_positive_rate, follow_up_coverage,
                              follow_up_sensitivity, follow_up_specificity,
                              n_total=n_total, route_tiers=route_tiers)
        lam = flow["lam"]

        # NO early-warning mechanism: Rt_today depends only on t, exactly as
        # in run_scenario(). WBE has no influence on this line whatsoever.
        Rt_today = time_varying_rt(Rt, t, response_delay_days=cm_response_delay_days,
                                    ramp_days=cm_ramp_days, reduction_strength=cm_reduction_strength) if apply_countermeasures else Rt
        beta_today = Rt_today * gamma
        S, I, R, incidence_today = sir_rk4_step(S, I, R, beta_today, gamma, lam, N)

        c_wbe_sampling = flow["flights_per_day"] * wbe_cost_per_sample
        c_followup = flow["n_followup"] * cost_per_test
        c_prog = c_wbe_sampling + c_followup

        # SHARED with run_scenario() -- compute_downstream_health_costs() is
        # the single implementation of Corrections 1,2,4,5, used identically
        # by both scenario runners (WBE-rebuild cleanup: previously this was
        # duplicated inline, with the ICU term referencing ECON["ICU_STRUCTURE"]
        # in run_scenario() -- a pre-existing latent bug, since ICU_STRUCTURE
        # was never merged into ECON -- and a defensive patched copy here.
        # Both pathways now use the one corrected implementation.)
        c_hosp, c_prod, c_mort, c_icu = compute_downstream_health_costs(
            incidence_today, symptomatic_fraction, hosp_rate, hosp_duration, CFR, vsl,
            mortality_already_infection_based=mortality_already_infection_based,
            icu_fraction_of_hosp_override=icu_fraction_of_hosp_override,
            icu_los_days_override=icu_los_days_override,
        )

        c_t = c_prog + c_hosp + c_prod + c_mort + c_icu

        if t > discount_start_day:
            disc_days = t - discount_start_day
            discount_factor = 1.0 / ((1 + r_daily) ** disc_days)
        else:
            discount_factor = 1.0

        total_cost += c_t * discount_factor
        total_prog += c_prog * discount_factor
        total_hosp += c_hosp * discount_factor
        total_prod += c_prod * discount_factor
        total_mort += c_mort * discount_factor
        total_icu += c_icu * discount_factor
        total_wbe_sampling += c_wbe_sampling * discount_factor
        total_followup_testing += c_followup * discount_factor

        # CORRECTION 8 (deaths/mortality-cost denominator consistency,
        # final-locked-model audit Finding 1) -- same fix as run_scenario()
        # above, applied here for the WBE-gated pathway.
        mortality_gate_for_deaths = 1.0 if mortality_already_infection_based else symptomatic_fraction
        daily_deaths_undiscounted += incidence_today * mortality_gate_for_deaths * CFR
        daily_hosp_cases_undiscounted += incidence_today * symptomatic_fraction * hosp_rate
        true_pos_cum += flow["true_positives"]
        false_pos_cum += flow["false_positives"]

        cum_infections += incidence_today

    cum_hosp_cases = daily_hosp_cases_undiscounted
    cum_deaths = daily_deaths_undiscounted

    return {
        "Rt": Rt, "gamma": gamma, "infectious_period_days": infectious_days,
        "CFR_pct": CFR * 100, "hosp_rate_pct": hosp_rate * 100,
        "symptomatic_fraction_pct": symptomatic_fraction * 100,
        "follow_up_modality": follow_up_modality_key,
        "follow_up_sensitivity": follow_up_sensitivity, "follow_up_specificity": follow_up_specificity,
        "cost_per_test": cost_per_test, "prevalence_frac": p0,
        "wbe_detection_prob": wbe_detection_prob, "wbe_false_positive_rate": wbe_false_positive_rate,
        "follow_up_coverage": follow_up_coverage, "avg_pax_per_flight": avg_pax_per_flight,
        "wbe_cost_per_sample": wbe_cost_per_sample,
        "final_S": S, "final_I": I, "final_R": R,
        "true_positives_cum": true_pos_cum, "false_positives_cum": false_pos_cum,
        "cumulative_infections": cum_infections, "cumulative_hosp_cases": cum_hosp_cases,
        "cumulative_deaths": cum_deaths,
        "screening_cost": total_prog, "hospital_cost": total_hosp,
        "productivity_cost": total_prod, "mortality_cost": total_mort, "icu_cost": total_icu,
        "wbe_sampling_cost": total_wbe_sampling, "followup_testing_cost": total_followup_testing,
        "total_societal_cost": total_cost,
        # Explicit isolation flag (per WBE-rebuild cleanup pass): any
        # consumer of this row (figures, tables, headline results, ranking
        # logic) MUST check this field. As long as wbe_detection_prob,
        # wbe_false_positive_rate, wbe_cost_per_sample, follow_up_coverage,
        # and avg_pax_per_flight are all still at their WBE_PARAMS defaults
        # (q=0.5, fp_rate=0.02, cost=$50, coverage=1.0, 250 pax/flight),
        # this row is NOT evidence-based and must not be cited, plotted, or
        # ranked as a finding -- see WBE_REBUILD.md.
        "wbe_parameter_status": (
            "placeholder_not_for_inference"
            if (wbe_detection_prob == WBE_PARAMS["wbe_detection_prob_per_infected_passenger"]
                and wbe_false_positive_rate == WBE_PARAMS["wbe_false_positive_rate"]
                and wbe_cost_per_sample == WBE_PARAMS["wbe_cost_per_sample"]
                and follow_up_coverage == WBE_PARAMS["follow_up_coverage"]
                and avg_pax_per_flight == WBE_PARAMS["avg_pax_per_flight"])
            else "non_default_parameters_still_unvalidated"
        ),
    }
