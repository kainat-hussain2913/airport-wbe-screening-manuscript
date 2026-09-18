"""
PSA convergence check + decomposition, rebuilt (final-locked-model audit
Phase 2) to use the SAME sampling methodology as the authoritative PSA
(`psa.py` / `run_psa_for_pathogen`) -- previously this script fixed test
specificity at its midpoint and never sampled it, while the authoritative
`psa.py` samples specificity from a Beta distribution per modality
(`spec_draws[mk] = beta_from_range(*mod["specificity_range"], ...)`). That
mismatch meant the convergence check was silently run under a DIFFERENT
model configuration than the one that produced the headline PSA numbers in
`results/psa_strategy_probabilities.csv`, and explains why an earlier version
of this script's N=10,000 result (96.9% for Influenza A/B) did not match the
authoritative run's N=10,000 result (98.95%, rounded to 99.0% in the
manuscript). See chat record / FINAL_MODEL_AUDIT.md for the audit finding.

This version:
  - Draws parameters in EXACTLY the same order, with EXACTLY the same
    distributions (including specificity), as run_psa_for_pathogen() in
    psa.py, so that truncating the stream at N=1,000 / 5,000 / 10,000 is a
    genuine convergence check of the actual final PSA, not an independent
    or differently-configured model.
  - Uses the SAME seed as the authoritative per-pathogen run (SEED + idx,
    from psa_one.py), so the N=10,000 draw here is literally the same
    10,000-iteration run that produced results/psa_strategy_probabilities.csv
    for that pathogen -- this lets the convergence check double as an exact
    reproducibility check of the headline number, not just an independently-
    seeded replicate.
  - Reports convergence for ALL FOUR strategies (not just molecular), since
    the manuscript's decision-relevant quantity is "which strategy is
    cost-minimising," not molecular-specific.
"""
import sys
import numpy as np
import csv
from parameters import PATHOGENS, MODALITIES, ECON, mid
from psa import (beta_from_range, lognormal_from_range, gamma_from_range, SEED, MODALITY_KEYS)
from engine import run_scenario


def run_raw(name, params, n_iter, seed):
    """Mirrors run_psa_for_pathogen() in psa.py EXACTLY (same draw order,
    same distributions, including specificity), but additionally retains
    per-iteration draws and per-strategy winner flags for convergence /
    decomposition reporting."""
    rng = np.random.default_rng(seed)
    Rt_draws = lognormal_from_range(*params["Rt_range"], rng, n_iter)
    inf_period_draws = lognormal_from_range(*params["infectious_period_range"], rng, n_iter)
    gamma_draws = 1.0 / inf_period_draws
    cfr_draws = beta_from_range(params["CFR_pct_range"][0] / 100, params["CFR_pct_range"][1] / 100, rng, n_iter)
    hosp_rate_draws = beta_from_range(params["hosp_rate_pct_range"][0] / 100, params["hosp_rate_pct_range"][1] / 100, rng, n_iter)
    hosp_dur_draws = lognormal_from_range(*params["hosp_duration_days_range"], rng, n_iter)
    symp_draws = beta_from_range(params["symptomatic_fraction_pct_range"][0] / 100, params["symptomatic_fraction_pct_range"][1] / 100, rng, n_iter)
    phi_draws = beta_from_range(params["detectable_at_arrival_pct_range"][0] / 100, params["detectable_at_arrival_pct_range"][1] / 100, rng, n_iter)
    prev_draws = beta_from_range(params["baseline_prevalence_pct"] / 100 * 0.5, params["baseline_prevalence_pct"] / 100 * 1.5, rng, n_iter)
    vsl_draws = gamma_from_range(ECON["VSL_low_resource"], ECON["VSL_high_income"], rng, n_iter)

    sens_draws = {}
    spec_draws = {}
    cost_draws = {}
    for mk in MODALITY_KEYS:
        mod = MODALITIES[mk]
        sens_draws[mk] = beta_from_range(*mod["sensitivity_range"], rng, n_iter) if mk != "none" else np.zeros(n_iter)
        spec_draws[mk] = beta_from_range(*mod["specificity_range"], rng, n_iter) if mk != "none" else np.ones(n_iter)
        cost_draws[mk] = gamma_from_range(*mod["cost_per_test_range"], rng, n_iter) if mk != "none" else np.zeros(n_iter)

    costs = {mk: np.zeros(n_iter) for mk in MODALITY_KEYS}
    for i in range(n_iter):
        for mk in MODALITY_KEYS:
            res = run_scenario(
                params, mk, prevalence_multiplier=1.0,
                rt_override=Rt_draws[i], gamma_override=gamma_draws[i],
                cfr_override=cfr_draws[i] * 100, hosp_rate_override=hosp_rate_draws[i] * 100,
                hosp_duration_override=hosp_dur_draws[i], symptomatic_fraction_override=symp_draws[i],
                phi_override=phi_draws[i], prevalence_override=prev_draws[i],
                vsl=vsl_draws[i],
                sensitivity_specificity_pair=(sens_draws[mk][i], spec_draws[mk][i]),
            )
            costs[mk][i] = res["total_societal_cost"]

    total_matrix = np.vstack([costs[mk] for mk in MODALITY_KEYS])  # shape (4, n_iter)
    winner_idx = np.argmin(total_matrix, axis=0)
    winner_flags = {mk: (winner_idx == j).astype(int) for j, mk in enumerate(MODALITY_KEYS)}

    draws = {"Rt": Rt_draws, "infectious_period": inf_period_draws, "CFR_pct": cfr_draws * 100,
             "hosp_rate_pct": hosp_rate_draws * 100, "hosp_duration": hosp_dur_draws,
             "symptomatic_fraction_pct": symp_draws * 100, "phi_detectable_pct": phi_draws * 100,
             "prevalence_pct": prev_draws * 100, "VSL": vsl_draws,
             "rapid_sensitivity": sens_draws["rapid"], "lab_sensitivity": sens_draws["lab"],
             "molecular_sensitivity": sens_draws["molecular"],
             "rapid_specificity": spec_draws["rapid"], "lab_specificity": spec_draws["lab"],
             "molecular_specificity": spec_draws["molecular"],
             "rapid_cost": cost_draws["rapid"], "lab_cost": cost_draws["lab"], "molecular_cost": cost_draws["molecular"]}
    return draws, winner_flags, costs


