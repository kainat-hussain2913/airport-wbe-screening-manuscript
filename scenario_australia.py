"""
scenario_australia.py
======================
Australian-scale scenario: n_total = 52,700 arrivals/day, N = 27,100,000.

VERIFIED INPUTS
---------------
  Population (N_DOWNSTREAM_AUS = 27,100,000):
    ABS Estimated Resident Population, 31 March 2024.
    Source: ABS media release "Australia's population officially passes 27 million"
    https://www.abs.gov.au/media-centre/media-releases/australias-population-officially-passes-27-million

  Daily inbound international air arrivals (N_TOTAL_AUS = 52,700):
    ESTIMATED inbound arrivals/day, derived from BITRE International Airline Activity
    to April 2024 (statistical report). BITRE reports total two-way scheduled
    international passenger traffic for all Australian international airports (air only,
    scheduled services). 12-month total to April 2024: 38.473 million (two-way).
    Inbound-only total is not separately published; inbound estimated using a 50:50
    directional split assumption: 38,473,000 / 2 / 365 = 52,703 → rounded to 52,700/day.
    Reference period: May 2023 – April 2024.
    Source: BITRE International Airline Activity to April 2024 statistical report.
    https://www.bitre.gov.au/sites/default/files/documents/international_airline_activity_0424.pdf
    NOTE: ABS Overseas Arrivals and Departures (OAD) covers air AND sea ports and was
    not used as the primary source to avoid including cruise passenger arrivals.

PROGRAMME BENCHMARK (National Wastewater Surveillance Program)
-----------------------------------------------------------------------
  Contract total:  AUD 17,199,999 (3-year), annualised average AUD 5,733,333/year.
  Supplier:        Named on the Australian CDC programme page (per author).
  Programme:       National Wastewater Surveillance Program, Australian CDC.
  Scope:           48-50 sentinel sites; community wastewater + airport sites.
                   Airport sampling type: UNSPECIFIED in public description.
                   The CDC page states sites are selected for "potential for disease
                   incursion (such as airports)" but does not specify terminal vs
                   aircraft/lavatory WBE. Does not describe in-flight sampling.

  VERIFICATION STATUS:
    - Australian CDC website confirms: programme exists, 3-year initial term, sentinel
      sites include major international airports; supplier named on that page per author.
      Source: https://www.cdc.gov.au/diseases/surveillance-systems-and-networks/
              national-wastewater-surveillance-program
      Note: Automated text fetch of this page did not return a supplier name; author
      confirms the name appears on the page. AusTender records returned 403 errors.
    - AUD 17,199,999 contract value: provisional. Not independently verifiable from
      AusTender (inaccessible). Value from Mans Magnusson's communication.
    - The annualised average (AUD 5,733,333/year) is a computed average over the
      3-year contract term; the actual annual spending schedule is not published.
    - AUD/USD: 0.6556 (ATO average rate for financial year ending 30 June 2024).
      Source: Australian Taxation Office, foreign exchange rates, FY 2023-24.
      https://www.ato.gov.au/tax-rates-and-codes/foreign-exchange-rates-annual-2024-financial-year

  SCOPE MISMATCH NOTE:
    The PH4A programme covers community + airport TERMINAL wastewater (ground-side).
    The modelled intervention is aircraft wastewater screening (in-flight/lavatory).
    These differ in scope. The PH4A budget is used only as an indicative national
    programme expenditure benchmark; it is NOT a matched cost comparator.

US PROGRAMME BENCHMARK (for comparison section)
-------------------------------------------------
  USD 28M figure cited by Mans: could not be verified from a primary source.
  From primary sources found:
    - Ginkgo Bioworks/XpresCheck CDC contract (Aug 2022): USD 16M base / up to USD 61M
      with options. Covered ~4-5 airports initially.
      Source: GenomeWeb https://www.genomeweb.com/business-news/ginkgo-bioworks-xprescheck...
    - March 2024 expansion to 10 airports: investment "doubled" per CDC, no $ disclosed.
      Source: https://www.globenewswire.com/news-release/2024/03/12/2844404/
    - January 2025: USD 54M single payment under contract 75D30125C20439 (Ginkgo).
      Source: Nasdaq / USAspending.gov
    - No verified annual figure in range of USD 28M from a primary source.
  US programme benchmark is therefore stated as a range, not a single figure.

ALL MODEL PARAMETERS UNCHANGED
--------------------------------
  engine.py and parameters.py are LOCKED — not modified.
  Disease, economic, event-probability and warning-probability assumptions unchanged.
  The only overrides from manuscript baseline are n_total and N.
"""

