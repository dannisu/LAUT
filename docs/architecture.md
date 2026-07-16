# Architecture

LAUT separates scientific policy from data engineering.

```text
framework TOML ──> criteria and limits ─┐
                                       ├─> records ─> T1..T7 comparison ─> reports
catalog TOML ─> arrays ─> collocation ─> metrics ─┘
```

## Components

- `framework.py` validates stages, ranks, criteria, targets, and thresholds.
- `catalog.py` opens canonical variables from NPZ/CSV and optional
  NetCDF/OPeNDAP/Zarr sources.
- `metrics.py` contains small pure functions with a common API.
- `pipeline.py` binds a manifest to the catalog and framework.
- `criteria.py` produces auditable atomic result records.
- `ranking.py` combines either/or groups and compares configurations.
- `report.py` writes portable, diffable artifacts.

## Extension contracts

### New metric

Implement `metric(model, reference, *, parent=None, **parameters) -> float` and
register it in `METRICS`. A metric must mask non-finite paired samples, state its
units, and include synthetic edge-case tests.

### New source driver

Extend `Catalog._open`, keep credentials outside the catalog, return an object
supporting `source[variable]`, and close resources deterministically.

### Specialist process package

Complex diagnostics may live in separate packages. Write a long-form CSV or
feed scalar values into a run manifest. This is the preferred path for tide
harmonic analysis, marine-heatwave tracking, eddy censuses, and section
transport tools until their algorithms and regional masks are scientifically
agreed.

## Reproducibility metadata planned for v0.2

Reports will add source checksums/ETags, software environment, git revision,
calendar handling, spatial mask, regridding method, and uncertainty estimates.

