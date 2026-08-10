# Architecture

## System context

The workbench is a local decision-support compiler. A human prepares a synthetic discovery packet; the deterministic engine validates relationships and produces review artifacts. There is no model call, database, external connector, or production write.

```text
Discovery JSON
  -> schema and reference validation
  -> opportunity scoring and evidence gates
  -> requirement inclusion/exclusion
  -> PRD and traceability matrix
  -> low-fidelity screen filter
  -> JSON + Markdown artifacts
  -> human product decision
```

## Components

| Component | Responsibility |
| --- | --- |
| `models.py` | Parse typed artifacts and validate dates, IDs, ranges, and relationships |
| `engine.py` | Rank opportunities, gate requirements, compile PRD, trace evidence, and filter screens |
| `report.py` | Render a human-readable decision report with citations and exclusions |
| `cli.py` | Provide a reproducible local entry point and save artifacts |

## Product and Agent boundary

The repository demonstrates an AI-product delivery workflow but v0.1 is not an autonomous Agent. The trace is workflow state, not model reasoning. A future grounded model adapter must preserve deterministic gates and may draft text only from approved evidence.

## Data and action boundary

- every public evidence record must declare `synthetic: true`;
- future-dated evidence is rejected;
- unsupported requirements remain visible as exclusions;
- screens that depend on excluded requirements are omitted;
- external action and production release flags remain `false`.

## Production gaps

Production use would require research-consent controls, identity and roles, encrypted storage, evidence retention, audit logs, prompt/model evaluation if a model is added, API contracts, concurrency, monitoring, incident response, and usability testing.