import sys, os, csv, math, datetime

import os as _os
sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))

from parameters import (
    PATHOGENS, ECON, MODALITIES, WBE_PARAMS, ROUTE_TIERS,
    N_TOTAL_ARRIVALS_PER_DAY, DOWNSTREAM_POPULATION, mid,
)
from engine import daily_importation_rate
from runners import run_scenario_a, run_scenario_b
from portfolio import THREAT_CLASSES, PROB_SCENARIOS, MODALITY_DISPLAY
from icu_parameters import get_icu_params

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
N_TOTAL_AUS         = 52_700           # estimated daily inbound air arrivals (BITRE annual, 50:50 directional split; see provenance)
N_DOWNSTREAM_AUS    = 27_100_000       # ABS ERP 31 March 2024

N_TOTAL_BASELINE    = 10_000
N_DOWNSTREAM_BASELINE = 10_000_000

AVG_PAX_PER_FLIGHT  = WBE_PARAMS["avg_pax_per_flight"]    # 250 (locked)
FLIGHTS_PER_YEAR_AUS  = (N_TOTAL_AUS  / AVG_PAX_PER_FLIGHT) * 365   # 76,922
FLIGHTS_PER_YEAR_BASE = (N_TOTAL_BASELINE / AVG_PAX_PER_FLIGHT) * 365 # 14,600

LEAD_DAYS           = [2, 5, 10, 14]
HORIZON_DAYS        = 365
RESPONSE_MODALITY   = "molecular"
VSL                 = ECON["VSL_base_case"]   # USD 3.5M — NOT adjusted for Australia

# Programme benchmarks (original currencies, not converted in model)
PH4A_TOTAL_AUD      = 17_199_999
PH4A_YEARS          = 3
PH4A_ANNUAL_AVG_AUD = PH4A_TOTAL_AUD / PH4A_YEARS        # 5,733,333 AUD/yr (average)
AUD_USD_2024        = 0.6556                                 # ATO average FY 2023-24 (year ending 30 June 2024)
PH4A_ANNUAL_USD_IND = PH4A_ANNUAL_AVG_AUD * AUD_USD_2024  # USD ~3,727,000 (indicative)

RESULTS_DIR = "<repo>/results/australia_scenario"
os.makedirs(RESULTS_DIR, exist_ok=True)

# ---------------------------------------------------------------------------
# Configuration record
# ---------------------------------------------------------------------------
import time
t_start = time.time()

