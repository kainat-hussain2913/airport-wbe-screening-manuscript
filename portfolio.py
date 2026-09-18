"""
Portfolio calculations and mechanism-decomposition table.

Broad-panel threat classes (from Mans broad_panel_option_value.py, preserved exactly):
  SARS-like, Avian-influenza (illustrative stress test), Ebola-like, Mpox-like, Enteric.

For each of Scenario A and B, we produce:
  - portfolio excluding avian influenza
  - portfolio including avian influenza (labelled as stress test)

For each portfolio × scenario, we report for d = 2, 5, 10, 14:
  - maximum supportable annual surveillance expenditure
  - expenditure per arriving flight
  - expected deaths averted per year
  - threat-class contributions
  - low/base/high probability assumptions (separately labelled as unsourced)

P_event and P_warning are KEPT SEPARATE throughout.
All probabilities are labelled as unsourced scenario assumptions.
Avian influenza is labelled:
  "Illustrative avian-influenza stress test; not a validated H5N1 estimate."

IMPORTANT: all displayed numbers are generated from CSVs; no manual transcription.
"""

import sys, os, csv, math
import os as _os
_HERE = _os.path.dirname(_os.path.abspath(__file__))
sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))

from parameters import PATHOGENS, ECON, MODALITIES, WBE_PARAMS, mid
from runners import run_scenario_a, run_scenario_b
from icu_parameters import get_icu_params

RESULTS_DIR = _os.path.join(_HERE, "results")
os.makedirs(RESULTS_DIR, exist_ok=True)

N_TOTAL          = 10_000          # manuscript baseline (parameters.py N_TOTAL_ARRIVALS_PER_DAY; S2.1)
# NOTE: 14,082 was previously used here with the label "manuscript baseline" — this was wrong.
# 14,082 is preserved in the audit record as a superseded scale figure (possibly Perth Airport
# actual arrivals) but is NOT the manuscript baseline. The approved baseline is 10,000.
AVG_PAX_PER_FLIGHT = WBE_PARAMS["avg_pax_per_flight"]
FLIGHTS_PER_DAY  = N_TOTAL / AVG_PAX_PER_FLIGHT
FLIGHTS_PER_YEAR = FLIGHTS_PER_DAY * 365

LEAD_DAYS        = [2, 5, 10, 14]
HORIZON_DAYS     = 365
RESPONSE_MODALITY= "molecular"
VSL              = ECON["VSL_base_case"]

MODALITY_DISPLAY = {
    "rapid":     "Rapid Antigen Test (RAT)",
    "lab":       "Laboratory PCR",
    "molecular": "High-throughput molecular screening",
}

# --- Threat classes (verbatim from broad_panel_option_value.py) ---
# All P_event / P_warning values are UNSOURCED SCENARIO ASSUMPTIONS.

def clone_params(source_name, **overrides):
    p = dict(PATHOGENS[source_name])
    p.update(overrides)
    return p

