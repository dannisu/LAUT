# Roadmap

## v0.1 — foundation (this repository)

- Versioned S0-S4, O2-O6, and T1-T7 scorecard.
- Catalog adapters and direct/precomputed diagnostic paths.
- Core statistics, grouped criteria, hierarchy-aware ranking, and reports.
- Synthetic end-to-end test and GitHub automation.

## v0.2 — regional diagnostic pack

- Region masks for SEA/WMC, Indonesian straits, south Java, west Sumatra, and
  Sunda Shelf.
- NEMO C-grid transport sections with partial cells and sign conventions.
- MLD and 20 degC isotherm algorithms with profile uncertainty.
- Sea-level de-meaning, geostrophic-gradient diagnostics, and tide-gauge
  collocation.
- Hobday marine-heatwave diagnostics using both fixed and moving climatologies.
- Provenance manifest and uncertainty-aware reports.

## v0.3 — value-add and operational scaling

- Along-track SSH spectra and 30-200 km band skill.
- SST-gradient distributions and mesoscale spectral slope.
- Reproducible eddy census using a selected tracker.
- Dask/HPC execution, chunk planning, restartable pipelines, and cached
  collocation weights.
- Comparison dashboard and publication-quality scorecards.

## Operational framework release

- Run on the existing 20-year hindcast.
- Calibrate thresholds with literature bounds and observational uncertainty.
- Convene scientific review and publish a new non-proposal framework version.

