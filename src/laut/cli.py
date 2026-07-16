"""Command-line interface for LAUT."""

from __future__ import annotations

import argparse
from importlib.resources import files
from pathlib import Path
import shutil
import sys

from .catalog import Catalog
from .framework import default_framework_path, load_framework
from .pipeline import records_from_diagnostics, run_manifest
from .ranking import compare_configurations
from .report import write_reports


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="laut",
        description="Evaluate and compare Southeast Asian regional ocean-model configurations.",
    )
    parser.add_argument("--version", action="version", version="LAUT 0.1.0")
    commands = parser.add_subparsers(dest="command", required=True)

    validate = commands.add_parser("validate-framework", help="Check a framework TOML file")
    validate.add_argument("framework", nargs="?", type=Path)

    catalog = commands.add_parser("validate-catalog", help="Check a data catalog")
    catalog.add_argument("catalog", type=Path)

    init_config = commands.add_parser("init-config", help="Copy the bundled framework and examples")
    init_config.add_argument("destination", type=Path)

    evaluate = commands.add_parser("evaluate", help="Evaluate a diagnostics CSV")
    evaluate.add_argument("diagnostics", type=Path)
    evaluate.add_argument("--framework", type=Path)
    evaluate.add_argument("--stage", default="S4")
    evaluate.add_argument("--mode", default="forced", choices=["forced", "gcm_driven", "coupled"])
    evaluate.add_argument("--output", type=Path, default=Path("outputs/laut-evaluation"))

    run = commands.add_parser("run", help="Run a data-catalog evaluation manifest")
    run.add_argument("manifest", type=Path)
    run.add_argument("--output", type=Path)
    return parser


def _print_scores(comparison: object, framework_status: str) -> None:
    for score in comparison.scores:  # type: ignore[attr-defined]
        decision = (
            "MEETS PROPOSAL"
            if score.accepted and framework_status == "proposal"
            else "ACCEPT"
            if score.accepted
            else "NOT READY"
        )
        print(
            f"{score.position}. {score.configuration}: {decision}; "
            f"coverage {score.coverage:.1f}%; weighted score {score.weighted_score:.1f}"
        )


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "validate-framework":
            framework = load_framework(args.framework)
            print(
                f"OK: {framework.name} {framework.version} ({framework.status}); "
                f"{len(framework.criteria)} atomic criteria"
            )
            return 0
        if args.command == "validate-catalog":
            catalog = Catalog.from_toml(args.catalog)
            errors = catalog.validate()
            if errors:
                print("Invalid catalog:\n- " + "\n- ".join(errors), file=sys.stderr)
                return 2
            print(f"OK: {len(catalog.sources)} data sources")
            return 0
        if args.command == "init-config":
            args.destination.mkdir(parents=True, exist_ok=True)
            shutil.copy2(default_framework_path(), args.destination / "laut-sea-v0.1.0.toml")
            examples = files("laut").joinpath("resources")
            for name in ("catalog.example.toml", "run.example.toml"):
                shutil.copy2(Path(str(examples.joinpath(name))), args.destination / name)
            print(f"Wrote editable configuration to {args.destination}")
            return 0
        if args.command == "evaluate":
            framework = load_framework(args.framework)
            records = records_from_diagnostics(
                args.diagnostics, framework, args.stage, args.mode
            )
            comparison = compare_configurations(records, framework)
            paths = write_reports(comparison, args.output, framework.status)
            _print_scores(comparison, framework.status)
            print(f"Reports: {paths[-1]}")
            return 0
        if args.command == "run":
            result = run_manifest(args.manifest)
            destination = args.output or result.output_dir
            paths = write_reports(result.comparison, destination, result.framework.status)
            _print_scores(result.comparison, result.framework.status)
            print(f"Reports: {paths[-1]}")
            return 0
    except (KeyError, OSError, RuntimeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
