# Interview Claim Review

## Controlled path

```text
Synthetic consented note
  -> preserved raw excerpts
  -> normalized observation or interpretation
  -> numeric and lexical support check
  -> declared human review status
  -> proposed indicative evidence or blocked/pending claim
  -> no automatic evidence-register or PRD mutation
```

## Claim boundaries

- An `observation` may produce proposed evidence only when it is declared approved and its cited excerpts pass support checks.
- An `interpretation` remains a review item even when its input is mistakenly marked approved.
- A number absent from the cited excerpts produces `unsupported_numeric_claim`.
- A supported number paired with a different time, percentage, or currency unit produces `unsupported_numeric_unit_claim`.
- Lexical overlap below the explicit 0.30 threshold produces `insufficient_excerpt_support`.
- A reviewer-blocked or pending observation remains outside proposed evidence.

## Provenance and limitations

Each raw excerpt preserves its input whitespace and line breaks exactly; a separate normalized view is used only inside support checks. Each proposed record retains the source note ID, excerpt IDs, claim ID, observation date, synthetic flag, and `indicative` reliability. It is labelled `proposed_not_merged` and does not enter the opportunity score, requirement gate, feedback decision log, or current PRD.

The checks are deterministic safeguards, not semantic fact verification. Real research would require consent, secure storage, trained reviewers, retention controls, redaction, and qualitative analysis beyond token overlap.
