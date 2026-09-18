"""
Task 4: master deterministic results.
7 pathogens x {none, rapid, lab, molecular} x {0.5x, 1x, 2x baseline prevalence}
plus, for wbe_applicable pathogens, three WBE-GATED variants (RAT follow-up,
PCR/lab follow-up, LAMP/molecular follow-up) using the rebuilt analytical
gate (engine.py CORRECTION 7 / run_wbe_gated_scenario). `molecular` is
Sentinel RT-LAMP (see parameters.py MODALITIES["molecular"] and manuscript
Abstract) -- confirmed the third individual follow-up modality available in
this model, added here as a third WBE-gated arm alongside RAT and PCR, with
NO changes to any modality's sensitivity/specificity/cost/throughput
parameters. These WBE rows are NOT part of the primary cost-minimising
comparison (MODALITY_KEYS below is unchanged from before the WBE rebuild) --
they are reported as separate configuration rows, same as the WBE and
route-targeted variants were before. WBE_PARAMS values are explicit
placeholders (see parameters.py); these rows are NOT a headline result and
should not be cited as a validated WBE cost-effectiveness finding.

Strategy/output labels below use manuscript-facing modality names (Rapid
Antigen Test (RAT), Laboratory PCR, Sentinel RT-LAMP) rather than exposing
the internal code keys (rapid/lab/molecular) in any user-facing "strategy"
field.
ICU costing: every scenario is run with the pathogen's ICU admission fraction
and length of stay from icu_parameters.scenario_icu_kwargs, the same
configuration used by every other analysis in this study. Diphtheria and the
measles stress-test pathogen have no identified ICU inputs, so their c_icu term
is zero; that is an evidence gap, not a finding of zero ICU burden.
"""
import csv
import sys
from parameters import PATHOGENS, STRESS_TEST_PATHOGENS, MODALITIES, ECON
from engine import run_scenario, run_wbe_gated_scenario
from icu_parameters import scenario_icu_kwargs

PREV_TIERS = [("0.5x", 0.5), ("1x", 1.0), ("2x", 2.0)]
MODALITY_KEYS = ["none", "rapid", "lab", "molecular"]

# Manuscript-facing modality names, keyed by the internal MODALITIES code key.
# Used for all WBE-gated strategy labels below so no code key (rapid/lab/
# molecular) leaks into a manuscript-facing "strategy" field.
MANUSCRIPT_MODALITY_NAME = {
    "rapid": "RAT",
    "lab": "Laboratory PCR",
    "molecular": "Sentinel RT-LAMP",
}

WBE_FOLLOWUP_MODALITIES = [
    ("rapid", f"WBE-gated {MANUSCRIPT_MODALITY_NAME['rapid']} follow-up", "wbe_gated_rat"),
    ("lab", f"WBE-gated {MANUSCRIPT_MODALITY_NAME['lab']} follow-up", "wbe_gated_pcr"),
    ("molecular", f"WBE-gated {MANUSCRIPT_MODALITY_NAME['molecular']} follow-up", "wbe_gated_lamp"),
]

