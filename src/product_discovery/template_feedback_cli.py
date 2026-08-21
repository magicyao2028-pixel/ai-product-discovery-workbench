from __future__ import annotations

import argparse
from pathlib import Path

from .template_feedback import replay_template_feedback, write_feedback_report


def main() -> None:
    parser = argparse.ArgumentParser(description="Replay governed synthetic template feedback.")
    parser.add_argument("--feedback", type=Path, default=Path("data/sample_template_feedback.json"))
    parser.add_argument("--json-output", type=Path, default=Path("reports/template_feedback_report.json"))
    parser.add_argument("--markdown-output", type=Path, default=Path("reports/template_feedback_report.md"))
    args = parser.parse_args()
    report = replay_template_feedback(args.feedback)
    write_feedback_report(report, args.json_output, args.markdown_output)
    print(
        f"Template feedback replay: {report['summary']['passed']}/"
        f"{report['summary']['replayed']} passed"
    )


if __name__ == "__main__":
    main()
