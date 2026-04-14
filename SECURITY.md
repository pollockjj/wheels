# Security Policy

## Scope

This repository produces internal wheel artifacts that are intended to be auditable and safe enough for ComfyOrg review. Security issues in build logic, workflow dependencies, provenance generation, published artifacts, or index generation are in scope.

## Reporting

Do not file public issues for suspected security problems.

Report security concerns privately to the repository owner and ComfyOrg maintainers through the private channel you already use for repository and infrastructure work. Include:

- affected workflow, script, or artifact path
- exact commit SHA or workflow run
- reproduction steps
- expected versus observed behavior
- any indicators of supply-chain impact

## Response Expectations

- fail closed on trust and provenance regressions
- prefer revoking or replacing suspect artifacts over explaining them away
- require explicit evidence before declaring a security issue resolved
