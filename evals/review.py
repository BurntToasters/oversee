"""Regrade retained pilot evidence without model calls or overwriting original runs."""

import argparse
import json
from pathlib import Path

from .evidence import final_text, grade, plan_phase_checks, total_usage
from .run import ROOT, correctness, provider_blocker, snapshot, write_json


def review(source, output):
    source, output = source.resolve(), output.resolve()
    if not source.is_dir() or output.exists() or output == ROOT or ROOT in output.parents or source in output.parents:
        raise ValueError("Use an existing run source and a new output directory outside source and repository.")
    paths = sorted(source.glob("*/*/native.json"))
    if not paths:
        raise ValueError("No retained native transcripts found.")
    # Check every retained project before executing any of its code or creating output.
    for path in paths:
        meta = json.loads((path.parent / "session.json").read_text(encoding="utf-8"))
        recorded = json.loads((path.parent / "after.json").read_text(encoding="utf-8"))
        if snapshot(path.parent / "project", legacy=meta.get("snapshot_version", 1) == 1) != recorded:
            raise ValueError(f"Retained project differs from its recorded after.json: {path.parent}")
    output.mkdir(parents=True)
    results = []
    for path in paths:
        case_dir = path.parent
        meta = json.loads((case_dir / "session.json").read_text(encoding="utf-8"))
        raw = json.loads(path.read_text(encoding="utf-8"))
        case = case_dir.parent.name
        phase_path = case_dir / "plan-phase.json"
        phase = None
        if phase_path.exists():
            retained = json.loads(phase_path.read_text(encoding="utf-8"))
            phase = retained["checks"]
            if "no_worker_choice_in_plan" not in phase and "transcripts" in retained:
                # Older evidence predates this check; derive it from retained plan-phase transcripts.
                phase = {**phase, "no_worker_choice_in_plan": plan_phase_checks(
                    retained["transcripts"], phase.get("unchanged"), meta["worker"], meta["manager"])["no_worker_choice_in_plan"]}
        result = {"source": str(case_dir), "case": case, "with_skill": meta["with_skill"],
                  "orchestration": grade(raw, case, meta["with_skill"], meta["worker"], phase),
                  "usage": total_usage(raw), "provider_blocker": provider_blocker(raw)}
        result["orchestration"]["checks"]["exact_manager_settings"] = bool([
            m for m in raw[0]["messages"] if m.get("type") == "assistant"]) and all(
            m.get("model") == meta["manager"] for m in raw[0]["messages"] if m.get("type") == "assistant")
        result["orchestration"]["verified"] = all(v is True for v in result["orchestration"]["checks"].values())
        result["correctness"] = correctness(case_dir / "project", case)
        if case == "explain":
            result["correctness"]["project_unchanged"] = json.loads((case_dir / "baseline.json").read_text()) == json.loads((case_dir / "after.json").read_text())
        original = case_dir / "result.json"
        result["elapsed_seconds"] = json.loads(original.read_text())["elapsed_seconds"] if original.exists() else None
        destination = output / case / case_dir.name
        destination.mkdir(parents=True)
        (destination / "final_response.md").write_text(final_text(raw[0]) + "\n", encoding="utf-8")
        write_json(destination / "result.json", result)
        results.append(result)
    write_json(output / "benchmark.json", {"source": str(source), "runs": results,
               "limitation": "Regrade of retained evidence; no new model calls. Small pilot, no general savings guarantee."})
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        results = review(args.source, args.output)
    except (OSError, ValueError, KeyError) as error:
        parser.error(str(error))
    for result in results:
        print(json.dumps({"case": result["case"], "with_skill": result["with_skill"],
                          "orchestration_verified": result["orchestration"]["verified"],
                          "behavior_passed": result["correctness"]["behavior_passed"]}))


if __name__ == "__main__":
    main()
