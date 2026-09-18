"""
psa_icu.py
==========
ICU-enabled probabilistic sensitivity analysis (PSA).

Identical to psa_original.py but (a) passes per-pathogen ICU fraction and LOS
to run_scenario() via the engine's _override kwargs, and (b) passes the
Gamma-distributed per-test cost draws into the strategy calculation.

Key differences from psa_original.py:
  1. Imports ICU_FRACTIONS and ICU_LOS_DAYS from icu_parameters.
  2. run_scenario() called with icu_fraction_of_hosp_override and
     icu_los_days_override for each pathogen.
  3. run_scenario() called with cost_per_test_override drawn from the
     per-modality Gamma distribution (see FIX below).
  4. Output written to results/psa_icu_summary.csv and
     results/psa_icu_strategy_probabilities.csv (separate from pre-ICU outputs).

FIX (test-cost uncertainty, 2026-09)
------------------------------------
Earlier versions of this script generated `cost_draws[mk]` from
gamma_from_range(*MODALITIES[mk]["cost_per_test_range"]) but never passed them
to run_scenario(), so every iteration silently used the midpoint test cost
(engine default). Programme cost was therefore deterministic within a pathogen
and the Methods claim that test-cost uncertainty was propagated was not met.
The draws are now passed through `cost_per_test_override`, which the engine
applies only to the programme-cost term. Health outcomes are unaffected by
this argument (see engine.run_scenario docstring and
validate_cost_override.py).

`use_cost_draws=False` reproduces the previous (midpoint-cost) behaviour and
exists solely so the fix can be isolated from the change of seed convention
described below.

SEED CONVENTION
---------------
Each pathogen now draws from its own independent stream,
`np.random.default_rng(SEED + i)`, where i is the 0-based index of the
pathogen in parameters.PATHOGENS:

    SARS-CoV-2 = SEED+0, Influenza A/B = SEED+1, Mpox = SEED+2,
    Norovirus  = SEED+3, Ebola         = SEED+4, Diphtheria = SEED+5

with SEED = 20260811. This is the convention already documented in
psa_icu_ebola.py / psa_icu_diphtheria.py, now applied uniformly to all six
pathogens. It replaces the earlier mixed scheme in which the first four
pathogens consumed one sequential stream while Ebola and Diphtheria used
SEED+4 / SEED+5, a scheme whose results depended on how the run was chunked
across restarts. Under the present convention any single pathogen can be
rerun in isolation and reproduces exactly.

REPRODUCE:
  python3 psa_icu.py                    # corrected run -> results/psa_icu_*.csv
  python3 psa_icu.py --no-cost-draws \
      --out-prefix psa_icu_midpointcost_control   # midpoint-cost control
"""

import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import numpy as np
import csv
from parameters import PATHOGENS, MODALITIES, ECON, mid
from icu_parameters import ICU_FRACTIONS, ICU_LOS_DAYS

SEED   = 20260811    # same base seed as psa_original.py for comparability
N_ITER = 10_000
MODALITY_KEYS = ["none", "rapid", "lab", "molecular"]

# 0-based pathogen index -> independent RNG stream (see SEED CONVENTION above)
PATHOGEN_ORDER = list(PATHOGENS.keys())


def seed_for(name):
    """Documented per-pathogen seed: SEED + 0-based index in parameters.PATHOGENS."""
    return SEED + PATHOGEN_ORDER.index(name)


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


