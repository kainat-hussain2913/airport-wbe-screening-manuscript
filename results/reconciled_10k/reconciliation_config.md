# Reconciliation Run Configuration

**Script:** `/home/claude/analysis/wbe_v2/reconciliation_10k.py`
**Run timestamp:** 2026-09-16T01:38:34.742830Z

## Parameters

| Parameter | Value | Note |
|-----------|-------|------|
| n_total | 10,000 | Manuscript base case (parameters.py S2.1); was 14,082 in portfolio.py |
| IC convention | sensitivity=0 for BOTH arms | lam0 = daily_importation_rate(p0, phi, 0.0, n_total); I(0) = lam0; modelling assumption, not equilibrium |
| Horizon | 365 days | Unchanged |
| Delays | 2, 5, 10, 14 days | Unchanged |
| Response modality | molecular | Unchanged |
| VSL | $3,500,000 (base_case) | Unchanged |
| Prevalence | pathogen baseline × 1.0 multiplier | Unchanged; SARS-CoV-2 1.5% retained from prior engine constants — provenance unresolved |
| P_event, P_warning | Unchanged from portfolio.py THREAT_CLASSES | All labelled UNSOURCED SCENARIO ASSUMPTIONS |

## Unresolved assumptions (not changed, but requiring declaration)

- SARS-CoV-2 baseline prevalence (1.5%): retained from prior engine constants, not sourced from manuscript S1.
- All P_event and P_warning values: unsourced scenario assumptions.
- aircraft WBE detection probability (q=0.5): placeholder; does not enter lead-time calculations.

## Reproduce command

```
cd /home/claude/analysis/wbe_v2
python reconciliation_10k.py
```

## Files written

- `results/reconciled_10k/portfolio_detail_10k.csv`
- `results/reconciled_10k/portfolio_summary_10k.csv`
- `results/reconciled_10k/mechanism_decomposition_10k.csv`
- `results/reconciled_10k/raw_grid_with_negatives_10k.csv`
- `results/reconciled_10k/comparison_old_vs_new.csv`
- `results/reconciled_10k/qa_log_10k.txt`
- `results/reconciled_10k/reconciliation_config.md`

## Files NOT modified

- `/home/claude/analysis/wbe_v2/portfolio.py` (unchanged)
- `/home/claude/analysis/wbe_v2/runners.py` (unchanged)
- `/home/claude/analysis/wbe_v2/generate_grids.py` (unchanged)
- `/home/claude/analysis/wbe_v2/results/*.csv` (all previous outputs preserved)
- `/mnt/user-data/uploads/coldsimulator/manuscript_review_files/code/engine.py` (locked)
- `/mnt/user-data/uploads/coldsimulator/manuscript_review_files/code/parameters.py` (locked)
