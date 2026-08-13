# Scoring and Gates

## Opportunity score

```text
score = impact * confidence * 10 / effort
```

- impact: integer from 1 to 5;
- confidence: decimal from 0 to 1;
- effort: integer from 1 to 5.

The formula is intentionally simple and visible. It supports comparison inside one synthetic packet; it is not a market forecast or financial model.

## Opportunity eligibility

An opportunity is eligible only when it has:

- at least two evidence items;
- at least two distinct evidence types;
- confidence of at least 0.5.

The highest-scoring eligible opportunity becomes the proposed focus. When none is eligible, PRD compilation is blocked.

## Requirement gate

A requirement is included only when:

1. it belongs to the selected opportunity;
2. it cites at least two distinct evidence items;
3. every cited item also supports that opportunity;
4. it does not perform an external action.

Excluded requirements remain in the review with machine-readable reasons. This avoids silently deleting stakeholder requests while preventing weak or unsafe scope from entering the PRD.

## Traceability

Each included evidence-requirement pair becomes one row containing:

- evidence ID and type;
- opportunity ID;
- requirement ID;
- acceptance criteria.

This is a minimal traceability model. Requirement feedback and proposed interview evidence are separate non-mutating review artifacts; neither changes the approved traceability matrix automatically.
