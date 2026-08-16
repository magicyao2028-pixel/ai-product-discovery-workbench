# Product Requirements Document

## Product statement

AI Product Discovery Workbench helps a product owner turn a structured evidence package into a reviewable product decision without losing the chain from observed problem to acceptance criterion.

## Primary users

- an AI application product manager exploring a business workflow;
- an operations lead reviewing whether the proposed solution matches the problem;
- a technical partner checking scope, evidence, and acceptance boundaries before implementation.

## User problem

Small teams often jump from stakeholder requests to features. Evidence is scattered, prioritization assumptions stay implicit, unsupported requirements survive into delivery, and low-fidelity prototypes are mistaken for finished designs.

## v0.4 scope

1. Validate synthetic dated discovery evidence.
2. Rank declared opportunities with a visible formula.
3. Require at least two evidence items, two evidence types, and confidence of 0.5 for opportunity eligibility.
4. Link included requirements to the selected opportunity, supporting evidence, and acceptance criteria.
5. Exclude unsupported and external-action requirements.
6. Produce a PRD, traceability rows, and a low-fidelity screen flow.
7. Preserve human ownership and zero execution.
8. Validate dated synthetic feedback against stable requirement and evidence IDs.
9. Aggregate whether feedback supports, challenges, or does not affect each requirement.
10. Propose a requirement version review without changing the requirement or claiming approval.
11. Preserve structured synthetic interview notes and raw excerpts.
12. Separate normalized observations from interpretations.
13. Block claims whose numbers or wording are not supported by cited excerpts.
14. Generate proposed, provenance-rich interview evidence without merging it into the current evidence register.
15. Compare named prioritization scenarios while keeping evidence and eligibility gates fixed.
16. Report winner and rank changes without mutating the current PRD, requirements, or evidence register.

## Acceptance criteria

- IDs and cross-references validate deterministically;
- public inputs must declare themselves synthetic;
- evidence cannot be dated after the analysis date;
- every included requirement has at least two supporting evidence items;
- included requirement evidence belongs to its opportunity;
- external-action requirements and dependent screens are excluded;
- output contains an explicit human approval gate and no execution claim;
- tests and examples run offline without a paid API.
- feedback cannot reference unknown requirements or evidence, or be dated after the analysis date;
- every change recommendation cites feedback and evidence IDs;
- a challenged requirement may receive a proposed next version, but the current PRD remains unchanged;
- every change decision stays pending for a named human owner and reports `requirement_change_executed: false`.
- every proposed interview evidence record cites one source note and its excerpts;
- interpretations and unsupported observations never become proposed evidence;
- interview processing reports `existing_evidence_register_mutated: false` and does not alter the current PRD.
- priority scenarios validate bounded exponents, expose formulas and preserve the baseline score;
- alternative winners remain review artifacts and cannot rewrite the current PRD.

## Out of scope

- live research collection, transcription, or customer data;
- LLM-based synthesis or autonomous product decisions;
- market sizing, causal validation, forecasting, or financial claims;
- high-fidelity visual design and usability validation;
- API, database, authentication, deployment, or production integrations.

## v0.4 success evidence

Success means the synthetic example is reproducible, unsupported scope and interview claims are visibly excluded, every included requirement remains traceable, and later feedback, proposed interview evidence, or alternative priority scenarios cannot mutate the current PRD automatically. It does not mean the sample product has been validated, approved, or shipped.
