"""Data-source catalog with lightweight local and optional xarray drivers."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
import glob
import tomllib

import numpy as np


@dataclass(frozen=True)
class SourceSpec:
    id: str
    driver: str
    uri: str
    description: str = ""
    variables: dict[str, str] = field(default_factory=dict)
    coordinates: dict[str, str] = field(default_factory=dict)
    scale: dict[str, float] = field(default_factory=dict)
    offset: dict[str, float] = field(default_factory=dict)
    open_options: dict[str, Any] = field(default_factory=dict)


class Catalog:
    """Open named arrays from local files, OPeNDAP, object stores, or Zarr."""

    def __init__(self, sources: dict[str, SourceSpec], base_dir: Path | None = None):
        self.sources = sources
        self.base_dir = base_dir or Path.cwd()
        self._handles: dict[str, Any] = {}

    @classmethod
    def from_toml(cls, path: str | Path) -> "Catalog":
        source_path = Path(path)
        with source_path.open("rb") as handle:
            raw = tomllib.load(handle)
        sources: dict[str, SourceSpec] = {}
        for item in raw.get("sources", []):
            spec = SourceSpec(
                id=str(item["id"]),
                driver=str(item["driver"]),
                uri=str(item["uri"]),
                description=str(item.get("description", "")),
                variables={str(k): str(v) for k, v in item.get("variables", {}).items()},
                coordinates={str(k): str(v) for k, v in item.get("coordinates", {}).items()},
                scale={str(k): float(v) for k, v in item.get("scale", {}).items()},
                offset={str(k): float(v) for k, v in item.get("offset", {}).items()},
                open_options=dict(item.get("open_options", {})),
            )
            if spec.id in sources:
                raise ValueError(f"Duplicate source ID: {spec.id}")
            sources[spec.id] = spec
        return cls(sources, source_path.parent)

    def validate(self) -> list[str]:
        errors: list[str] = []
        supported = {"csv", "netcdf", "npz", "opendap", "zarr"}
        for source in self.sources.values():
            if source.driver not in supported:
                errors.append(f"{source.id}: unsupported driver {source.driver!r}")
            if source.driver in {"csv", "netcdf", "npz"}:
                path = self._resolve_uri(source.uri)
                if source.driver == "netcdf" and any(char in str(path) for char in "*?["):
                    exists = bool(glob.glob(str(path)))
                else:
                    exists = path.exists()
                if not exists:
                    errors.append(f"{source.id}: local path does not exist: {path}")
        return errors

    def _resolve_uri(self, uri: str) -> Path:
        path = Path(uri).expanduser()
        return path if path.is_absolute() else (self.base_dir / path).resolve()

    def _open(self, source: SourceSpec) -> Any:
        if source.id in self._handles:
            return self._handles[source.id]
        if source.driver == "npz":
            handle = np.load(self._resolve_uri(source.uri), allow_pickle=False)
        elif source.driver == "csv":
            handle = np.genfromtxt(
                self._resolve_uri(source.uri), delimiter=",", names=True, dtype=float
            )
        else:
            try:
                import xarray as xr
            except ImportError as exc:
                raise RuntimeError(
                    f"Source {source.id!r} uses {source.driver}; install LAUT with "
                    "`pip install 'laut-ocean[ocean]'`."
                ) from exc
            options = dict(source.open_options)
            if source.driver in {"netcdf", "opendap"}:
                uri = source.uri if source.driver == "opendap" else str(self._resolve_uri(source.uri))
                if source.driver == "netcdf" and any(char in uri for char in "*?["):
                    matches = sorted(glob.glob(uri))
                    handle = xr.open_mfdataset(matches, **options)
                else:
                    handle = xr.open_dataset(uri, **options)
            elif source.driver == "zarr":
                handle = xr.open_zarr(source.uri, **options)
            else:
                raise ValueError(f"Unsupported source driver: {source.driver}")
            rename = {
                actual: canonical
                for canonical, actual in {**source.variables, **source.coordinates}.items()
                if actual in handle and actual != canonical
            }
            if rename:
                handle = handle.rename(rename)
        self._handles[source.id] = handle
        return handle

    def array(self, source_id: str, variable: str) -> Any:
        try:
            source = self.sources[source_id]
        except KeyError as exc:
            raise KeyError(f"Unknown catalog source: {source_id}") from exc
        handle = self._open(source)
        actual = source.variables.get(variable, variable)
        if source.driver in {"netcdf", "opendap", "zarr"}:
            actual = variable  # xarray sources were canonicalized on open.
        try:
            values = handle[actual]
        except (KeyError, ValueError, IndexError) as exc:
            raise KeyError(f"Variable {variable!r} not found in source {source_id!r}") from exc
        scale = source.scale.get(variable, 1.0)
        offset = source.offset.get(variable, 0.0)
        return values * scale + offset

    def close(self) -> None:
        for handle in self._handles.values():
            close = getattr(handle, "close", None)
            if callable(close):
                close()
        self._handles.clear()

    def __enter__(self) -> "Catalog":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()


def align_arrays(model: Any, reference: Any, mode: str = "exact") -> tuple[Any, Any]:
    """Collocate a model/reference pair before computing a metric."""

    if hasattr(model, "dims") and hasattr(reference, "dims"):
        import xarray as xr

        if mode == "interp":
            model = model.interp_like(reference)
            return xr.align(model, reference, join="inner")
        if mode == "nearest":
            model = model.interp_like(reference, method="nearest")
            return xr.align(model, reference, join="inner")
        join = "exact" if mode == "exact" else "inner"
        return xr.align(model, reference, join=join)
    model_array = np.asarray(model)
    reference_array = np.asarray(reference)
    if model_array.shape != reference_array.shape:
        try:
            model_array, reference_array = np.broadcast_arrays(model_array, reference_array)
        except ValueError as exc:
            raise ValueError(
                f"Cannot align array shapes {model_array.shape} and {reference_array.shape}"
            ) from exc
    return model_array, reference_array
