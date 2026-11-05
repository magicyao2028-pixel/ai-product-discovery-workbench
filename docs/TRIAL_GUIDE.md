# 20-Minute Trial Guide

This trial is offline, uses synthetic inputs, needs no account or paid API, and executes no external action.

## 1. Install and test

```bash
python -m pip install -e .
python -m unittest discover -s tests -v
```

Expected result: all tests pass. If import fails, confirm Python 3.10+ and run the commands from the repository root.

## 2. Run the governed template path

```bash
python -m product_discovery.cli data/sample_discovery.json \
  --scenario-config data/sample_priority_scenarios.json \
  --template-config data/sample_report_template.json \
  --json-output examples/discovery_review.json \
  --markdown-output examples/discovery_review.md
```

Inspect `report_template.governance` in the JSON output. Evidence, requirements, and the current PRD must all report no mutation.

## 3. Replay feedback and the complete evidence chain

```bash
python -m product_discovery.template_feedback_cli
python -m product_discovery.trial_cli
```

Expected result: one accepted synthetic regression passes, one pending item is excluded, and the trial reports `PASS` with thirteen evidence claims and zero external actions.

## Failure path and recovery

Run the CLI with `data/invalid_template_missing_governance.json`. It must fail with `missing_required_template_section`. Restore the required `governance` section or use `data/sample_report_template.json`; do not bypass validation.

Requirements must supply `external_action` as a real JSON boolean (`true` or `false`).
A quoted boolean, numeric value, null, collection, or missing field fails validation.
`discovery-workbench` and `discovery-trial` exit with code 2 on input `ValueError`
and replace both requested report files with an explicit `failed_validation` result:
JSON has `overall_passed: false` and `core_passed: false`; Markdown says `FAIL`.
This prevents a prior successful report at those paths from being mistaken for the
current invalid run. Fix the input and rerun to regenerate the successful reports.
Successful report schemas and valid-input behavior are unchanged. This failure
reporting contract assumes distinct writable JSON and Markdown output paths; it
does not guarantee recovery from filesystem failures or an interrupted write.

## What this trial does not prove

It does not prove market demand, usability, customer adoption, model quality, production security, or commercial results. Public feedback in this repository is synthetic and labelled as such.