def run_psa_icu_for_pathogen(name, params, rng, n_iter=N_ITER, use_cost_draws=True):
    # Resolve per-pathogen ICU parameters
    icu_frac = ICU_FRACTIONS.get(name)   # None for Diphtheria
    icu_los  = ICU_LOS_DAYS.get(name)    # None for Diphtheria
    icu_kw = {
        "icu_fraction_of_hosp_override": icu_frac,
        "icu_los_days_override": icu_los if icu_los is not None else 7,
    }

    Rt_draws          = lognormal_from_range(*params["Rt_range"], rng, n_iter)
    inf_period_draws  = lognormal_from_range(*params["infectious_period_range"], rng, n_iter)
    gamma_draws       = 1.0 / inf_period_draws
    cfr_draws         = beta_from_range(params["CFR_pct_range"][0]/100, params["CFR_pct_range"][1]/100, rng, n_iter)
    hosp_rate_draws   = beta_from_range(params["hosp_rate_pct_range"][0]/100, params["hosp_rate_pct_range"][1]/100, rng, n_iter)
    hosp_dur_draws    = lognormal_from_range(*params["hosp_duration_days_range"], rng, n_iter)
    symp_draws        = beta_from_range(params["symptomatic_fraction_pct_range"][0]/100, params["symptomatic_fraction_pct_range"][1]/100, rng, n_iter)
    phi_draws         = beta_from_range(params["detectable_at_arrival_pct_range"][0]/100, params["detectable_at_arrival_pct_range"][1]/100, rng, n_iter)
    prev_draws        = beta_from_range(params["baseline_prevalence_pct"]/100 * 0.5, params["baseline_prevalence_pct"]/100 * 1.5, rng, n_iter)
    vsl_draws         = gamma_from_range(ECON["VSL_low_resource"], ECON["VSL_high_income"], rng, n_iter)

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
    prog_costs = {mk: np.zeros(n_iter) for mk in MODALITY_KEYS}
    for i in range(n_iter):
        for mk in MODALITY_KEYS:
            # FIX: propagate the per-test cost draw. use_cost_draws=False leaves
            # cost_per_test_override=None, i.e. the engine's midpoint behaviour.
            cost_kw = ({"cost_per_test_override": float(cost_draws[mk][i])}
                       if (use_cost_draws and mk != "none") else {})
            res = run_scenario(
                params, mk, prevalence_multiplier=1.0,
                rt_override=Rt_draws[i], gamma_override=gamma_draws[i],
                cfr_override=cfr_draws[i] * 100, hosp_rate_override=hosp_rate_draws[i] * 100,
                hosp_duration_override=hosp_dur_draws[i], symptomatic_fraction_override=symp_draws[i],
                phi_override=phi_draws[i], prevalence_override=prev_draws[i],
                vsl=vsl_draws[i],
                sensitivity_specificity_pair=(sens_draws[mk][i], spec_draws[mk][i]),
                **icu_kw, **cost_kw,
            )
            costs[mk][i] = res["total_societal_cost"]
            prog_costs[mk][i] = res["screening_cost"]

    total_matrix = np.vstack([costs[mk] for mk in MODALITY_KEYS])
    winner_idx   = np.argmin(total_matrix, axis=0)
    winner_counts = {mk: int(np.sum(winner_idx == j)) for j, mk in enumerate(MODALITY_KEYS)}
    winner_probs  = {mk: winner_counts[mk] / n_iter for mk in MODALITY_KEYS}

    summary = {
        "pathogen": name,
        "n_iter": n_iter,
        "icu_fraction": icu_frac,
        "icu_los_days": icu_los,
        "seed": int(seed_for(name)),
        "test_cost_draws_propagated": bool(use_cost_draws),
    }
    for mk in MODALITY_KEYS:
        c = costs[mk]
        summary[f"{mk}_mean_test_cost"]        = float(np.mean(cost_draws[mk]))
        summary[f"{mk}_mean_programme_cost"]   = float(np.mean(prog_costs[mk]))
        summary[f"{mk}_mean_cost"]             = float(np.mean(c))
        summary[f"{mk}_median_cost"]           = float(np.median(c))
        summary[f"{mk}_ci_lo"]                 = float(np.percentile(c, 2.5))
        summary[f"{mk}_ci_hi"]                 = float(np.percentile(c, 97.5))
        summary[f"{mk}_prob_cost_minimising"]  = winner_probs[mk]

    no_screen_mean = summary["none_mean_cost"]
    for mk in MODALITY_KEYS:
        summary[f"{mk}_incremental_vs_none_mean"] = summary[f"{mk}_mean_cost"] - no_screen_mean

    return summary, costs


