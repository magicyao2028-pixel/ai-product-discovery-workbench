# Security and Data Policy

## Current posture

- The application runs offline and has no runtime dependencies.
- Every public evidence record must explicitly be synthetic.
- No customer identifier, interview recording, confidential document, API token, or production credential is required.
- No external action or production release is implemented.
- Synthetic interview notes require explicit consent before normalization.
- Proposed evidence preserves note/excerpt provenance and is never merged automatically.
- Numeric mismatches and weak excerpt support block observation promotion.
- Boolean, NaN, and infinite opportunity scores are rejected before ranking.
- Templates cannot remove governance or mutate evidence, requirements, or the current PRD.
- Template feedback executes only local validation fixtures and never an external action.

## Safe-use rules

1. Do not place real interview notes or company documents in a public clone.
2. Obtain consent and define retention before handling real research data.
3. Keep future secrets outside version control.
4. Default every future integration to read-only or dry-run.
5. Require authenticated human approval before any production mutation.
6. Preserve an audit trail from evidence version to approved requirement.

## Not production-ready

The prototype has no authentication, roles, encryption, database, deletion workflow, privacy retention, monitoring, rate limiting, or incident response. These gaps block production use.
