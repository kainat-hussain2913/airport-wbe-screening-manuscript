# Australian Scenario — Configuration Record
Run timestamp: 2026-09-15T07:42:34.604862Z

## Overrides from manuscript baseline (reconciliation_10k.py)
  n_total (arrivals/day): 10,000 → 52,700 (5.27×)
  N (downstream pop):     10,000,000 → 27,100,000 (2.71×)
  flights/year:           14,600 → 76,942

## Australian input provenance
  N_TOTAL_AUS = 52,700: ESTIMATED inbound air arrivals/day.
    Derived from BITRE International Airline Activity to April 2024 (all Australian
    international airports, scheduled services, air only). Total two-way traffic for
    12 months to April 2024: 38.473M. Inbound estimated as half of two-way total
    (50:50 directional split assumption). Inbound-only not separately published.
    38,473,000 / 2 / 365 = 52,703/day → rounded to 52,700.
    Source: BITRE statistical report (May 2023 – April 2024).
    bitre.gov.au/sites/default/files/documents/international_airline_activity_0424.pdf
  N_DOWNSTREAM_AUS = 27,100,000: ABS ERP, 31 March 2024
    Source: abs.gov.au/media-centre/media-releases/australias-population-officially-passes-27-million

## Unchanged parameters
  avg_pax_per_flight: 250 (locked parameters.py)
  horizon_days:       365
  lead_days:          [2, 5, 10, 14]
  modality:           molecular
  VSL (base_case):    USD 3,500,000  [NOT adjusted for Australia]
  P_event/P_warning:  UNSOURCED SCENARIO ASSUMPTIONS — unchanged from THREAT_CLASSES

## Programme benchmark
  PH4A 3-year total:      AUD 17,199,999
  PH4A annual average:    AUD 5,733,333 [AVERAGE — actual schedule not published]
  AUD/USD:                0.6556 (ATO average, FY ending 30 June 2024)
  PH4A annual (USD):      USD 3,758,773 [indicative; value provisional]
  Verification:           AUD 17,199,999 value: PROVISIONAL — from Mans Magnusson;
                          AusTender inaccessible (403). Supplier named on Australian
                          CDC programme page (per author); automated fetch did not
                          return supplier name in rendered text.
  Airport sampling type:  UNSPECIFIED in public description. CDC page states sites
                          selected for 'potential for disease incursion (such as airports)'
                          only; does not specify terminal vs aircraft/lavatory WBE.
  Scope note:             Programme covers community wastewater + airport sites.
                          Type of airport sampling unspecified. NOT equivalent to
                          in-flight aircraft WBE. Expenditure is a contextual benchmark.

## Modelling caveat
  N=27.1M in single-compartment SIR assumes homogeneous national mixing.
  Model designed for a metropolitan catchment (N=10M); this is an extrapolation.
  Results are order-of-magnitude estimates.

## Files NOT modified
  engine.py, parameters.py (locked). All existing results/ files preserved.