THREAT_CLASSES = [
    {
        "threat_class": "SARS-like respiratory virus",
        "representative_pathogen": "SARS-CoV-2",
        "pathogen_params": PATHOGENS["SARS-CoV-2"],
        "prevalence_multiplier": 1.0,
        "panel_target": "sarbecovirus/coronavirus broad panel",
        "avian_influenza": False,
        "avian_influenza_label": None,
        "probability_note": "UNSOURCED SCENARIO ASSUMPTION",
        "annual_event_probability_low":  0.005,
        "annual_event_probability_base": 0.02,
        "annual_event_probability_high": 0.05,
        "useful_warning_probability_low":  0.05,
        "useful_warning_probability_base": 0.20,
        "useful_warning_probability_high": 0.40,
    },
    {
        "threat_class": "Avian-influenza-like respiratory virus",
        "representative_pathogen": "pandemic H5N1-like stress scenario",
        "avian_influenza": True,
        "avian_influenza_label": "Illustrative avian-influenza stress test; not a validated H5N1 estimate.",
        "pathogen_params": clone_params(
            "Influenza A/B",
            Rt_range=(1.5, 2.5),
            CFR_pct_range=(0.5, 5.0),
            hosp_rate_pct_range=(5, 20),
            symptomatic_fraction_pct_range=(50, 80),
            baseline_prevalence_pct=0.2,
            wbe_applicable=True,
            wbe_evidence="illustrative panel stress scenario; not aircraft-WBE validated",
            mortality_already_infection_based=False,
        ),
        "prevalence_multiplier": 1.0,
        "panel_target": "influenza A / avian influenza broad panel",
        "probability_note": "UNSOURCED SCENARIO ASSUMPTION — illustrative only",
        "annual_event_probability_low":  0.002,
        "annual_event_probability_base": 0.01,
        "annual_event_probability_high": 0.03,
        "useful_warning_probability_low":  0.03,
        "useful_warning_probability_base": 0.15,
        "useful_warning_probability_high": 0.35,
    },
    {
        "threat_class": "Ebola-like viral haemorrhagic fever",
        "representative_pathogen": "Ebola",
        "pathogen_params": PATHOGENS["Ebola"],
        "prevalence_multiplier": 1.0,
        "panel_target": "filovirus broad panel",
        "avian_influenza": False,
        "avian_influenza_label": None,
        "probability_note": "UNSOURCED SCENARIO ASSUMPTION",
        "annual_event_probability_low":  0.001,
        "annual_event_probability_base": 0.005,
        "annual_event_probability_high": 0.02,
        "useful_warning_probability_low":  0.05,
        "useful_warning_probability_base": 0.20,
        "useful_warning_probability_high": 0.40,
    },
    {
        "threat_class": "Mpox-like orthopoxvirus",
        "representative_pathogen": "Mpox",
        "pathogen_params": PATHOGENS["Mpox"],
        "prevalence_multiplier": 1.0,
        "panel_target": "orthopoxvirus broad panel",
        "avian_influenza": False,
        "avian_influenza_label": None,
        "probability_note": "UNSOURCED SCENARIO ASSUMPTION",
        "annual_event_probability_low":  0.005,
        "annual_event_probability_base": 0.02,
        "annual_event_probability_high": 0.05,
        "useful_warning_probability_low":  0.05,
        "useful_warning_probability_base": 0.20,
        "useful_warning_probability_high": 0.40,
    },
    {
        "threat_class": "High-burden enteric outbreak",
        "representative_pathogen": "Norovirus",
        "pathogen_params": PATHOGENS["Norovirus"],
        "prevalence_multiplier": 1.0,
        "panel_target": "enteric virus broad panel",
        "avian_influenza": False,
        "avian_influenza_label": None,
        "probability_note": "UNSOURCED SCENARIO ASSUMPTION",
        "annual_event_probability_low":  0.02,
        "annual_event_probability_base": 0.10,
        "annual_event_probability_high": 0.25,
        "useful_warning_probability_low":  0.05,
        "useful_warning_probability_base": 0.20,
        "useful_warning_probability_high": 0.40,
    },
]

PROB_SCENARIOS = [
    ("low",  "annual_event_probability_low",  "useful_warning_probability_low"),
    ("base", "annual_event_probability_base", "useful_warning_probability_base"),
    ("high", "annual_event_probability_high", "useful_warning_probability_high"),
]


def run_bd_for_threat(threat, runner_fn, d):
    """Run immediate and delayed arms for one threat class; return B(d) and deaths averted.

    ICU parameters (fraction and LOS) are looked up per-pathogen from icu_parameters.py.
    For pathogens with unresolved ICU data (Diphtheria; not in THREAT_CLASSES) or where
    get_icu_params returns (None, None), icu_fraction_of_hosp=None → c_icu=0.
    """
    icu_frac, icu_los = get_icu_params(threat)
    im, dl = runner_fn(
        threat["pathogen_params"],
        RESPONSE_MODALITY,
        d,
        prevalence_multiplier=threat["prevalence_multiplier"],
        horizon_days=HORIZON_DAYS,
        vsl=VSL,
        n_total=N_TOTAL,
        icu_fraction_of_hosp=icu_frac,
        icu_los_days=icu_los if icu_los is not None else 7,
    )
    bd            = max(0.0, dl["total_societal_cost"] - im["total_societal_cost"])
    deaths_averted= max(0.0, dl["cum_deaths"]          - im["cum_deaths"])
    infect_averted= max(0.0, dl["cum_infections"]      - im["cum_infections"])
    return bd, deaths_averted, infect_averted


