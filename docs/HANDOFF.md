# Handoff

## Current state

- Release: v0.2.0
- Maintenance rounds completed: 1/10
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

M2: add structured synthetic interview-note normalization and claim review. Preserve original note excerpts, label observation versus interpretation, block unsupported claims, and keep every normalized statement traceable to its source note. Do not add an LLM, database, or external integration in M2.

## Completion gate for M2

- raw synthetic note IDs and excerpts remain visible;
- normalized observations and interpretations are clearly separated;
- unsupported claims are blocked or flagged for human review;
- generated evidence records cite their source note IDs;
- old and new tests pass;
- maintenance count advances to 2/10 only after publication is verified.
