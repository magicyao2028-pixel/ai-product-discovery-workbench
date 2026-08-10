# Handoff

## Current state

- Release: v0.1.0
- Maintenance rounds completed: 0/10
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

M1: record dated feedback against stable requirement IDs, calculate whether feedback supports, challenges, or does not affect a requirement, and emit a human-readable change decision log. Do not add an LLM, database, or integration in M1.

## Completion gate for M1

- feedback references validate deterministically;
- change decisions cite requirement and evidence IDs;
- unsupported automatic requirement changes are blocked;
- examples and the static site show the version trail;
- old and new tests pass;
- maintenance count advances to 1/10 only after publication is verified.
