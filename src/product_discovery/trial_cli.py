from __future__ import annotations

import argparse
from pathlib import Path

from .trial import run_trial, write_trial_report


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the offline product-discovery reviewer trial.")
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--json-output", type=Path, default=Path("reports/trial_report.json"))
    parser.add_argument("--markdown-output", type=Path, default=Path("reports/trial_report.md"))
    args = parser.parse_args()
    report = run_trial(args.root.resolve())
    write_trial_report(report, args.json_output, args.markdown_output)
    print(f"Trial readiness: {'PASS' if report['overall_passed'] else 'FAIL'}")


if __name__ == "__main__":
    main()
