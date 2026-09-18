"""Measles PSA, run SEPARATELY and clearly labelled STRESS-TEST-ONLY (not part
of results/psa_summary.csv / psa_strategy_probabilities.csv, which cover only
the 6 primary pathogens). See FINAL_MODEL_AUDIT.md for why Measles is
excluded from the primary comparison."""
import numpy as np, csv
from parameters import STRESS_TEST_PATHOGENS
from psa import run_psa_for_pathogen, SEED

rng = np.random.default_rng(SEED + 999)
summary, costs = run_psa_for_pathogen("Measles", STRESS_TEST_PATHOGENS["Measles"], rng)
summary["primary_or_stress_test"] = "stress_test_only"
with open("results/psa_measles_stress_test_summary.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(summary.keys()))
    w.writeheader()
    w.writerow(summary)
print(f"Measles [STRESS TEST ONLY]: molecular cost-minimising in {summary['molecular_prob_cost_minimising']*100:.1f}% of 10000 sims")
