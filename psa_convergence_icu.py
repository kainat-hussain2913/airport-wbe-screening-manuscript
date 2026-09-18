"""
psa_convergence_icu.py
======================
PSA convergence check + parameter decomposition for the ICU-enabled,
test-cost-corrected PSA (psa_icu.py).

Supersedes psa_convergence_and_decomposition.py for the primary-pathogen
results, which mirrored the PRE-ICU psa.py: it passed no ICU overrides and
no per-test cost draws, so truncating its stream was a convergence check of
a different model configuration than the one reported in the manuscript.

This script mirrors run_psa_icu_for_pathogen() exactly -- same draw order,
same distributions, same ICU overrides, same cost_per_test_override -- and
uses the same per-pathogen seed (SEED + 0-based index in parameters.PATHOGENS).
The N=10,000 probability it computes is therefore not an independent
replicate but literally the authoritative run; this is asserted against the
cost vectors saved by psa_icu.py (results/psa_icu_draws_<pathogen>.npz), so a
silent divergence between the two scripts fails loudly.

Representative pathogens are those PRE-SPECIFIED before the ICU/test-cost
corrections (Influenza A/B, Diphtheria; see psa_convergence_and_decomposition.py
header). They are NOT re-selected on the corrected results. Whether they still
satisfy the pre-specified "most decisive / least decisive" rule under the
corrected results is reported explicitly, and any pathogen that newly satisfies
the rule is additionally run and labelled POST-HOC.

REPRODUCE:
  python3 psa_convergence_icu.py --with-measles
"""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import csv
import numpy as np

from parameters import PATHOGENS, MODALITIES, ECON, mid
from icu_parameters import ICU_FRACTIONS, ICU_LOS_DAYS
from psa_icu import (beta_from_range, lognormal_from_range, gamma_from_range,
                     SEED, N_ITER, MODALITY_KEYS, seed_for, PATHOGEN_ORDER)
from engine import run_scenario

PRIMARY_REPS = ["Influenza A/B", "Diphtheria"]   # pre-specified, not re-selected
MEASLES_SEED = SEED + 100                        # documented stress-test stream


def run_raw_icu(name, params, n_iter, seed, icu_frac, icu_los, use_cost_draws=True):
    """Byte-for-byte mirror of psa_icu.run_psa_icu_for_pathogen(), retaining
    the per-iteration draws and per-strategy winner flags."""
    rng = np.random.default_rng(seed)
    icu_kw = {"icu_fraction_of_hosp_override": icu_frac,
              "icu_los_days_override": icu_los if icu_los is not None else 7}

    Rt_draws         = lognormal_from_range(*params["Rt_range"], rng, n_iter)
    inf_period_draws = lognormal_from_range(*params["infectious_period_range"], rng, n_iter)
    gamma_draws      = 1.0 / inf_period_draws
    cfr_draws        = beta_from_range(params["CFR_pct_range"][0]/100, params["CFR_pct_range"][1]/100, rng, n_iter)
    hosp_rate_draws  = beta_from_range(params["hosp_rate_pct_range"][0]/100, params["hosp_rate_pct_range"][1]/100, rng, n_iter)
    hosp_dur_draws   = lognormal_from_range(*params["hosp_duration_days_range"], rng, n_iter)
    symp_draws       = beta_from_range(params["symptomatic_fraction_pct_range"][0]/100, params["symptomatic_fraction_pct_range"][1]/100, rng, n_iter)
    phi_draws        = beta_from_range(params["detectable_at_arrival_pct_range"][0]/100, params["detectable_at_arrival_pct_range"][1]/100, rng, n_iter)
    prev_draws       = beta_from_range(params["baseline_prevalence_pct"]/100*0.5, params["baseline_prevalence_pct"]/100*1.5, rng, n_iter)
    vsl_draws        = gamma_from_range(ECON["VSL_low_resource"], ECON["VSL_high_income"], rng, n_iter)

    sens_draws, spec_draws, cost_draws = {}, {}, {}
    for mk in MODALITY_KEYS:
        mod = MODALITIES[mk]
        sens_draws[mk] = beta_from_range(*mod["sensitivity_range"], rng, n_iter) if mk != "none" else np.zeros(n_iter)
        spec_draws[mk] = beta_from_range(*mod["specificity_range"], rng, n_iter) if mk != "none" else np.ones(n_iter)
        cost_draws[mk] = gamma_from_range(*mod["cost_per_test_range"], rng, n_iter) if mk != "none" else np.zeros(n_iter)

    costs = {mk: np.zeros(n_iter) for mk in MODALITY_KEYS}
    for i in range(n_iter):
        for mk in MODALITY_KEYS:
            cost_kw = ({"cost_per_test_override": float(cost_draws[mk][i])}
                       if (use_cost_draws and mk != "none") else {})
            res = run_scenario(
                params, mk, prevalence_multiplier=1.0,
                rt_override=Rt_draws[i], gamma_override=gamma_draws[i],
                cfr_override=cfr_draws[i]*100, hosp_rate_override=hosp_rate_draws[i]*100,
                hosp_duration_override=hosp_dur_draws[i], symptomatic_fraction_override=symp_draws[i],
                phi_override=phi_draws[i], prevalence_override=prev_draws[i],
                vsl=vsl_draws[i],
                sensitivity_specificity_pair=(sens_draws[mk][i], spec_draws[mk][i]),
                **icu_kw, **cost_kw,
            )
            costs[mk][i] = res["total_societal_cost"]

    winner_idx = np.argmin(np.vstack([costs[mk] for mk in MODALITY_KEYS]), axis=0)
    winner_flags = {mk: (winner_idx == j).astype(int) for j, mk in enumerate(MODALITY_KEYS)}

    draws = {"Rt": Rt_draws, "infectious_period": inf_period_draws, "CFR_pct": cfr_draws*100,
             "hosp_rate_pct": hosp_rate_draws*100, "hosp_duration": hosp_dur_draws,
             "symptomatic_fraction_pct": symp_draws*100, "phi_detectable_pct": phi_draws*100,
             "prevalence_pct": prev_draws*100, "VSL": vsl_draws,
             "rapid_sensitivity": sens_draws["rapid"], "lab_sensitivity": sens_draws["lab"],
             "molecular_sensitivity": sens_draws["molecular"],
             "rapid_specificity": spec_draws["rapid"], "lab_specificity": spec_draws["lab"],
             "molecular_specificity": spec_draws["molecular"],
             "rapid_cost": cost_draws["rapid"], "lab_cost": cost_draws["lab"],
             "molecular_cost": cost_draws["molecular"]}
    return draws, winner_flags, costs


