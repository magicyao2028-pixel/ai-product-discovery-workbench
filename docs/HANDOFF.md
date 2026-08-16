# Handoff

## Current state

- Release: v0.4.0
- Maintenance rounds completed: 3/10
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
  --json-output examples/discovery_review.json \
  --markdown-output examples/discovery_review.md
```

## Next authorized maintenance round

M4: add configurable discovery and PRD templates. Preserve scenario transparency, interview lineage, unsupported-claim blocking, existing evidence gates, and the non-executing PRD boundary.

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

## Completion gate for M4

- templates remain traceable to the same evidence and requirement IDs;
- current PRD and requirements remain unchanged until human approval;
- old and new tests pass and maintenance advances only after publication is verified.
