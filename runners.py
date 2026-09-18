"""
WBE lead-time value: two scenario runners.

Scenario A (screening_only):
    The delayed arm defers airport screening by d days.
    Domestic countermeasure timing is IDENTICAL in both arms
    (starts at cm_response_delay_days from day 0, regardless of d).
    B_A(d) = C_A_late(d) - C_A_early(0)
    This isolates the value of earlier airport surveillance alone.

Scenario B (screening_plus_countermeasures):
    The delayed arm defers airport screening AND shifts the domestic
    countermeasure ramp by d days.
    Countermeasure start in immediate arm: cm_response_delay_days
    Countermeasure start in delayed arm:   cm_response_delay_days + d
    B_B(d) = C_B_late(d) - C_B_early(0)
    This captures the full value when WBE also triggers earlier policy action.

QA design:
    At d=0 both runners are identical (no delay) and must agree to <0.01%.
    B_A(0) = B_B(0) = 0 by construction.
    Scenario A keeps CM timing fixed; Scenario B shifts it by exactly d.

Implementation note:
    Both runners re-implement the day-loop directly (rather than calling
    run_scenario()) because run_scenario() fixes screening from day 1 and
    has no deployment-delay concept.  The mathematics are identical to
    engine.py; the key sub-functions (sir_rk4_step, time_varying_rt,
    daily_importation_rate, compute_downstream_health_costs) are imported
    from engine.py in <repo>/ (which shadows the
    uploaded copy and includes the icu_los_days_override targeted change).

ICU costing (revised 2026-09):
    Both public runner functions accept optional `icu_fraction_of_hosp`
    (default None → c_icu = 0, reproducing pre-ICU outputs exactly) and
    `icu_los_days` (default 7, backward-compatible).  Both are passed to
    compute_downstream_health_costs() via icu_fraction_of_hosp_override
    and icu_los_days_override respectively.
    Setting icu_fraction_of_hosp=None always reproduces previous outputs
    regardless of icu_los_days.
"""

import sys, os
# wbe_v2 engine.py must shadow the uploaded copy (contains icu_los_days_override patch).
import os as _os
sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))

from engine import (
    sir_rk4_step,
    time_varying_rt,
    daily_importation_rate,
    compute_downstream_health_costs,
    weighted_avg_multiplier,
)
from parameters import (
    PATHOGENS, MODALITIES, ECON, ROUTE_TIERS,
    N_TOTAL_ARRIVALS_PER_DAY, DOWNSTREAM_POPULATION, mid,
)

# Fixed countermeasure parameters — same as main-branch base case.
DEFAULT_CM_DELAY  = 21   # days from recognition to ramp start
DEFAULT_CM_RAMP   = 14   # days to full ramp
DEFAULT_CM_REDUC  = 0.6  # reduction strength


def _discount_factor(day, r_daily, discount_start_day):
    if day <= discount_start_day:
        return 1.0
    return 1.0 / ((1 + r_daily) ** (day - discount_start_day))


