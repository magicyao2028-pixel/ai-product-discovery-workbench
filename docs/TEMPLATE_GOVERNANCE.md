# Template Governance

M4 templates control report section order and human-readable titles. They do not change discovery evidence, ranking inputs, eligibility gates, requirements, acceptance criteria, the current PRD, or approval ownership.

## Required sections

Every profile must contain each key exactly once:

- `decision_summary`
- `evidence_review`
- `requirement_review`
- `prototype_flow`
- `governance`

Unknown, duplicate, missing, blank, and malformed sections fail closed with a stable validation code. The `governance` section cannot be removed for a shorter or more persuasive report.

## Feedback boundary

Structured feedback may be `accepted_for_regression`, `pending`, or `rejected`. Only accepted feedback with a replay fixture, expected error code, and recorded resolution enters the regression run. Pending feedback is visible but excluded. A passing synthetic replay proves a control behaves as declared; it is not user adoption, customer demand, or production validation.

## Human ownership

Templates never approve requirements or execute an external action. A human product owner remains responsible for evidence quality, prioritization, requirement approval, and release decisions.