def report(pathogen, params, seed, icu_frac, icu_los, w, kind="PRIMARY", verify_npz=True):
    draws, flags, costs = run_raw_icu(pathogen, params, N_ITER, seed, icu_frac, icu_los)

    if verify_npz:
        npz = f"results/psa_icu_draws_{pathogen.replace('/', '-')}.npz"
        if os.path.exists(npz):
            ref = np.load(npz)
            for mk in MODALITY_KEYS:
                assert np.array_equal(costs[mk], ref[mk]), (
                    f"{pathogen}/{mk}: convergence stream diverges from the authoritative "
                    f"psa_icu.py run -- the two scripts are no longer mirrors.")
            print(f"  [verify] {pathogen}: cost vectors identical to authoritative psa_icu.py run")
        else:
            print(f"  [verify] {pathogen}: {npz} absent -- run psa_icu.py first to enable the check")

    print(f"\n=== {pathogen} ({kind}) -- seed={seed}, ICU frac={icu_frac}, ICU LOS={icu_los} ===")
    for n in (1000, 5000, 10000):
        parts = []
        for mk in MODALITY_KEYS:
            p = flags[mk][:n].mean()
            se = (p*(1-p)/n) ** 0.5
            parts.append(f"{MODALITIES[mk]['label']}={p*100:5.1f}%(+/-{se*100:.2f}pp)")
            w.writerow([pathogen, kind, seed, n, MODALITIES[mk]["label"], p, se,
                        icu_frac if icu_frac is not None else "", True])
        print(f"  N={n:6d}  " + "  ".join(parts))
    p5, p10 = flags["molecular"][:5000].mean(), flags["molecular"].mean()
    print(f"  Molecular: |5k->10k| change = {abs(p10-p5)*100:.3f}pp")

    corrs = sorted(((k, float(np.corrcoef(d, flags["molecular"])[0, 1]))
                    for k, d in draws.items() if np.std(d) > 1e-12),
                   key=lambda x: -abs(x[1]))
    with open(f"results/psa_icu_decomposition_{pathogen.replace('/', '-').replace(' ', '_')}.csv",
              "w", newline="") as f:
        cw = csv.writer(f)
        cw.writerow(["parameter", "point_biserial_r"])
        cw.writerows(corrs)
    print("  Top correlates of 'molecular won': " +
          ", ".join(f"{k} r={r:+.3f}" for k, r in corrs[:5]))
    return flags


if __name__ == "__main__":
    with_measles = "--with-measles" in sys.argv

    # Read the corrected headline probabilities to test the pre-specified rule.
    headline = {}
    with open("results/psa_icu_strategy_probabilities.csv") as f:
        for r in csv.DictReader(f):
            if r["strategy"] == MODALITIES["molecular"]["label"]:
                headline[r["pathogen"]] = float(r["prob_cost_minimising"])
    most  = max(headline, key=lambda k: headline[k])
    least = min(headline, key=lambda k: abs(headline[k] - 0.5))
    print("Corrected headline p(molecular cost-minimising):")
    for k, v in headline.items():
        print(f"  {k:16s} {v*100:6.2f}%")
    print(f"Pre-specified rule applied to corrected results -> most decisive: {most}; "
          f"least decisive: {least}")
    print(f"Pre-specified representatives (fixed, not re-selected): {PRIMARY_REPS}")

    extra = [p for p in (most, least) if p not in PRIMARY_REPS]
    if extra:
        print(f"NOTE: under the corrected results the rule now selects {extra}; "
              f"these are additionally run and labelled POST-HOC.")

    with open("results/psa_icu_convergence_final.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["pathogen", "pathogen_type", "seed", "n_iter", "strategy",
                    "prob_cost_minimising", "mc_standard_error", "icu_fraction",
                    "test_cost_draws_propagated"])

        for pathogen in PRIMARY_REPS:
            report(pathogen, PATHOGENS[pathogen], seed_for(pathogen),
                   ICU_FRACTIONS.get(pathogen), ICU_LOS_DAYS.get(pathogen), w, "PRIMARY")

        for pathogen in extra:
            report(pathogen, PATHOGENS[pathogen], seed_for(pathogen),
                   ICU_FRACTIONS.get(pathogen), ICU_LOS_DAYS.get(pathogen), w,
                   "PRIMARY-POSTHOC")

        if with_measles:
            from parameters import STRESS_TEST_PATHOGENS
            # Measles has no sourced ICU fraction in icu_parameters.py; run with
            # icu_fraction=None (c_icu = 0), i.e. the stress test stays pre-ICU.
            report("Measles", STRESS_TEST_PATHOGENS["Measles"], MEASLES_SEED,
                   ICU_FRACTIONS.get("Measles"), ICU_LOS_DAYS.get("Measles"),
                   w, "STRESS-TEST", verify_npz=False)

    print("\nWrote results/psa_icu_convergence_final.csv")
