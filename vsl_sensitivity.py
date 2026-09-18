"""
Task 4 of adversarial audit: VSL sensitivity analysis across 6 primary
pathogens (Measles excluded from primary set per the Measles investigation,
run separately below as a labelled stress-test case).

Base case: $3.5M (WHO-referenced), chosen because it is the manuscript's own
stated post-Round-1-review base case (R2-M3: "adopt a WHO-referenced or
equivalent standard VSL as the base case... current $300,000 base case is
not defensible as a neutral health economic assumption"). This choice was
made by the manuscript's authors/reviewers before I ever touched the model;
I did not select it to favour any strategy. All 4 anchors are run below.

ICU costing follows icu_parameters.scenario_icu_kwargs, as in every other
analysis in this study.
"""
import csv
from parameters import PATHOGENS, STRESS_TEST_PATHOGENS, MODALITIES, ECON
from engine import run_scenario
from icu_parameters import scenario_icu_kwargs

VSL_ANCHORS = [("low_resource_300k", 300_000), ("mid_1M", 1_000_000),
               ("WHO_base_case_3.5M", 3_500_000), ("US_EPA_11.6M", 11_600_000)]
MODALITY_KEYS = ["none", "rapid", "lab", "molecular"]
PRIMARY = ["SARS-CoV-2", "Influenza A/B", "Mpox", "Norovirus", "Ebola", "Diphtheria"]
STRESS_TEST_ONLY = ["Measles"]

rows = []
ALL_PATHOGENS = {**PATHOGENS, **STRESS_TEST_PATHOGENS}
for pathogen in PRIMARY + STRESS_TEST_ONLY:
    params = ALL_PATHOGENS[pathogen]
    icu_kw = scenario_icu_kwargs(pathogen)
    for label, vsl in VSL_ANCHORS:
        costs = {mk: run_scenario(params, mk, prevalence_multiplier=1.0, vsl=vsl, **icu_kw)["total_societal_cost"] for mk in MODALITY_KEYS}
        winner = min(costs, key=costs.get)
        rows.append({"pathogen": pathogen, "primary_or_stress_test": "primary" if pathogen in PRIMARY else "stress_test_only",
                     "vsl_anchor": label, "vsl_value": vsl, "winner": MODALITIES[winner]["label"],
                     "cost_none": costs["none"], "cost_rapid": costs["rapid"], "cost_lab": costs["lab"], "cost_molecular": costs["molecular"]})

with open("results/vsl_sensitivity.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader()
    for r in rows: w.writerow(r)

print("VSL sensitivity (winner at each anchor):")
for pathogen in PRIMARY + STRESS_TEST_ONLY:
    prow = [r for r in rows if r["pathogen"] == pathogen]
    tag = "" if pathogen in PRIMARY else " [STRESS-TEST ONLY, not primary]"
    print(f"  {pathogen:15s}{tag}")
    for r in prow:
        print(f"      {r['vsl_anchor']:20s} (${r['vsl_value']:>10,}) -> {r['winner']}")
    winners = set(r["winner"] for r in prow)
    print(f"      {'STABLE' if len(winners)==1 else 'CHANGES across VSL anchors'}")