def build_portfolio(scenario_label, runner_fn, include_avian):
    """Build full detail rows and summary rows for one (scenario, avian_inclusion) combination."""
    detail_rows  = []
    summary_rows = []

    for prob_scenario, event_key, warning_key in PROB_SCENARIOS:
        for d in LEAD_DAYS:
            threats_used = [t for t in THREAT_CLASSES if (not t["avian_influenza"] or include_avian)]

            # Pre-compute B(d) for each threat (shared across prob scenarios for same d)
            bd_cache = {}
            for threat in threats_used:
                bd, deaths, infect = run_bd_for_threat(threat, runner_fn, d)
                bd_cache[threat["threat_class"]] = (bd, deaths, infect)

            portfolio_ev    = 0.0
            portfolio_deaths= 0.0
            portfolio_infect= 0.0
            threat_rows = []

            for threat in threats_used:
                p_event   = threat[event_key]
                p_warning = threat[warning_key]
                bd, deaths, infect = bd_cache[threat["threat_class"]]

                ev      = p_event * p_warning * bd
                ev_deaths = p_event * p_warning * deaths
                ev_infect = p_event * p_warning * infect
                portfolio_ev     += ev
                portfolio_deaths += ev_deaths
                portfolio_infect += ev_infect

                threat_rows.append({
                    "scenario":              scenario_label,
                    "avian_included":        include_avian,
                    "prob_scenario":         prob_scenario,
                    "lead_days":             d,
                    "threat_class":          threat["threat_class"],
                    "representative_pathogen": threat["representative_pathogen"],
                    "panel_target":          threat["panel_target"],
                    "avian_influenza":       threat["avian_influenza"],
                    "avian_influenza_label": threat["avian_influenza_label"] or "",
                    "probability_note":      threat["probability_note"],
                    "annual_event_probability":  p_event,
                    "useful_warning_probability_given_event": p_warning,
                    "combined_prob":         p_event * p_warning,
                    "conditional_Bd":        bd,
                    "expected_annual_contribution": ev,
                    "expected_deaths_averted_per_year": ev_deaths,
                    "expected_infections_averted_per_year": ev_infect,
                    "cost_per_arriving_flight_contribution": (
                        ev / FLIGHTS_PER_YEAR if FLIGHTS_PER_YEAR > 0 else 0.0
                    ),
                })

            # Add % contribution columns (requires portfolio total)
            for row in threat_rows:
                row["pct_of_portfolio_ev"] = (
                    100.0 * row["expected_annual_contribution"] / portfolio_ev
                    if portfolio_ev > 0 else 0.0
                )
            detail_rows.extend(threat_rows)

            summary_rows.append({
                "scenario":            scenario_label,
                "avian_included":      include_avian,
                "prob_scenario":       prob_scenario,
                "lead_days":           d,
                "n_threats":           len(threats_used),
                "portfolio_ev":        portfolio_ev,
                "cost_per_arriving_flight": portfolio_ev / FLIGHTS_PER_YEAR,
                "expected_deaths_averted_per_year": portfolio_deaths,
                "expected_infections_averted_per_year": portfolio_infect,
                "flights_per_year":    FLIGHTS_PER_YEAR,
                "n_total_arrivals_per_day": N_TOTAL,
                "avg_pax_per_flight":  AVG_PAX_PER_FLIGHT,
                "response_modality":   MODALITY_DISPLAY[RESPONSE_MODALITY],
                "vsl":                 VSL,
                "horizon_days":        HORIZON_DAYS,
                "avian_pct": (
                    100.0 * sum(r["expected_annual_contribution"] for r in threat_rows
                                if r["avian_influenza"]) / portfolio_ev
                    if include_avian and portfolio_ev > 0 else 0.0
                ),
            })

    return detail_rows, summary_rows


