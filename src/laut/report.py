"""Portable CSV, JSON, and Markdown output."""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
import csv
import json

from .framework import VALID_RANKS
from .ranking import Comparison


def write_reports(
    comparison: Comparison,
    output_dir: str | Path,
    framework_status: str = "operational",
) -> list[Path]:
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    records_path = destination / "diagnostic-results.csv"
    comparison_path = destination / "configuration-ranking.csv"
    json_path = destination / "laut-results.json"
    markdown_path = destination / "summary.md"

    record_rows = [record.as_dict() for record in comparison.records]
    if record_rows:
        with records_path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(record_rows[0]))
            writer.writeheader()
            writer.writerows(record_rows)
    else:
        records_path.write_text("", encoding="utf-8")

    score_rows = []
    for score in comparison.scores:
        row = {
            "position": score.position,
            "configuration": score.configuration,
            "stage": score.stage,
            "mode": score.mode,
            "accepted": score.accepted,
            "coverage_percent": round(score.coverage, 3),
            "weighted_score": round(score.weighted_score, 3),
            "failures": score.failures,
            "missing": score.missing,
        }
        row.update({f"{rank}_score": round(score.rank_scores[rank], 3) for rank in VALID_RANKS})
        score_rows.append(row)
    if score_rows:
        with comparison_path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(score_rows[0]))
            writer.writeheader()
            writer.writerows(score_rows)
    else:
        comparison_path.write_text("", encoding="utf-8")

    payload = {
        "framework_status": framework_status,
        "scores": [
            {**asdict(score), "rank_scores": dict(score.rank_scores)} for score in comparison.scores
        ],
        "records": record_rows,
    }
    json_path.write_text(json.dumps(payload, indent=2, allow_nan=False), encoding="utf-8")

    lines = [
        "# LAUT configuration comparison",
        "",
        "Ordering is lexicographic from T1 to T7; lower-ranked strengths cannot mask "
        "higher-ranked weaknesses.",
        "",
        "| Rank | Configuration | Stage | Mode | Coverage | Weighted score | Decision |",
        "|---:|---|:---:|---|---:|---:|---|",
    ]
    for score in comparison.scores:
        decision = (
            "MEETS PROPOSAL"
            if score.accepted and framework_status == "proposal"
            else "ACCEPT"
            if score.accepted
            else "NOT READY"
        )
        lines.append(
            f"| {score.position} | {score.configuration} | {score.stage} | {score.mode} | "
            f"{score.coverage:.1f}% | {score.weighted_score:.1f} | {decision} |"
        )
    lines.extend(["", "## Priority profile", ""])
    lines.append("| Configuration | " + " | ".join(VALID_RANKS) + " |")
    lines.append("|---|" + "---:|" * len(VALID_RANKS))
    for score in comparison.scores:
        values = " | ".join(f"{score.rank_scores[rank]:.1f}" for rank in VALID_RANKS)
        lines.append(f"| {score.configuration} | {values} |")
    lines.extend(
        [
            "",
            "> `NOT READY` means at least one required criterion failed or is missing, or the "
            "configuration was not evaluated at Stage S4.",
            f"> Framework status: `{framework_status}`.",
            "",
        ]
    )
    markdown_path.write_text("\n".join(lines), encoding="utf-8")
    return [records_path, comparison_path, json_path, markdown_path]
