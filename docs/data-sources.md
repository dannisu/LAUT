# Data sources

The framework identifies likely references but LAUT does not embed credentials
or redistribute data. Users remain responsible for provider registration,
licensing, citation, and local retention policy.

| Variable/process | Proposed reference | LAUT access pattern |
|---|---|---|
| SST | OSTIA or OISST | NetCDF, OPeNDAP, Zarr |
| SLA and EKE | Copernicus Marine altimetry | Downloaded NetCDF or authorised service endpoint |
| Temperature/salinity profiles | EN4 and Argo | NetCDF; specialist profile collocation may use COAsT |
| Coastal sea level and tides | GESLA | CSV/NetCDF; harmonic diagnostic supplied to LAUT |
| ITF transports | INSTANT moorings | Precomputed section diagnostics or local files |
| Parent comparison | Driving GCM/global ocean | NetCDF/Zarr/OPeNDAP |
| Previous configuration | V3/current CCRS-NEMO-SEA | NetCDF/Zarr |

## Canonical names

Catalog mappings isolate provider/model naming differences from diagnostics.
For example, NEMO `sosstsst`, CMIP `tos`, and OSTIA `analysed_sst` can all map
to `sst`. Scale and offset maps provide simple deterministic unit conversion.

## Collocation

The current xarray adapter supports:

- `exact`: coordinates and indexes must match;
- `inner`: use intersecting coordinates;
- `nearest`: interpolate the model to reference coordinates by nearest point;
- `interp`: linearly interpolate the model to reference coordinates.

Production evaluation should also record masks, coastline treatment, temporal
averaging, calendar conversion, representativeness, and uncertainty. Those
choices can matter as much as the headline metric.

## Credentials

Never commit tokens, `.netrc`, cloud keys, or signed URLs. Prefer provider CLI
credential stores, environment variables, or a site-specific secret manager.