config_lines = [
    "# Australian Scenario — Configuration Record",
    f"Run timestamp: {datetime.datetime.utcnow().isoformat()}Z",
    "",
    "## Overrides from manuscript baseline (reconciliation_10k.py)",
    f"  n_total (arrivals/day): {N_TOTAL_BASELINE:,} → {N_TOTAL_AUS:,} (5.27×)",
    f"  N (downstream pop):     {N_DOWNSTREAM_BASELINE:,} → {N_DOWNSTREAM_AUS:,} (2.71×)",
    f"  flights/year:           {FLIGHTS_PER_YEAR_BASE:,.0f} → {FLIGHTS_PER_YEAR_AUS:,.0f}",
    "",
    "## Australian input provenance",
    f"  N_TOTAL_AUS = {N_TOTAL_AUS:,}: ESTIMATED inbound air arrivals/day.",
    f"    Derived from BITRE International Airline Activity to April 2024 (all Australian",
    f"    international airports, scheduled services, air only). Total two-way traffic for",
    f"    12 months to April 2024: 38.473M. Inbound estimated as half of two-way total",
    f"    (50:50 directional split assumption). Inbound-only not separately published.",
    f"    38,473,000 / 2 / 365 = 52,703/day → rounded to 52,700.",
    f"    Source: BITRE statistical report (May 2023 – April 2024).",
    f"    bitre.gov.au/sites/default/files/documents/international_airline_activity_0424.pdf",
    f"  N_DOWNSTREAM_AUS = {N_DOWNSTREAM_AUS:,}: ABS ERP, 31 March 2024",
    f"    Source: abs.gov.au/media-centre/media-releases/australias-population-officially-passes-27-million",
    "",
    "## Unchanged parameters",
    f"  avg_pax_per_flight: {AVG_PAX_PER_FLIGHT} (locked parameters.py)",
    f"  horizon_days:       {HORIZON_DAYS}",
    f"  lead_days:          {LEAD_DAYS}",
    f"  modality:           {RESPONSE_MODALITY}",
    f"  VSL (base_case):    USD {VSL:,}  [NOT adjusted for Australia]",
    f"  P_event/P_warning:  UNSOURCED SCENARIO ASSUMPTIONS — unchanged from THREAT_CLASSES",
    "",
    "## Programme benchmark",
    f"  PH4A 3-year total:      AUD {PH4A_TOTAL_AUD:,}",
    f"  PH4A annual average:    AUD {PH4A_ANNUAL_AVG_AUD:,.0f} [AVERAGE — actual schedule not published]",
    f"  AUD/USD:                {AUD_USD_2024} (ATO average, FY ending 30 June 2024)",
    f"  PH4A annual (USD):      USD {PH4A_ANNUAL_USD_IND:,.0f} [indicative; value provisional]",
    f"  Verification:           AUD 17,199,999 value: PROVISIONAL — from Mans Magnusson;",
    f"                          AusTender inaccessible (403). Supplier named on Australian",
    f"                          CDC programme page (per author); automated fetch did not",
    f"                          return supplier name in rendered text.",
    f"  Airport sampling type:  UNSPECIFIED in public description. CDC page states sites",
    f"                          selected for 'potential for disease incursion (such as airports)'",
    f"                          only; does not specify terminal vs aircraft/lavatory WBE.",
    f"  Scope note:             Programme covers community wastewater + airport sites.",
    f"                          Type of airport sampling unspecified. NOT equivalent to",
    f"                          in-flight aircraft WBE. Expenditure is a contextual benchmark.",
    "",
    "## Modelling caveat",
    "  N=27.1M in single-compartment SIR assumes homogeneous national mixing.",
    "  Model designed for a metropolitan catchment (N=10M); this is an extrapolation.",
    "  Results are order-of-magnitude estimates.",
    "",
    "## Files NOT modified",
    "  engine.py, parameters.py (locked). All existing results/ files preserved.",
]
print("\n".join(config_lines))

config_path = os.path.join(RESULTS_DIR, "australia_scenario_config.md")
with open(config_path, "w") as f:
    f.write("\n".join(config_lines) + "\n")

# ---------------------------------------------------------------------------
# Initial conditions check
# ---------------------------------------------------------------------------
print("\n=== Initial conditions at Australian scale ===")
WBE_PATHOGENS = {k: v for k, v in PATHOGENS.items() if v.get("wbe_applicable")}

ic_rows = []
for pname, params in WBE_PATHOGENS.items():
    p0  = params["baseline_prevalence_pct"] / 100.0
    phi = mid(*params["detectable_at_arrival_pct_range"]) / 100.0
    lam0_base = daily_importation_rate(p0, phi, 0.0, n_total=N_TOTAL_BASELINE)
    lam0_aus  = daily_importation_rate(p0, phi, 0.0, n_total=N_TOTAL_AUS)
    lam0_us   = daily_importation_rate(p0, phi, 0.0, n_total=300_000)
    ic_rows.append({"pathogen": pname, "lam0_base": lam0_base,
                    "lam0_aus": lam0_aus, "lam0_us": lam0_us})
    frac_aus  = lam0_aus / N_DOWNSTREAM_AUS
    frac_base = lam0_base / N_DOWNSTREAM_BASELINE
    print(f"  {pname}: lam0_base={lam0_base:.1f}, lam0_aus={lam0_aus:.1f}, lam0_us={lam0_us:.1f}"
          f" | I0/N_base={frac_base:.2e}, I0/N_aus={frac_aus:.2e}")

