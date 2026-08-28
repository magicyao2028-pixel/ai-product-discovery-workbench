# Handoff

## Current state

- Release: v0.7.0
- Maintenance rounds completed: 6/10
- Runtime: offline Python 3.10+, no runtime dependencies
- Data: synthetic only
- Model calls: none
- External writes: none

## Reproduce

```bash
python -m pip install -e .
python -m unittest discover -s tests -v
python -m product_discovery.cli data/sample_discovery.json \
  --scenario-config data/sample_priority_scenarios.json \
  --template-config data/sample_report_template.json \
  --json-output examples/discovery_review.json \
  --markdown-output examples/discovery_review.md
python -m product_discovery.template_feedback_cli
python -m product_discovery.trial_cli
```

## Next planned maintenance round

M7: add a bounded output comparison or reviewer queue. Do not introduce a remote model, dependency or evidence mutation without a separate contract.

## M3 evidence

- raw synthetic note IDs and excerpts remain visible;
- normalized observations and interpretations are clearly separated;
- numeric or weakly supported observations are blocked even when declared approved;
- interpretations remain outside evidence promotion;
- one grounded approved observation generates a proposed record citing note and excerpt IDs;
- proposed records do not mutate current evidence, opportunity scores, requirements, or the PRD;
- 42 offline tests pass, including scenario validation, exact raw-text preservation and number-unit drift regression cases with intervening modifiers.
- named baseline, confidence-first, and effort-sensitive scenarios use validated explicit exponents;
- the synthetic alternative winner is visible while evidence eligibility remains unchanged;
- sensitivity output states that the current PRD and evidence register were not mutated.

## M4 evidence

- configurable section order and titles remain traceable to the same evidence and requirement IDs;
- missing governance, duplicate, unknown, and malformed template sections fail closed;
- current evidence, PRD, requirements, and approval ownership remain unchanged;
- accepted synthetic feedback replays as a regression while pending feedback is excluded;
- the evidence index links seven claims to runnable code, tests, examples, intake, feedback, and limitations;
- external component screening records exact versions, commits, licenses, and the no-copy decision;
- boolean and non-finite opportunity scores are rejected before ranking.

## M5 evidence

- optional `fallback` and `local_extractive` grounded modes produce cited summaries from the packet evidence register;
- both modes are dependency-free, make no model call, do not mutate the PRD or evidence and retain human approval;
- the eight-claim evidence index and trial verify citation scope, mode behavior and zero external actions.

## M6 evidence

- the versioned offline service contract validates schema, packet shape and grounded mode before analysis;
- deterministic request receipts are stable across retries for the same canonical payload and mode;
- the service returns review/governance output without persistence, external writes or automatic approval;
- the nine-claim evidence index and trial verify the receipt, mode behavior and zero external actions.
