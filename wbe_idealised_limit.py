"""
wbe_idealised_limit.py
======================
WBE gate at its idealised limiting case, compared with universal screening.

The idealised limit is q = 1.0 (every flight carrying an infected passenger is
flagged), wbe_false_positive_rate = 0 (no uninfected flight is flagged),
follow_up_coverage = 1.0 (every passenger on a flagged flight is tested) and
wbe_cost_per_sample = 0 (sampling is free). It is a mathematical boundary
condition, not an operationally realistic configuration, and it lies outside the
swept ranges in wbe_threshold_sweep_icu.py.

The purpose is to substantiate Extended Methods S-WBE / Supplementary Table S19:
at this limit the gate's epidemiological outcomes are identical to universal
screening by construction, and its entire economic effect is a reduction in
testing volume.

Configuration matches the threshold sweep: four WBE-applicable pathogens, three
prevalence scenarios, three follow-up modalities, 365-day horizon, 10,000
arrivals/day, 250 passengers per flight, ICU costing enabled.

Writes results/wbe_sweep/wbe_idealised_limit.csv. Modifies nothing else.
"""

import os, sys, csv

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from parameters import PATHOGENS
from engine import run_scenario, run_wbe_gated_scenario
from icu_parameters import ICU_FRACTIONS, ICU_LOS_DAYS

HERE        = os.path.dirname(os.path.abspath(__file__))
RESULTS_DIR = os.path.join(HERE, "results", "wbe_sweep")
os.makedirs(RESULTS_DIR, exist_ok=True)

PREV_TIERS          = [("0.5x", 0.5), ("1x", 1.0), ("2x", 2.0)]
FOLLOWUP_MODALITIES = [("rapid", "RAT"), ("lab", "Laboratory PCR"),
                       ("molecular", "Sentinel RT-LAMP")]
REFERENCE_PAX = 250
HORIZON_DAYS  = 365
N_TOTAL       = 10_000

# The idealised limit
Q_IDEAL, FP_IDEAL, COV_IDEAL, SAMPLE_COST_IDEAL = 1.0, 0.0, 1.0, 0.0

HEALTH_FIELDS = ["cumulative_infections", "cumulative_hosp_cases", "cumulative_deaths",
                 "hospital_cost", "productivity_cost", "mortality_cost", "icu_cost"]


def icu_kwargs(name):
    frac, los = ICU_FRACTIONS.get(name), ICU_LOS_DAYS.get(name)
    if frac is None or los is None:
        return {"icu_fraction_of_hosp_override": None, "icu_los_days_override": 7}
    return {"icu_fraction_of_hosp_override": frac, "icu_los_days_override": los}


rows = []
for pathogen, params in PATHOGENS.items():
    if not params.get("wbe_applicable"):
        continue
    icu_kw = icu_kwargs(pathogen)
    for tier_label, mult in PREV_TIERS:
        for modality_key, modality_label in FOLLOWUP_MODALITIES:
            uc = run_scenario(params, modality_key, prevalence_multiplier=mult,
                              horizon_days=HORIZON_DAYS, n_total=N_TOTAL, **icu_kw)
            gate = run_wbe_gated_scenario(
                params, modality_key, prevalence_multiplier=mult,
                wbe_detection_prob=Q_IDEAL, wbe_false_positive_rate=FP_IDEAL,
                follow_up_coverage=COV_IDEAL, avg_pax_per_flight=REFERENCE_PAX,
                wbe_cost_per_sample=SAMPLE_COST_IDEAL, horizon_days=HORIZON_DAYS,
                n_total=N_TOTAL, **icu_kw)

            # Programme cost carries the same per-test price in both arms, so its
            # ratio is the testing-volume ratio at this limit (sampling cost = 0).
            uc_prog, gate_prog = uc["screening_cost"], gate["screening_cost"]
            row = dict(
                pathogen=pathogen, prevalence_tier=tier_label,
                follow_up_modality=modality_label,
                wbe_detection_prob_q=Q_IDEAL, wbe_false_positive_rate=FP_IDEAL,
                follow_up_coverage=COV_IDEAL, wbe_cost_per_sample=SAMPLE_COST_IDEAL,
                avg_pax_per_flight=REFERENCE_PAX, horizon_days=HORIZON_DAYS,
                n_total=N_TOTAL,
                icu_fraction=icu_kw["icu_fraction_of_hosp_override"],
                icu_los_days=icu_kw["icu_los_days_override"],
                cost_per_test=gate["cost_per_test"],
            )
            for f in HEALTH_FIELDS:
                row[f"uc_{f}"] = uc[f]
                row[f"gate_{f}"] = gate[f]
                row[f"delta_{f}"] = gate[f] - uc[f]
            row.update(
                uc_programme_cost=uc_prog,
                gate_programme_cost=gate_prog,
                gate_wbe_sampling_cost=gate["wbe_sampling_cost"],
                programme_cost_ratio=gate_prog / uc_prog if uc_prog else None,
                programme_cost_saving_pct=100.0 * (1 - gate_prog / uc_prog) if uc_prog else None,
                uc_total_societal_cost=uc["total_societal_cost"],
                gate_total_societal_cost=gate["total_societal_cost"],
                delta_total_societal_cost=gate["total_societal_cost"] - uc["total_societal_cost"],
                max_rel_health_deviation=max(
                    (abs(gate[f] - uc[f]) / abs(uc[f])) if uc[f] else 0.0
                    for f in HEALTH_FIELDS),
            )
            rows.append(row)

out = os.path.join(RESULTS_DIR, "wbe_idealised_limit.csv")
with open(out, "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(rows)

dev = max(r["max_rel_health_deviation"] for r in rows)
savings = [r["programme_cost_saving_pct"] for r in rows]
print(f"{len(rows)} idealised-limit cases written to {out}")
print(f"largest relative difference in any health outcome or health cost vs "
      f"universal screening: {dev:.2e} (floating-point rounding)")
print(f"programme-cost saving (= testing-volume reduction at this limit): "
      f"{min(savings):.2f}% to {max(savings):.2f}%")
for r in rows:
    if r["pathogen"] == "SARS-CoV-2" and r["prevalence_tier"] == "1x":
        print(f"  SARS-CoV-2, base prevalence, {r['follow_up_modality']}: "
              f"{r['programme_cost_saving_pct']:.2f}% saving "
              f"({r['programme_cost_ratio']*100:.1f}% of passengers still tested)")