# ---------------------------------------------------------------------------
# B_d helper functions (exact pattern from scenario_us_350m.py)
# ---------------------------------------------------------------------------
def run_bd_aus(threat, runner_fn, d):
    icu_frac, icu_los = get_icu_params(threat)
    im, dl = runner_fn(
        threat["pathogen_params"], RESPONSE_MODALITY, d,
        prevalence_multiplier=threat["prevalence_multiplier"],
        horizon_days=HORIZON_DAYS, vsl=VSL,
        n_total=N_TOTAL_AUS, N=N_DOWNSTREAM_AUS,
        icu_fraction_of_hosp=icu_frac,
        icu_los_days=icu_los if icu_los is not None else 7,
    )
    bd             = max(0.0, dl["total_societal_cost"] - im["total_societal_cost"])
    deaths_averted = max(0.0, dl["cum_deaths"]     - im["cum_deaths"])
    return bd, deaths_averted


def run_bd_base(threat, runner_fn, d):
    icu_frac, icu_los = get_icu_params(threat)
    im, dl = runner_fn(
        threat["pathogen_params"], RESPONSE_MODALITY, d,
        prevalence_multiplier=threat["prevalence_multiplier"],
        horizon_days=HORIZON_DAYS, vsl=VSL,
        n_total=N_TOTAL_BASELINE, N=N_DOWNSTREAM_BASELINE,
        icu_fraction_of_hosp=icu_frac,
        icu_los_days=icu_los if icu_los is not None else 7,
    )
    bd             = max(0.0, dl["total_societal_cost"] - im["total_societal_cost"])
    deaths_averted = max(0.0, dl["cum_deaths"]     - im["cum_deaths"])
    return bd, deaths_averted


# ---------------------------------------------------------------------------
# Portfolio build (all combinations of scenario × avian × prob × lead_days)
# ---------------------------------------------------------------------------
RUNNER_MAP = {"A": run_scenario_a, "B": run_scenario_b}

print("\n=== Building portfolios — Australian scenario ===")

summary_rows = []
detail_rows  = []

for scenario_key, runner_fn in RUNNER_MAP.items():
    for avian_included in [False, True]:
        portfolio_label = (f"{scenario_key}_{'with' if avian_included else 'without'}_avian")
        print(f"  {portfolio_label} ...")

        for prob_scenario, event_key, warning_key in PROB_SCENARIOS:
            for d in LEAD_DAYS:
                threats_used = [t for t in THREAT_CLASSES
                                if (not t["avian_influenza"] or avian_included)]

                # Pre-compute Bd for each threat (shared across portfolio accumulation)
                bd_cache_aus  = {}
                bd_cache_base = {}
                for threat in threats_used:
                    bd_a, da_a = run_bd_aus(threat,  runner_fn, d)
                    bd_b, da_b = run_bd_base(threat, runner_fn, d)
                    bd_cache_aus[threat["threat_class"]]  = (bd_a, da_a)
                    bd_cache_base[threat["threat_class"]] = (bd_b, da_b)

                portfolio_ev_aus  = 0.0
                portfolio_ev_base = 0.0
                portfolio_deaths_aus  = 0.0
                portfolio_deaths_base = 0.0
                threat_rows = []

                for threat in threats_used:
                    p_event   = threat[event_key]
                    p_warning = threat[warning_key]

                    bd_a, da_a = bd_cache_aus[threat["threat_class"]]
                    bd_b, da_b = bd_cache_base[threat["threat_class"]]

                    ev_aus_tc  = p_event * p_warning * bd_a
                    ev_base_tc = p_event * p_warning * bd_b

                    portfolio_ev_aus       += ev_aus_tc
                    portfolio_ev_base      += ev_base_tc
                    portfolio_deaths_aus   += p_event * p_warning * da_a
                    portfolio_deaths_base  += p_event * p_warning * da_b

                    threat_rows.append(dict(
                        scenario=scenario_key,
                        avian_included=avian_included,
                        prob_scenario=prob_scenario,
                        lead_days=d,
                        threat_class=threat["threat_class"],
                        p_event=p_event,
                        p_warning=p_warning,
                        Bd_aus=bd_a,
                        Bd_base=bd_b,
                        ratio_Bd=bd_a / bd_b if bd_b > 0 else None,
                        ev_aus=ev_aus_tc,
                        ev_base=ev_base_tc,
                        deaths_averted_aus=da_a,
                        deaths_averted_base=da_b,
                    ))

                for row in threat_rows:
                    row["pct_of_portfolio_ev_aus"] = (
                        100.0 * row["ev_aus"] / portfolio_ev_aus
                        if portfolio_ev_aus > 0 else 0.0
                    )
                detail_rows.extend(threat_rows)

                summary_rows.append(dict(
                    scenario=scenario_key,
                    avian_included=avian_included,
                    prob_scenario=prob_scenario,
                    lead_days=d,
                    n_total_aus=N_TOTAL_AUS,
                    N_downstream_aus=N_DOWNSTREAM_AUS,
                    n_total_base=N_TOTAL_BASELINE,
                    N_downstream_base=N_DOWNSTREAM_BASELINE,
                    portfolio_ev_aus=portfolio_ev_aus,
                    portfolio_ev_base=portfolio_ev_base,
                    ratio_ev=(portfolio_ev_aus / portfolio_ev_base
                              if portfolio_ev_base > 0 else None),
                    cost_per_flight_aus=portfolio_ev_aus  / FLIGHTS_PER_YEAR_AUS,
                    cost_per_flight_base=portfolio_ev_base / FLIGHTS_PER_YEAR_BASE,
                    deaths_averted_aus=portfolio_deaths_aus,
                    deaths_averted_base=portfolio_deaths_base,
                    flights_per_year_aus=FLIGHTS_PER_YEAR_AUS,
                    flights_per_year_base=FLIGHTS_PER_YEAR_BASE,
                    vsl=VSL,
                    horizon_days=HORIZON_DAYS,
                ))

