# Prioritization Sensitivity

## Purpose

v0.4 makes ranking assumptions inspectable. It evaluates the same declared opportunities under multiple named scoring scenarios and reports whether the highest-ranked eligible opportunity changes. This is a decision aid, not market validation.

## Formula

```text
score = impact^a * confidence^b * 10 / effort^c
```

The baseline uses `a=1`, `b=1`, and `c=1`, exactly preserving the prior ICE-style score. Alternative scenarios change only the declared exponents:

- `confidence-first` gives confidence exponent 2;
- `speed-first` gives effort exponent 2.

Every exponent must be finite and between 0.5 and 3. Scenario IDs must be unique, and comparison requires at least two scenarios.

## Invariants

- Evidence IDs, evidence types, impact, confidence, and effort are never rewritten by a scenario.
- Existing evidence-diversity and minimum-confidence eligibility gates remain fixed.
- An ineligible opportunity can never become the selected scenario winner merely because its score changes.
- Alternative winners do not rewrite the current selected opportunity, PRD, requirements, traceability matrix, feedback decisions, or proposed interview evidence.
- All results remain pending human decision.

## Synthetic reference result

The baseline and confidence-first scenarios select `OPP-001`. The effort-sensitive scenario selects `OPP-003`, which has lower declared effort. This rank change exposes dependence on prioritization assumptions; it does not show that either opportunity has real demand or should be built.

```bash
discovery-workbench data/sample_discovery.json \
  --scenario-config data/sample_priority_scenarios.json \
  --json-output examples/discovery_review.json \
  --markdown-output examples/discovery_review.md
```