if __name__ == "__main__":
    import argparse
    import time
    import json

    ap = argparse.ArgumentParser(description="ICU-enabled PSA, all six pathogens.")
    ap.add_argument("--no-cost-draws", action="store_true",
                    help="Do NOT propagate per-test cost draws (midpoint-cost control).")
    ap.add_argument("--out-prefix", default="psa_icu",
                    help="Output file prefix under results/ (default: psa_icu).")
    ap.add_argument("--n-iter", type=int, default=N_ITER)
    args = ap.parse_args()

    use_cost_draws = not args.no_cost_draws
    n_iter = args.n_iter
    prefix = args.out_prefix
    t0 = time.time()

    # Verify patched engine before spending an hour of CPU on the wrong one.
    from engine import run_scenario as _rs
    import inspect
    sig = str(inspect.signature(_rs))
    assert "icu_fraction_of_hosp_override" in sig, f"Engine lacks ICU override: {sig[:120]}"
    assert "cost_per_test_override" in sig, f"Engine lacks cost override: {sig[:120]}"
    print(f"Engine: {inspect.getfile(_rs)}  OK (ICU + cost overrides present)")
    print(f"Test-cost draws propagated: {use_cost_draws}")
    print(f"N_ITER={n_iter} per pathogen, base SEED={SEED}, per-pathogen seed = SEED + index")

    os.makedirs("results", exist_ok=True)

    CEAC_FIELDS = ["pathogen", "strategy", "icu_fraction", "icu_los_days", "seed",
                   "test_cost_draws_propagated", "prob_cost_minimising",
                   "mean_test_cost", "mean_programme_cost",
                   "mean_cost", "median_cost", "ci95_lo", "ci95_hi"]

    summary_path = f"results/{prefix}_summary.csv"
    ceac_path    = f"results/{prefix}_strategy_probabilities.csv"

    all_summaries, ceac_rows = [], []
    summary_fh = ceac_fh = sw = cw = None

    for idx, name in enumerate(PATHOGEN_ORDER):
        params = PATHOGENS[name]
        s = seed_for(name)
        rng = np.random.default_rng(s)
        print(f"[{idx+1}/6] {name}: PSA, {n_iter} iterations, seed={s} ...", flush=True)
        t1 = time.time()
        summary, costs = run_psa_icu_for_pathogen(name, params, rng, n_iter=n_iter,
                                                  use_cost_draws=use_cost_draws)
        print(f"      done in {time.time()-t1:.0f}s", flush=True)
        all_summaries.append(summary)

        rows_for_path = [{
            "pathogen": name,
            "strategy": MODALITIES[mk]["label"],
            "icu_fraction": summary["icu_fraction"],
            "icu_los_days": summary["icu_los_days"],
            "seed": summary["seed"],
            "test_cost_draws_propagated": summary["test_cost_draws_propagated"],
            "prob_cost_minimising": summary[f"{mk}_prob_cost_minimising"],
            "mean_test_cost": summary[f"{mk}_mean_test_cost"],
            "mean_programme_cost": summary[f"{mk}_mean_programme_cost"],
            "mean_cost": summary[f"{mk}_mean_cost"],
            "median_cost": summary[f"{mk}_median_cost"],
            "ci95_lo": summary[f"{mk}_ci_lo"],
            "ci95_hi": summary[f"{mk}_ci_hi"],
        } for mk in MODALITY_KEYS]
        ceac_rows.extend(rows_for_path)

        if idx == 0:
            summary_fh = open(summary_path, "w", newline="")
            sw = csv.DictWriter(summary_fh, fieldnames=list(summary.keys()))
            sw.writeheader()
            ceac_fh = open(ceac_path, "w", newline="")
            cw = csv.DictWriter(ceac_fh, fieldnames=CEAC_FIELDS)
            cw.writeheader()
        sw.writerow(summary); summary_fh.flush()
        for r in rows_for_path:
            cw.writerow(r)
        ceac_fh.flush()

        # Per-pathogen raw cost vectors, for convergence checks and CEACs.
        np.savez_compressed(f"results/{prefix}_draws_{name.replace('/', '-')}.npz",
                            **{mk: costs[mk] for mk in MODALITY_KEYS})

    summary_fh.close(); ceac_fh.close()

    meta = {
        "script": "psa_icu.py",
        "base_seed": SEED,
        "seed_convention": "np.random.default_rng(SEED + 0-based index in parameters.PATHOGENS)",
        "per_pathogen_seed": {n: int(seed_for(n)) for n in PATHOGEN_ORDER},
        "n_iter_per_pathogen": n_iter,
        "modalities": MODALITY_KEYS,
        "test_cost_draws_propagated": use_cost_draws,
        "test_cost_distribution": "Gamma, moment-matched to cost_per_test_range (mean=mid, sd=range/4)",
        "horizon_days": ECON["horizon_days"],
        "arrivals_per_day": 10000,
        "downstream_population": 10000000,
        "icu_fractions": {n: ICU_FRACTIONS.get(n) for n in PATHOGEN_ORDER},
        "icu_los_days": {n: ICU_LOS_DAYS.get(n) for n in PATHOGEN_ORDER},
        "diphtheria_icu_status": ("UNRESOLVED - no defensible sourced ICU fraction or LOS; "
                                  "run with icu_fraction_of_hosp_override=None, so c_icu=0 "
                                  "and the Diphtheria PSA remains pre-ICU"),
        "elapsed_seconds": round(time.time() - t0, 1),
    }
    with open(f"results/{prefix}_metadata.json", "w") as f:
        json.dump(meta, f, indent=2)

    print(f"\nICU-enabled PSA - strategy-selection probabilities")
    print(f"{'Pathogen':16s} {'ICU frac':9s} {'p(none)':9s} {'p(RAT)':9s} {'p(lab)':9s} {'p(molecular)':12s}")
    print("-" * 70)
    for name in PATHOGEN_ORDER:
        rows = {r["strategy"]: r for r in ceac_rows if r["pathogen"] == name}
        g = lambda mk: next(r["prob_cost_minimising"] for r in ceac_rows
                            if r["pathogen"] == name and r["strategy"] == MODALITIES[mk]["label"])
        frac = ICU_FRACTIONS.get(name)
        print(f"{name:16s} {str(frac):9s} {g('none')*100:7.2f}%  {g('rapid')*100:7.2f}%  "
              f"{g('lab')*100:7.2f}%  {g('molecular')*100:9.2f}%")

    print(f"\nSeed base={SEED} (per-pathogen SEED+index), N_ITER={n_iter}, "
          f"elapsed={time.time()-t0:.0f}s")
    print(f"Wrote {summary_path}, {ceac_path}, results/{prefix}_metadata.json")