# ---------------------------------------------------------------------------
# Write CSV outputs
# ---------------------------------------------------------------------------
summary_path = os.path.join(RESULTS_DIR, "portfolio_summary_aus.csv")
detail_path  = os.path.join(RESULTS_DIR, "portfolio_detail_aus.csv")

with open(summary_path, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(summary_rows[0].keys()))
    w.writeheader(); w.writerows(summary_rows)
print(f"\nWrote {len(summary_rows)} rows to {summary_path}")

with open(detail_path, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(detail_rows[0].keys()))
    w.writeheader(); w.writerows(detail_rows)
print(f"Wrote {len(detail_rows)} rows to {detail_path}")

# ---------------------------------------------------------------------------
# Results summary printout
# ---------------------------------------------------------------------------
print()
print("=" * 95)
print("=== RESULTS: MANUSCRIPT BASELINE vs AUSTRALIAN SCENARIO (n=52,700 / N=27.1M) ===")
print("=" * 95)
print(f"Config: d=5 days, base prob, molecular, VSL=USD {VSL:,}")
print(f"P_event and P_warning: UNSOURCED SCENARIO ASSUMPTIONS (unchanged from manuscript).")
print(f"MODELLING CAVEAT: N=27.1M in single-compartment SIR — homogeneous national mixing assumed.")
print()

print(f"{'Scenario (prob)':<38} | {'Baseline EV':>14} | {'AUS EV':>14} | {'AUS/flight':>12} | {'Deaths/yr':>10}")
print("-" * 100)
for row in summary_rows:
    if row["lead_days"] == 5 and not row["avian_included"]:
        label = f"Scen {row['scenario']} — {row['prob_scenario']}"
        print(f"{label:<38} | ${row['portfolio_ev_base']:>13,.0f} | "
              f"${row['portfolio_ev_aus']:>13,.0f} | "
              f"${row['cost_per_flight_aus']:>11,.0f} | "
              f"{row['deaths_averted_aus']:>10.2f}")

print()
print("--- d-sweep, base probability, Scen A and B, excl. avian ---")
print(f"{'Scenario':<12} | {'d':>3} | {'Baseline EV':>14} | {'AUS EV':>14} | {'AUS/flight':>12}")
print("-" * 65)
for row in summary_rows:
    if row["prob_scenario"] == "base" and not row["avian_included"]:
        print(f"Scen {row['scenario']:<7} | {row['lead_days']:>3}d | "
              f"${row['portfolio_ev_base']:>13,.0f} | "
              f"${row['portfolio_ev_aus']:>13,.0f} | "
              f"${row['cost_per_flight_aus']:>11,.0f}")

print()
print("--- Avian stress test (SEPARATE — not in primary figures) ---")
for row in summary_rows:
    if row["avian_included"] and row["lead_days"] == 5 and row["prob_scenario"] == "base":
        print(f"  Scen {row['scenario']} + avian [STRESS], d=5: "
              f"AUS EV=${row['portfolio_ev_aus']:,.0f}  |  per-flight=${row['cost_per_flight_aus']:,.0f}")

