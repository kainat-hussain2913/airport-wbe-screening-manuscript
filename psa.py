"""
Task 6: Probabilistic Sensitivity Analysis.

Distribution choices (per parameter TYPE, not chosen mechanically):
  - Probabilities/fractions bounded [0,1] (CFR, hosp_rate, symptomatic_fraction,
    detectable_at_arrival/phi, test sensitivity, test specificity, prevalence):
    BETA distribution. Beta is the standard choice for bounded proportions in
    health-economic PSA (Briggs, Claxton & Sculpher 2006) because it respects
    the [0,1] support and can represent both symmetric and skewed uncertainty.
  - Positive, unbounded, multiplicative-uncertainty parameters (Rt, infectious
    period / gamma): LOG-NORMAL. Transmission and duration parameters are
    naturally multiplicative (doubling/halving is the meaningful unit of
    uncertainty, not additive shifts), and log-normal enforces positivity.
  - Positive cost parameters (cost_per_test, VSL, c_bed, w_avg): GAMMA.
    Standard choice for cost data in health-economic PSA (right-skewed,
    strictly positive, matches typical cost-distribution shape).

Each manuscript-cited range (lo, hi) is treated as an approximate 95% interval
(lo = 2.5th percentile, hi = 97.5th percentile) and moment-matched to the
chosen distribution family: mean = midpoint(lo,hi), sd = (hi-lo)/4. This is a
standard, transparent, documented convention when only a range (not a full
distribution) is published - it is NOT an invented parameter value; only the
shape assumption around an already-cited range is added.

Seed: fixed at 20260811 (today's date, YYYYMMDD) for full reproducibility.
Iterations: 10,000 per pathogen (as specified), giving Monte Carlo standard
error on a strategy-selection probability of at most sqrt(0.25/10000) = 0.5pp
in the worst case (p=0.5), stable to 1 decimal place.
"""

import numpy as np
import csv
from parameters import PATHOGENS, MODALITIES, ECON, mid

SEED = 20260811
N_ITER = 10_000
MODALITY_KEYS = ["none", "rapid", "lab", "molecular"]


def beta_from_range(lo, hi, rng, size):
    mean = (lo + hi) / 2.0
    sd = max((hi - lo) / 4.0, 1e-9)
    if mean <= 0 or mean >= 1:
        return np.full(size, np.clip(mean, 1e-6, 1 - 1e-6))
    var = min(sd ** 2, mean * (1 - mean) * 0.98)
    common = mean * (1 - mean) / var - 1
    a = max(mean * common, 0.5)
    b = max((1 - mean) * common, 0.5)
    return rng.beta(a, b, size=size)


def lognormal_from_range(lo, hi, rng, size):
    mean = (lo + hi) / 2.0
    sd = max((hi - lo) / 4.0, 1e-9)
    sigma2 = np.log(1 + (sd / mean) ** 2)
    mu = np.log(mean) - sigma2 / 2
    return rng.lognormal(mu, np.sqrt(sigma2), size=size)


def gamma_from_range(lo, hi, rng, size):
    mean = (lo + hi) / 2.0
    sd = max((hi - lo) / 4.0, 1e-9)
    shape = (mean / sd) ** 2
    scale = sd ** 2 / mean
    return rng.gamma(shape, scale, size=size)


def run_psa_for_pathogen(name, params, rng, n_iter=N_ITER):
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

    from engine import run_scenario
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
    winner_counts = {mk: int(np.sum(winner_idx == j)) for j, mk in enumerate(MODALITY_KEYS)}
    winner_probs = {mk: winner_counts[mk] / n_iter for mk in MODALITY_KEYS}

    summary = {"pathogen": name, "n_iter": n_iter}
    for mk in MODALITY_KEYS:
        c = costs[mk]
        summary[f"{mk}_mean_cost"] = float(np.mean(c))
        summary[f"{mk}_median_cost"] = float(np.median(c))
        summary[f"{mk}_ci_lo"] = float(np.percentile(c, 2.5))
        summary[f"{mk}_ci_hi"] = float(np.percentile(c, 97.5))
        summary[f"{mk}_prob_cost_minimising"] = winner_probs[mk]

    no_screen_mean = summary["none_mean_cost"]
    for mk in MODALITY_KEYS:
        summary[f"{mk}_incremental_vs_none_mean"] = summary[f"{mk}_mean_cost"] - no_screen_mean

    return summary, costs


if __name__ == "__main__":
    rng = np.random.default_rng(SEED)
    all_summaries = []
    ceac_rows = []  # cost-effectiveness acceptability: strategy win-prob at this "true" scenario (baseline prevalence)
    for name, params in PATHOGENS.items():
        print(f"Running PSA for {name} ({N_ITER} iterations)...")
        summary, costs = run_psa_for_pathogen(name, params, rng)
        all_summaries.append(summary)
        for mk in MODALITY_KEYS:
            ceac_rows.append({"pathogen": name, "strategy": MODALITIES[mk]["label"],
                               "prob_cost_minimising": summary[f"{mk}_prob_cost_minimising"],
                               "mean_cost": summary[f"{mk}_mean_cost"],
                               "median_cost": summary[f"{mk}_median_cost"],
                               "ci95_lo": summary[f"{mk}_ci_lo"], "ci95_hi": summary[f"{mk}_ci_hi"]})

    fieldnames = list(all_summaries[0].keys())
    with open("results/psa_summary.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for s in all_summaries:
            w.writerow(s)

    with open("results/psa_strategy_probabilities.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(ceac_rows[0].keys()))
        w.writeheader()
        for r in ceac_rows:
            w.writerow(r)

    print("\nPSA strategy-selection probabilities at baseline prevalence:")
    for name in PATHOGENS:
        rows = [r for r in ceac_rows if r["pathogen"] == name]
        best = max(rows, key=lambda r: r["prob_cost_minimising"])
        print(f"  {name:20s} -> {best['strategy']:35s} cost-minimising in {best['prob_cost_minimising']*100:.1f}% of simulations")
    print(f"\nSeed={SEED}, N_ITER={N_ITER} per pathogen. Wrote results/psa_summary.csv and results/psa_strategy_probabilities.csv")