def _run_arm(
    pathogen_params,
    modality_key,
    deployment_delay_days,        # d: screening inactive for days 1..d
    cm_start_day,                  # absolute day countermeasure ramp begins
    prevalence_multiplier=1.0,
    horizon_days=365,
    vsl=ECON["VSL_base_case"],
    n_total=N_TOTAL_ARRIVALS_PER_DAY,
    N=DOWNSTREAM_POPULATION,
    discount_rate_annual=ECON["discount_rate_annual"],
    discount_start_day=ECON["discount_start_day"],
    cm_ramp_days=DEFAULT_CM_RAMP,
    cm_reduction_strength=DEFAULT_CM_REDUC,
    icu_fraction_of_hosp=None,    # None → c_icu = 0 (pre-ICU baseline)
    icu_los_days=7,               # ICU LOS in days; only used when icu_fraction_of_hosp is not None
):
    """
    Single-arm simulation.

    Screening is inactive (sensitivity = 0) for days 1..deployment_delay_days.
    Countermeasure ramp begins at cm_start_day (NOT tied to deployment_delay_days
    internally — the caller decides that relationship).

    Initial conditions: always set from sensitivity=0 (unscreened baseline),
    so that both arms of a B(d) comparison start from the same state and
    B(0) = 0 by construction regardless of test sensitivity.
    """
    p = pathogen_params
    Rt = mid(*p["Rt_range"])
    infectious_days = mid(*p["infectious_period_range"])
    gamma = 1.0 / infectious_days
    CFR = mid(*p["CFR_pct_range"]) / 100.0
    hosp_rate = mid(*p["hosp_rate_pct_range"]) / 100.0
    hosp_duration = mid(*p["hosp_duration_days_range"])
    symptomatic_fraction = mid(*p["symptomatic_fraction_pct_range"]) / 100.0
    phi = mid(*p["detectable_at_arrival_pct_range"]) / 100.0
    p0 = p["baseline_prevalence_pct"] / 100.0 * prevalence_multiplier
    mortality_already_infection_based = bool(p.get("mortality_already_infection_based"))

    mod = MODALITIES[modality_key]
    sensitivity = mid(*mod["sensitivity_range"])
    cost_per_test = mid(*mod["cost_per_test_range"])

    beta = Rt * gamma

    # Initial conditions: always unscreened baseline (sensitivity=0).
    lam0 = daily_importation_rate(p0, phi, 0.0, n_total=n_total)
    S = N - lam0
    I = lam0
    R = 0.0

    r_daily = discount_rate_annual / 365.0
    total_cost = 0.0
    total_prog = total_hosp = total_prod = total_mort = total_icu = 0.0
    cum_infections = 0.0
    cum_deaths = 0.0
    cum_hosp_cases = 0.0

    for day in range(1, horizon_days + 1):
        screening_active = day > deployment_delay_days
        eff_sensitivity = sensitivity if screening_active else 0.0
        n_test = n_total if screening_active else 0.0

        lam = daily_importation_rate(p0, phi, eff_sensitivity, n_total=n_total)

        # Countermeasure: Rt ramps down starting at cm_start_day.
        # We pass (day - cm_start_day + DEFAULT_CM_DELAY) as the response_delay
        # to time_varying_rt — equivalently, we just compute activation directly.
        Rt_today = time_varying_rt(
            Rt, day,
            response_delay_days=cm_start_day,
            ramp_days=cm_ramp_days,
            reduction_strength=cm_reduction_strength,
        )
        beta_today = Rt_today * gamma

        S_before = S
        S, I, R, incidence_today = sir_rk4_step(S, I, R, beta_today, gamma, lam, N)

        c_prog = n_test * cost_per_test if modality_key != "none" else 0.0

        c_hosp, c_prod, c_mort, c_icu = compute_downstream_health_costs(
            incidence_today, symptomatic_fraction, hosp_rate, hosp_duration, CFR, vsl,
            mortality_already_infection_based=mortality_already_infection_based,
            icu_fraction_of_hosp_override=icu_fraction_of_hosp,
            icu_los_days_override=icu_los_days,
        )

        df = _discount_factor(day, r_daily, discount_start_day)

        total_cost += (c_prog + c_hosp + c_prod + c_mort + c_icu) * df
        total_prog += c_prog * df
        total_hosp += c_hosp * df
        total_prod += c_prod * df
        total_mort += c_mort * df
        total_icu  += c_icu  * df

        mortality_gate = 1.0 if mortality_already_infection_based else symptomatic_fraction
        cum_deaths        += incidence_today * mortality_gate * CFR
        cum_hosp_cases    += incidence_today * symptomatic_fraction * hosp_rate
        cum_infections    += incidence_today

    return {
        "deployment_delay_days": deployment_delay_days,
        "cm_start_day":          cm_start_day,
        "total_societal_cost":   total_cost,
        "screening_cost":        total_prog,
        "hospital_cost":         total_hosp,
        "productivity_cost":     total_prod,
        "mortality_cost":        total_mort,
        "icu_cost":              total_icu,
        "cum_infections":        cum_infections,
        "cum_deaths":            cum_deaths,
        "cum_hosp_cases":        cum_hosp_cases,
        "Rt":                    Rt,
        "CFR_pct":               CFR * 100,
        "infectious_period_days": infectious_days,
        "phi_pct":               phi * 100,
        "p0_pct":                p0 * 100,
        "sensitivity":           sensitivity,
        "vsl":                   vsl,
    }


