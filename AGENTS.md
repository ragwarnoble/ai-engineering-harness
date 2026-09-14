# AI Engineering Harness

## Mission

Build reliable, testable, maintainable software with AI assistance.

## Core principles

1. Understand before modifying.
2. Inspect repository evidence before making architectural assumptions.
3. Prefer the smallest correct change.
4. Avoid unnecessary dependencies.
5. Preserve existing behavior unless explicitly changing it.
6. Every behavior change requires tests.
7. Never expose secrets.
8. Never weaken or bypass quality gates.
9. Prefer deterministic implementations.
10. Review every change before committing.

## AI workflow

For every non-trivial task:

1. Understand
2. Inspect
3. Plan
4. Implement
5. Test
6. Review
7. Evaluate
8. Commit

## Evidence discipline

Distinguish between:

FACT
- directly observed repository evidence

INFERENCE
- conclusion derived from evidence

ASSUMPTION
- not yet verified

DECISION
- selected implementation approach

Never present an assumption as a fact.

## Implementation rules

- Do not rewrite unrelated code.
- Do not introduce dependencies without justification.
- Do not remove tests to make a task pass.
- Do not disable linting, type checking, security checks, or evaluation gates.
- Do not hard-code credentials.
- Do not silently change public behavior.

## Testing requirements

Every behavior change should include appropriate tests.

At minimum consider:

- happy path
- invalid input
- edge cases
- failure behavior
- regression behavior

## Definition of done

A task is complete only when:

- implementation is complete
- tests are present
- tests pass
- lint passes
- type checking passes
- coverage passes
- security checks pass
- documentation is updated where appropriate
- git diff has been reviewed