# ---------------------------------------------------------------------------
# Comparison table: Baseline vs Australia vs US
# ---------------------------------------------------------------------------
print()
print("=" * 100)
print("=== THREE-WAY COMPARISON: Baseline | Australia | United States — d=5, base prob, excl. avian ===")
print("=" * 100)

# Load US saved results
us_path = "<repo>/results/us_scenario/portfolio_summary_us.csv"
us_d5 = {}
if os.path.exists(us_path):
    with open(us_path) as f:
        for row in csv.DictReader(f):
            if (row["prob_scenario"] == "base" and row["lead_days"] == "5"
                    and row["avian_included"] == "False"):
                us_d5[row["scenario"]] = {
                    "ev":  float(row["portfolio_ev_us"]),
                    "cpf": float(row["cost_per_flight_us"]),
                    "deaths": float(row["deaths_averted_us"]),
                }

aus_d5 = {r["scenario"]: r for r in summary_rows
          if r["lead_days"] == 5 and not r["avian_included"] and r["prob_scenario"] == "base"}

print(f"\n{'Parameter':<38} | {'Manuscript base':>16} | {'Australia':>16} | {'United States':>16}")
print("-" * 96)
print(f"{'Population (N)':<38} | {'10,000,000':>16} | {'27,100,000':>16} | {'350,000,000':>16}")
print(f"{'Arrivals/day (n_total)':<38} | {'10,000':>16} | {'52,700':>16} | {'300,000':>16}")
print(f"{'Flights/year':<38} | {'14,600':>16} | {FLIGHTS_PER_YEAR_AUS:>16,.0f} | {'438,000':>16}")
print(f"{'Model currency':<38} | {'USD':>16} | {'USD':>16} | {'USD':>16}")
print(f"{'VSL (all scenarios)':<38} | {'USD 3.5M':>16} | {'USD 3.5M':>16} | {'USD 3.5M':>16}")
print()
for sk in ["A", "B"]:
    ar = aus_d5.get(sk, {})
    ur = us_d5.get(sk, {})
    if ar and ur:
        print(f"{'Scen ' + sk + ' annual EV (USD)':<38} | "
              f"${ar['portfolio_ev_base']:>15,.0f} | "
              f"${ar['portfolio_ev_aus']:>15,.0f} | "
              f"${ur['ev']:>15,.0f}")
        print(f"{'Scen ' + sk + ' per-flight threshold (USD)':<38} | "
              f"${ar['cost_per_flight_base']:>15,.0f} | "
              f"${ar['cost_per_flight_aus']:>15,.0f} | "
              f"${ur['cpf']:>15,.0f}")
        print()

print(f"{'Programme expenditure benchmark':<38}")
print(f"  Australia:  AUD 17,199,999 total / AUD 5,733,333/year (3-yr average) [PROVISIONAL]")
print(f"              USD ~{PH4A_ANNUAL_USD_IND:,.0f}/year at AUD/USD {AUD_USD_2024} (ATO FY 2023-24 average) [indicative]")
print(f"              Scope: community + airport sites (airport sampling type unspecified;")
print(f"                     national programme; NOT equivalent to aircraft/lavatory WBE)")
print(f"              Coverage: 48-50 sentinel sites (community wastewater and airports)")
print(f"              Source: Mans Magnusson (AusTender inaccessible; value unverified)")
print(f"  US:         No single verified annual figure from primary sources.")
print(f"              USD 16M base / up to USD 61M with options (original 2022 contract)")
print(f"              USD 54M single payment January 2025 (contract 75D30125C20439)")
print(f"              Scope: nasal swabs + aircraft/terminal WBE, 10 major US airports")
print(f"              >70% of inbound international pax pass through participating airports")
print(f"              USD 28M figure cited by Mans: unverified from primary source")
print()
print("CAUTIONS:")
print("  1. Programme scopes do not match the modelled intervention (aircraft WBE).")
print("  2. Threshold-to-budget ratios do not constitute demonstrated ROI.")
print("  3. Event and warning probabilities are unsourced scenario assumptions.")
print("  4. Homogeneous national mixing assumed; model was designed for a city catchment.")
print("  5. Sea and land arrivals excluded from n_total in both country scenarios.")
print()
print(f"Total elapsed: {time.time()-t_start:.1f}s")
print("=== AUSTRALIA SCENARIO COMPLETE ===")
