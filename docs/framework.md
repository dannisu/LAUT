# Evaluation framework

LAUT v0.1 translates the expanded ocean acceptance framework dated 13 July
2026 into a versioned TOML scorecard. The translation follows four rules.

## 1. Three baselines remain distinct

| Baseline | Question | Criteria |
|---|---|---|
| Observations and reanalysis | Is the regional model realistic? | O2, O3, O4 |
| Parent GCM/global ocean | Does downscaling add value? | O5 |
| Previous configuration | Has performance been degraded? | Non-degradation and coupled comparisons |

Every atomic criterion records its baseline and reference. A diagnostic without
a reference cannot produce an acceptance result.

## 2. Development stage is a gate

S0-S3 are development checks. Only an S4 evaluation run (at least 20 years in
the proposed framework) is eligible for acceptance. Earlier runs may be scored
to guide tuning, but the report says `NOT READY`.

## 3. Targets and thresholds mean different things

- **Target** is the level toward which the configuration is tuned.
- **Threshold** is the outer acceptance bound.
- **Missing** means no finite diagnostic was supplied and scores zero.

Results are therefore `target`, `pass`, `fail`, or `missing`. Where the source
uses an either/or rule, such as MLD within 10 m **or** 20%, criteria share an
`any` group and count as one scoring unit.

## 4. Variable ranking controls comparison order

| Rank | Target | Main diagnostics |
|:---:|---|---|
| T1 | Surface fluxes and SST | SST bias/RMSE/PCC; marine heatwaves |
| T2 | Vertical mixing | MLD, thermocline, subsurface temperature |
| T3 | ITF and strait transports | Total/partition, vertical structure, seasonality, ENSO response |
| T4 | Sea-level gradients and tides | SLA, coastal SSH, M2/S2/K1/O1 |
| T5 | Salinity and stratification | SSS bias/RMSE and regional plume structure |
| T6 | EKE and mesoscale value-add | Spectra, gradients, eddies, unresolved processes |
| T7 | Deep drift | Temperature/salinity trend, steric attribution, heat budget |

Configuration ordering is lexicographic across this profile. The separate
weighted score is descriptive only.

## Machine-testable interpretation notes

- SSH is evaluated as de-meaned sea-level anomaly, not absolute model SSH.
- Forced runs use absolute O2 skill thresholds. GCM-driven runs should focus on
  O5 added skill and parent-bias inheritance.
- Manual boolean diagnostics are explicit placeholders for requirements whose
  physical calculation is configuration-specific, such as correct ITF core
  layer or closed heat budget. They must be backed by a documented analysis.
- `factor_within = 2` means a model/reference ratio between 0.5 and 2.
- The local SST exception up to 2 degC is retained as a note, not silently
  reduced to a domain-wide pass condition. Exceptions must be documented and
  physically understood.

## Calibration requirement

The source document states that O2-O6 values have not yet been calibrated
against the current CCRS-NEMO-SEA 20-year hindcast. Before an operational
release:

1. run the full diagnostic set on that hindcast;
2. record data versions, period, masks, collocation, and uncertainty;
3. place targets at or slightly beyond current skill;
4. retain literature-supported outer thresholds; and
5. release a new framework version with scientific review.

