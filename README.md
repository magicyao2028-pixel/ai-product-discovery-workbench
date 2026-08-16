# AI Product Discovery Workbench

An offline, evidence-traceable product workflow that turns a structured discovery packet into scenario-sensitive opportunity rankings, requirement gates, a PRD, a traceability matrix, a low-fidelity screen flow, and a governed feedback decision log.

**中文介绍：** 面向传统企业 AI 转型和中小团队产品探索的离线原型。它把访谈、流程审查、支持记录等模拟证据连接到机会排序、需求、验收标准和低保真页面流程，并用多个显式评分场景展示优先级是否敏感；替代结果不会自动改写 PRD，所有产品决策仍需人工确认。

## Why this project exists

AI product work is not only prompt writing. Teams need to show why a problem matters, which evidence supports it, how a requirement will be accepted, what is deliberately excluded, and who owns the final decision. This repository demonstrates that product chain without pretending that synthetic research is real market validation.

The business scenario is an internal AI-application exploration for Changsha Shiju Trading Co., Ltd. All evidence, interviews, workflow observations, product details, and outputs are synthetic.

## What v0.4 demonstrates

- typed discovery evidence with dates and source categories;
- transparent impact-confidence-effort opportunity ranking;
- validated baseline, confidence-first, and effort-sensitive ranking scenarios;
- visible alternative winners with fixed evidence-eligibility gates and zero PRD mutation;
- minimum evidence-diversity and confidence gates;
- requirements linked to opportunities, evidence, and acceptance criteria;
- exclusion of unsupported or write-capable external actions;
- an evidence-to-requirement traceability matrix;
- a low-fidelity screen flow with unsupported screens removed;
- deterministic JSON and Markdown output, tests, and a static demo.
- dated feedback linked to stable requirement and evidence IDs;
- transparent support, challenge, and no-effect counts for each requirement;
- version recommendations that remain pending until a human approves them;
- a hard guarantee that the workflow does not automatically change a requirement.
- structured synthetic interview notes with consent, stable note IDs, and preserved excerpts;
- explicit separation of observations from interpretations;
- lexical and numeric support checks that block unsupported claims;
- provenance-rich proposed evidence that never mutates the current evidence register or PRD.

## Quick start

```bash
python -m pip install -e .
python -m unittest discover -s tests -v
python -m product_discovery.cli data/sample_discovery.json \
  --scenario-config data/sample_priority_scenarios.json \
  --json-output examples/discovery_review.json \
  --markdown-output examples/discovery_review.md
```

The package requires Python 3.10 or later and has no runtime dependencies.

## Workflow

```text
Synthetic discovery packet
  -> validate evidence and relationships
  -> preserve interview excerpts and review normalized claims
  -> rank opportunities
  -> compare declared priority scenarios without changing evidence
  -> select an evidence-eligible problem
  -> include or exclude requirements
  -> compile PRD and traceability matrix
  -> map low-fidelity screen flow
  -> aggregate dated feedback by stable requirement ID
  -> emit a non-executing version decision log
  -> request human approval
  -> no production release or external action
```

## Repository map

- `src/product_discovery/`: validation, scoring, gates, reporting, and CLI
- `data/sample_discovery.json`: synthetic research and product inputs
- `examples/`: reproducible JSON and Markdown outputs
- `docs/PRD.md`: product intent, users, scope, and acceptance contract
- `docs/ARCHITECTURE.md`: components, data flow, and boundaries
- `docs/SCORING_AND_GATES.md`: prioritization and exclusion logic
- `docs/PRIORITIZATION_SENSITIVITY.md`: scenario formula, invariants, and alternative-winner evidence
- `docs/PROTOTYPE_FIDELITY.md`: low-fidelity versus high-fidelity prototypes
- `docs/FEEDBACK_DECISIONS.md`: feedback classification, versioning, and approval rules
- `docs/INTERVIEW_CLAIM_REVIEW.md`: note lineage, support checks, and evidence-promotion boundaries
- `docs/PRODUCT_TOOL_HANDOFF.md`: how artifacts map to PRD, Axure, Visio, and mind-map tools
- `docs/MAINTENANCE_PLAN.md`: ten planned substantive iterations
- `site/`: static public demonstration

## Honest boundaries

This is a portfolio prototype, not completed product discovery for a real customer. It does not conduct or transcribe interviews, infer needs with an LLM, validate market demand, produce a high-fidelity design, deploy software, execute an external business action, merge proposed interview evidence automatically, apply requirement changes automatically, or optimize priority weights from real outcomes. Scores, scenarios, and classifications organize declared synthetic inputs; they do not prove business value.

## License

MIT. See [LICENSE](LICENSE).
