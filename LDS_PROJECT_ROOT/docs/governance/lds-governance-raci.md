---
doc_id: "lds-governance-raci"
title: "LDS Governance RACI"
version: "1.0.0"
status: "stable"
last_updated: "2026-02-18"
owner: "docs-architecture"
---

# LDS Governance RACI

## Governance Objective

Guarantee deterministic behavior across LLM handoffs by enforcing canonical artifacts,
strict validation, and explicit exception control.

## RACI Matrix

| Workstream | Responsible | Accountable | Consulted | Informed |
|---|---|---|---|---|
| Spec and rule evolution | Docs Architect | Product/Program Owner | QA Lead, Platform Engineer | All contributors |
| Contract/schema integrity | Platform Engineer | Engineering Lead | Docs Architect | QA Lead |
| Validator and CI gates | Tooling Engineer | Engineering Lead | QA Lead | Docs Architect |
| Waiver approval | QA/Governance Lead | Product/Program Owner | Security Lead | Engineering Lead |
| Release readiness audit | QA/Governance Lead | Product/Program Owner | Docs Architect, Tooling Engineer | Stakeholders |

## Waiver SLA

1. Intake to triage: <= 1 business day.
2. Decision: <= 2 business days.
3. Maximum waiver lifetime: 14 days.
4. Expired waivers block release.

## Non-Negotiable Controls

1. Tier-0 drift without active waiver is a release blocker.
2. CI strict gate bypass is prohibited.
3. Legacy and fixtures are excluded from canonical retrieval scope.