def run_scenario_a(
    pathogen_params, modality_key, deployment_delay_days,
    prevalence_multiplier=1.0, horizon_days=365, vsl=ECON["VSL_base_case"],
    n_total=N_TOTAL_ARRIVALS_PER_DAY, N=DOWNSTREAM_POPULATION,
    cm_response_delay_days=DEFAULT_CM_DELAY,
    cm_ramp_days=DEFAULT_CM_RAMP, cm_reduction_strength=DEFAULT_CM_REDUC,
    icu_fraction_of_hosp=None,
    icu_los_days=7,
):
    """
    Scenario A — screening_only:
    Both immediate and delayed arms use FIXED countermeasure start = cm_response_delay_days.
    Only screening timing differs between the two arms.
    Returns (immediate, delayed) dicts.

    icu_fraction_of_hosp: fraction of hospitalised cases admitted to ICU.
      None (default) → c_icu = 0, reproducing pre-ICU baseline outputs.
    icu_los_days: ICU length of stay in days per new admission (default=7,
      backward-compatible). Only used when icu_fraction_of_hosp is not None.
    """
    fixed_cm_start = cm_response_delay_days
    immediate = _run_arm(pathogen_params, modality_key, 0, fixed_cm_start,
                         prevalence_multiplier, horizon_days, vsl, n_total, N,
                         cm_ramp_days=cm_ramp_days, cm_reduction_strength=cm_reduction_strength,
                         icu_fraction_of_hosp=icu_fraction_of_hosp,
                         icu_los_days=icu_los_days)
    delayed   = _run_arm(pathogen_params, modality_key, deployment_delay_days, fixed_cm_start,
                         prevalence_multiplier, horizon_days, vsl, n_total, N,
                         cm_ramp_days=cm_ramp_days, cm_reduction_strength=cm_reduction_strength,
                         icu_fraction_of_hosp=icu_fraction_of_hosp,
                         icu_los_days=icu_los_days)
    return immediate, delayed


def run_scenario_b(
    pathogen_params, modality_key, deployment_delay_days,
    prevalence_multiplier=1.0, horizon_days=365, vsl=ECON["VSL_base_case"],
    n_total=N_TOTAL_ARRIVALS_PER_DAY, N=DOWNSTREAM_POPULATION,
    cm_response_delay_days=DEFAULT_CM_DELAY,
    cm_ramp_days=DEFAULT_CM_RAMP, cm_reduction_strength=DEFAULT_CM_REDUC,
    icu_fraction_of_hosp=None,
    icu_los_days=7,
):
    """
    Scenario B — screening_plus_countermeasures:
    Immediate arm: CM starts at cm_response_delay_days (day 21).
    Delayed arm:   CM starts at cm_response_delay_days + deployment_delay_days.
    Both screening timing and CM timing shift together.
    Returns (immediate, delayed) dicts.

    icu_fraction_of_hosp: fraction of hospitalised cases admitted to ICU.
      None (default) → c_icu = 0, reproducing pre-ICU baseline outputs.
    icu_los_days: ICU length of stay in days per new admission (default=7,
      backward-compatible). Only used when icu_fraction_of_hosp is not None.
    """
    immediate_cm = cm_response_delay_days
    delayed_cm   = cm_response_delay_days + deployment_delay_days
    immediate = _run_arm(pathogen_params, modality_key, 0, immediate_cm,
                         prevalence_multiplier, horizon_days, vsl, n_total, N,
                         cm_ramp_days=cm_ramp_days, cm_reduction_strength=cm_reduction_strength,
                         icu_fraction_of_hosp=icu_fraction_of_hosp,
                         icu_los_days=icu_los_days)
    delayed   = _run_arm(pathogen_params, modality_key, deployment_delay_days, delayed_cm,
                         prevalence_multiplier, horizon_days, vsl, n_total, N,
                         cm_ramp_days=cm_ramp_days, cm_reduction_strength=cm_reduction_strength,
                         icu_fraction_of_hosp=icu_fraction_of_hosp,
                         icu_los_days=icu_los_days)
    return immediate, delayed