def build_mechanism_decomposition():
    """
    For each WBE-applicable pathogen × modality × lead_day (at 1x prevalence, base VSL),
    compute B_A (screening only), B_B (combined), incremental CM value, and pct.
    ICU parameters are looked up per-pathogen from icu_parameters.py.
    """
    from parameters import PATHOGENS
    from icu_parameters import ICU_FRACTIONS, ICU_LOS_DAYS
    WBE_PATHOGENS = {k: v for k, v in PATHOGENS.items() if v.get("wbe_applicable")}
    MODALITY_KEYS = ["rapid", "lab", "molecular"]
    rows = []
    for pname, params in WBE_PATHOGENS.items():
        icu_frac = ICU_FRACTIONS.get(pname)
        icu_los  = ICU_LOS_DAYS.get(pname)
        # If either is None (e.g., Diphtheria unresolved), pass None → c_icu=0
        kw_icu = {
            "icu_fraction_of_hosp": icu_frac,
            "icu_los_days": icu_los if icu_los is not None else 7,
        }
        for mk in MODALITY_KEYS:
            for d in LEAD_DAYS:
                im_a, dl_a = run_scenario_a(params, mk, d, horizon_days=HORIZON_DAYS, vsl=VSL, n_total=N_TOTAL, **kw_icu)
                im_b, dl_b = run_scenario_b(params, mk, d, horizon_days=HORIZON_DAYS, vsl=VSL, n_total=N_TOTAL, **kw_icu)
                bd_a = dl_a["total_societal_cost"] - im_a["total_societal_cost"]
                bd_b = dl_b["total_societal_cost"] - im_b["total_societal_cost"]
                incr = bd_b - bd_a
                pct  = 100.0 * incr / bd_b if bd_b > 0 else 0.0
                rows.append({
                    "pathogen":          pname,
                    "modality_key":      mk,
                    "modality_label":    MODALITY_DISPLAY[mk],
                    "lead_days":         d,
                    "B_screening_only":  bd_a,
                    "B_combined":        bd_b,
                    "B_incremental_CM":  incr,
                    "pct_CM_of_combined": pct,
                    "immediate_cm_start_A": im_a["cm_start_day"],
                    "delayed_cm_start_A":   dl_a["cm_start_day"],
                    "immediate_cm_start_B": im_b["cm_start_day"],
                    "delayed_cm_start_B":   dl_b["cm_start_day"],
                })
    return rows


if __name__ == "__main__":
    print("Building mechanism decomposition...")
    mech = build_mechanism_decomposition()
    mech_path = os.path.join(RESULTS_DIR, "mechanism_decomposition.csv")
    with open(mech_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(mech[0].keys()))
        w.writeheader(); w.writerows(mech)
    print(f"Wrote {len(mech)} rows to {mech_path}")

    all_detail = []
    all_summary = []
    for scenario_label, runner_fn in [
        ("A_screening_only", run_scenario_a),
        ("B_screening_plus_countermeasures", run_scenario_b),
    ]:
        for include_avian in [False, True]:
            label = f"{scenario_label}_{'with' if include_avian else 'without'}_avian"
            print(f"Building portfolio: {label} ...")
            det, summ = build_portfolio(scenario_label, runner_fn, include_avian)
            for r in det:  r["portfolio_view"] = label
            for r in summ: r["portfolio_view"] = label
            all_detail.extend(det)
            all_summary.extend(summ)

    det_path = os.path.join(RESULTS_DIR, "portfolio_detail.csv")
    summ_path = os.path.join(RESULTS_DIR, "portfolio_summary.csv")
    with open(det_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(all_detail[0].keys()))
        w.writeheader(); w.writerows(all_detail)
    with open(summ_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(all_summary[0].keys()))
        w.writeheader(); w.writerows(all_summary)
    print(f"Wrote {len(all_detail)} detail rows to {det_path}")
    print(f"Wrote {len(all_summary)} summary rows to {summ_path}")
