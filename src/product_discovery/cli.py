from __future__ import annotations

import argparse
import json
from pathlib import Path

from .engine import DiscoveryWorkbench
from .models import load_packet
from .report import render_markdown
from .sensitivity import load_priority_scenarios
from .templates import load_template_profile


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compile a synthetic discovery packet into a reviewable PRD.")
    parser.add_argument("packet", type=Path, help="Discovery packet JSON")
    parser.add_argument("--json-output", type=Path, default=Path("output/discovery_review.json"))
    parser.add_argument("--markdown-output", type=Path, default=Path("output/discovery_review.md"))
    parser.add_argument("--scenario-config", type=Path, help="Optional priority-scenario JSON")
    parser.add_argument("--template-config", type=Path, help="Optional report-template JSON")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    scenarios = load_priority_scenarios(args.scenario_config) if args.scenario_config else None
    template = load_template_profile(args.template_config) if args.template_config else None
    build_kwargs = {}
    if template is not None:
        build_kwargs["template_profile"] = template
    if scenarios is not None:
        build_kwargs["priority_scenarios"] = scenarios
    result = DiscoveryWorkbench().build(load_packet(args.packet), **build_kwargs)
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    args.markdown_output.write_text(render_markdown(result), encoding="utf-8")
    print(f"Discovery review written to {args.json_output} and {args.markdown_output}")


if __name__ == "__main__":
    main()
