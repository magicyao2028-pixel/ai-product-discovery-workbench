# Feedback and Requirement Decisions

## Purpose

M1 adds a review trail after the first PRD is compiled. It demonstrates how an AI product team can collect dated feedback without allowing an automated workflow to rewrite approved scope.

## Input contract

Every feedback item contains a stable `feedback_id`, an existing `requirement_id`, an observation date, one or more declared `evidence_ids`, a synthetic disclosure, and one explicit human classification:

- `supports`: the feedback reinforces the current requirement;
- `challenges`: the feedback identifies a reason to review the current requirement;
- `no_effect`: the feedback is relevant to the product discussion but does not change this requirement.

The workflow validates references, dates, uniqueness, and the public synthetic-data boundary before any decision artifact is generated.

## Deterministic recommendation rules

| Condition | Recommendation | Version effect |
| --- | --- | --- |
| Requirement is excluded from the PRD | `no_change_excluded_requirement` | Keep current version |
| At least one item challenges an included requirement | `review_revision` | Propose next minor version |
| Support exists and no challenge exists | `retain` | Keep current version |
| Only no-effect feedback exists | `no_change` | Keep current version |
| No feedback exists | `no_change_insufficient_feedback` | Keep current version |

These are review recommendations, not product decisions. The decision owner must inspect the cited feedback and evidence before accepting, rejecting, or rewriting a proposal.

## Non-execution guarantee

The engine compiles the current PRD first, then creates a separate decision log. It never edits requirement text or acceptance criteria. Every row reports `approval_status: pending_human_approval` and `requirement_change_executed: false`.

## Example version trail

`REQ-001 v1.0` has one supporting and one challenging feedback item. The workbench proposes `v1.1` for review because the challenge asks whether incomplete briefs should be saved as drafts. The output does not add that behavior to the PRD; a human product owner must decide what happens next.