rows = []
ALL_FOR_RUN = list(PATHOGENS.items()) + list(STRESS_TEST_PATHOGENS.items())
STRESS_TEST_NAMES = set(STRESS_TEST_PATHOGENS.keys())
for pathogen, params in ALL_FOR_RUN:
    icu_kw = scenario_icu_kwargs(pathogen)
    for tier_label, mult in PREV_TIERS:
        scenario_costs = {}
        for mk in MODALITY_KEYS:
            result = run_scenario(params, mk, prevalence_multiplier=mult, **icu_kw)
            scenario_costs[mk] = result
            row = dict(pathogen=pathogen, prevalence_tier=tier_label, strategy=MODALITIES[mk]["label"],
                       strategy_key=mk, wbe_gated=False, route_targeted=False,
                       is_stress_test_only=(pathogen in STRESS_TEST_NAMES))
            row.update(result)
            rows.append(row)

        # WBE-gated variants (rebuilt analytical gate architecture), only if
        # pathogen is WBE-applicable. Three follow-up-modality variants
        # (RAT, PCR, Sentinel RT-LAMP), per approved implementation plan.
        # NOT included in the primary cost-minimising comparison (see below).
        if params["wbe_applicable"]:
            for followup_key, label, strategy_key in WBE_FOLLOWUP_MODALITIES:
                result = run_wbe_gated_scenario(params, followup_key, prevalence_multiplier=mult, **icu_kw)
                row = dict(pathogen=pathogen, prevalence_tier=tier_label, strategy=label,
                           strategy_key=strategy_key, wbe_gated=True, route_targeted=False,
                           is_stress_test_only=(pathogen in STRESS_TEST_NAMES))
                row.update(result)
                rows.append(row)

        # Route-targeted molecular variant (Task-relevant: route/source risk lever)
        result = run_scenario(params, "molecular", prevalence_multiplier=mult, route_targeted=True, **icu_kw)
        row = dict(pathogen=pathogen, prevalence_tier=tier_label, strategy="High-throughput molecular (route-targeted)",
                   strategy_key="molecular_route_targeted", wbe_gated=False, route_targeted=True,
                   is_stress_test_only=(pathogen in STRESS_TEST_NAMES))
        row.update(result)
        rows.append(row)

# Determine cost-minimising strategy per pathogen x prevalence tier among the
# 4 PRIMARY modalities (none/rapid/lab/molecular) -- WBE and route-targeted
# variants reported separately since they are configuration overlays, not a
# distinct primary comparator set, per the brief's Task 4 structure.
by_key = {}
for r in rows:
    by_key.setdefault((r["pathogen"], r["prevalence_tier"]), []).append(r)

for key, group in by_key.items():
    primary = [r for r in group if r["strategy_key"] in MODALITY_KEYS]
    best = min(primary, key=lambda r: r["total_societal_cost"])
    no_screen = next(r for r in primary if r["strategy_key"] == "none")
    for r in group:
        r["cost_minimising_primary_strategy"] = best["strategy"]
        r["incremental_cost_vs_no_screening"] = r["total_societal_cost"] - no_screen["total_societal_cost"]
        r["cases_averted_vs_no_screening"] = no_screen["cumulative_infections"] - r["cumulative_infections"]
        r["deaths_averted_vs_no_screening"] = no_screen["cumulative_deaths"] - r["cumulative_deaths"]

# Field sets differ between standalone-modality rows and WBE-gated rows
# (e.g. "sensitivity"/"specificity" vs "follow_up_sensitivity"/
# "follow_up_specificity" plus WBE-specific fields) -- union all keys,
# preserving first-seen order, and let DictWriter fill blanks for rows
# missing a given column (restval="").
fieldnames = []
seen = set()
for r in rows:
    for k in r.keys():
        if k not in seen:
            seen.add(k)
            fieldnames.append(k)

with open("results/master_deterministic.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=fieldnames, restval="")
    w.writeheader()
    for r in rows:
        w.writerow(r)

print(f"Wrote {len(rows)} rows to results/master_deterministic.csv")

# Quick sanity printout: cost-minimising strategy per pathogen at baseline (1x)
print("\nPRIMARY (6 pathogens) cost-minimising strategy at baseline (1x) prevalence:")
for pathogen in PATHOGENS:
    key = (pathogen, "1x")
    best_strat = by_key[key][0]["cost_minimising_primary_strategy"]
    total = next(r["total_societal_cost"] for r in by_key[key] if r["strategy"] == best_strat)
    print(f"  {pathogen:20s} -> {best_strat:35s}  (${total:,.0f} over {ECON['horizon_days']}d, discounted)")

print("\nSTRESS-TEST-ONLY (not primary; do not cite as a primary result):")
for pathogen in STRESS_TEST_PATHOGENS:
    key = (pathogen, "1x")
    best_strat = by_key[key][0]["cost_minimising_primary_strategy"]
    total = next(r["total_societal_cost"] for r in by_key[key] if r["strategy"] == best_strat)
    print(f"  {pathogen:20s} -> {best_strat:35s}  (${total:,.0f} over {ECON['horizon_days']}d, discounted)  [STRESS TEST]")
