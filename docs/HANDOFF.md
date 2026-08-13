# Handoff

## Current state

- Release: v0.3.0
- Maintenance rounds completed: 2/10
- Runtime: offline Python 3.10+, no runtime dependencies
- Data: synthetic only
- Model calls: none
- External writes: none

## Reproduce

```bash
python -m pip install -e .
python -m unittest discover -s tests -v
python -m product_discovery.cli data/sample_discovery.json \
  --json-output examples/discovery_review.json \
  --markdown-output examples/discovery_review.md
```

## Next authorized maintenance round

M3: add prioritization sensitivity and alternative-scenario comparison. Preserve interview lineage, unsupported-claim blocking, existing evidence gates, and the non-executing PRD boundary. Do not add an LLM, database, or external integration in M3.

## M2 evidence

- raw synthetic note IDs and excerpts remain visible;
- normalized observations and interpretations are clearly separated;
- numeric or weakly supported observations are blocked even when declared approved;
- interpretations remain outside evidence promotion;
- one grounded approved observation generates a proposed record citing note and excerpt IDs;
- proposed records do not mutate current evidence, opportunity scores, requirements, or the PRD;
- 33 offline tests pass.

## Completion gate for M3

- baseline and alternative scoring scenarios are explicit and deterministic;
- rank sensitivity is visible without claiming market validation;
- current PRD and requirements remain unchanged until human approval;
- old and new tests pass;
- maintenance count advances to 3/10 only after publication is verified.
