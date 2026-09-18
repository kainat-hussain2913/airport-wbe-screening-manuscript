# National-scale analyses

Illustrative applications of the framework at Australian and United States arrival
volumes and catchment populations, reported in manuscript §3.10.

| File | Contents |
|---|---|
| `australia_scenario_config.md` | Australian configuration, input provenance and caveats |
| `us_scenario_config.md` | United States configuration, input provenance and caveats |
| `portfolio_summary_aus.csv`, `portfolio_detail_aus.csv` | Australian portfolio outputs, pre-ICU baseline run |
| `portfolio_summary_us.csv`, `portfolio_detail_us.csv` | US portfolio outputs, pre-ICU baseline run |
| `mechanism_decomposition_us.csv` | US mechanism decomposition |

**The thresholds reported in the manuscript are the ICU-enabled values in
`../icu/national_icu_key_results.json` and `../icu/national_icu_portfolio.csv`,
not the pre-ICU CSVs in this folder.** The ICU-enabled run reports the ICU effect
as a delta against the pre-ICU values, which is why both are retained:

| | Reported (ICU-enabled) | Pre-ICU baseline | ICU effect |
|---|---|---|---|
| Australia, Scenario A | USD 22,600,025 | USD 22,462,886 | +0.61% |
| Australia, Scenario B | USD 39,705,576 | USD 39,449,649 | +0.65% |
| United States, Scenario A | USD 154,210,880 | USD 152,897,745 | +0.86% |
| United States, Scenario B | USD 282,597,478 | USD 279,968,708 | +0.94% |

All at d = 5 days, base probability assumptions, excluding the avian-influenza
stress test.
