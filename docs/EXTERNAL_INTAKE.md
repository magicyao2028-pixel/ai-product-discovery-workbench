# External Component Intake

Screened on 2026-08-21 for M4. The decision concerns runtime adoption only; no source code was copied.

| Candidate | Version / commit reviewed | License | Decision | Reason |
| --- | --- | --- | --- | --- |
| Cookiecutter | 2.7.1 / `083dd3c6104124221e2cbc3e13e0929795861ed5` | BSD-3-Clause | Reject for M4 | Strong general project templating, but it adds a dependency and a second template language for five validated report sections. |
| Copier | 9.17.2 / `76239f5250ed14280a6fe45cbf1ffa9c6bb57185` | MIT | Reject for M4 | Update-aware scaffolding is useful for file trees, but M4 changes report layout only and does not need template migration. |
| Jinja | 3.1.6 / `15206881c006c79667fe5154fe80c01c65410679` | BSD-3-Clause | Reject for M4 | Free-form rendering would expand the trust surface and could hide evidence or governance sections. |

The built-in typed profile was retained because it is offline, deterministic, dependency-free, and fails closed when any mandatory review section is missing. Rejection is not a claim that these projects are low quality; it is a bounded fit decision for this repository.

## Revisit trigger

Re-screen a component only when a future requirement needs multi-file scaffolding, safe migration of user-owned templates, or a rendering feature that cannot be expressed by the five-section schema. Record the exact version, commit, license, copied-code status, tests, and rollback path before adoption.
