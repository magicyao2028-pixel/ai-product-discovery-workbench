from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .trial import run_trial, write_trial_report
from .output_errors import write_validation_failure


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the offline product-discovery reviewer trial.")
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--json-output", type=Path, default=Path("reports/trial_report.json"))
    parser.add_argument("--markdown-output", type=Path, default=Path("reports/trial_report.md"))
    args = parser.parse_args()
    try:
        report = run_trial(args.root.resolve())
    except ValueError as exc:
        write_validation_failure(exc, args.json_output, args.markdown_output)
        print(f"Trial validation failed: {exc}", file=sys.stderr)
        raise SystemExit(2) from None
    write_trial_report(report, args.json_output, args.markdown_output)
    print(f"Trial readiness: {'PASS' if report['overall_passed'] else 'FAIL'}")


if __name__ == "__main__":
    main()