def report_convergence(pathogen, params, seed, csv_writer=None, is_primary=True):
    N_MAX = 10000
    draws, winner_flags, costs = run_raw(pathogen, params, N_MAX, seed)
    molecular_won = winner_flags["molecular"]

    label = "PRIMARY" if is_primary else "STRESS-TEST"
    print(f"\n=== {pathogen} ({label}) -- seed={seed} ===")
    print("Convergence check (probability EACH strategy is cost-minimising, at increasing N):")
    row_prev = {}
    for n in (1000, 5000, 10000):
        line = []
        for mk in MODALITY_KEYS:
            p = winner_flags[mk][:n].mean()
            se = (p * (1 - p) / n) ** 0.5
            line.append(f"{MODALITIES[mk]['label']}={p*100:5.1f}%(+/-{se*100:.2f}pp)")
            if csv_writer is not None:
                csv_writer.writerow([pathogen, label, seed, n, MODALITIES[mk]["label"], p, se])
        print(f"  N={n:6d}  " + "  ".join(line))

    p5k = winner_flags["molecular"][:5000].mean()
    p10k = winner_flags["molecular"][:10000].mean()
    print(f"  Molecular: |5k->10k| change = {abs(p10k-p5k)*100:.3f}pp")

    print("\nPoint-biserial correlation of each parameter draw with 'molecular won' (0/1):")
    corrs = []
    for name, d in draws.items():
        if np.std(d) < 1e-12:
            continue
        r = np.corrcoef(d, molecular_won)[0, 1]
        corrs.append((name, r))
    corrs.sort(key=lambda x: -abs(x[1]))
    for name, r in corrs:
        print(f"  {name:26s} r={r:+.3f}")

    with open(f"results/psa_decomposition_{pathogen.replace('/', '-').replace(' ', '_')}.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["parameter", "point_biserial_r"])
        for name, r in corrs:
            w.writerow([name, r])

    return winner_flags


if __name__ == "__main__":
    # ---------------------------------------------------------------------
    # Pathogen selection rationale (pre-specified, NOT chosen for convergence
    # niceness): among the six primary pathogens, select the one with the
    # MOST decisive PSA probability (closest to 100%) and the one with the
    # LEAST decisive PSA probability (closest to 50%), per the already-
    # computed, bit-identical-post-Phase-1 headline results in
    # results/psa_strategy_probabilities.csv:
    #   SARS-CoV-2 92.2%, Influenza A/B 99.0%, Mpox 96.2%, Norovirus 92.8%,
    #   Ebola 82.9%, Diphtheria 80.7%.
    # -> Influenza A/B (most decisive, 99.0%) and Diphtheria (least decisive
    #    among the six primaries, 80.7%) are the two representative primary
    #    pathogens for the convergence demonstration. Measles is run
    #    separately below, labelled explicitly as a stress-test convergence
    #    check, NOT as one of the two primary-pathogen representatives.
    # ---------------------------------------------------------------------
    PRIMARY_REPS = ["Influenza A/B", "Diphtheria"]

    with open("results/psa_convergence_final.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["pathogen", "pathogen_type", "seed", "n_iter", "strategy", "prob_cost_minimising", "mc_standard_error"])

        for pathogen in PRIMARY_REPS:
            idx = list(PATHOGENS.keys()).index(pathogen)
            seed = SEED + idx  # SAME seed as the authoritative psa_one.py run for this pathogen
            report_convergence(pathogen, PATHOGENS[pathogen], seed, csv_writer=w, is_primary=True)

        # Optional: measles stress-test convergence, run and reported
        # separately, explicitly NOT one of the two primary-pathogen reps.
        if len(sys.argv) > 1 and sys.argv[1] == "--with-measles":
            from parameters import STRESS_TEST_PATHOGENS
            seed = SEED + 100  # documented, distinct stream for the stress-test pathogen
            report_convergence("Measles", STRESS_TEST_PATHOGENS["Measles"], seed, csv_writer=w, is_primary=False)

    print("\nWrote results/psa_convergence_final.csv")
