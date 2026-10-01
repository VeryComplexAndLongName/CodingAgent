# Repository Instructions

Use `CLAUDE.md` as the primary repository playbook. If anything here
conflicts with `CLAUDE.md`, follow `CLAUDE.md` and update this file to point
back to the source of truth instead of duplicating the rule.

## Before changing code

1. Read `openspec/README.md` for the change-order runbook.
2. Read `openspec/changes/*/tasks.md` before implementing a capability.

## Governance (mandatory)

- Every repository change must be tracked in an OpenSpec change entry under
   `openspec/changes/<id>/`.
- Do not apply direct ad-hoc changes outside OpenSpec, including docs/tests/
   tooling updates.
- All architecture-impacting changes must be documented via ADR in
   `docs/adr/`, and the OpenSpec change must reference that ADR.

## Architecture rules

- All architecture rules described in `Python.md` for python projects

## Language policy

All code comments, descriptions, and markdown files in this repository must
be written in English only. Do not add Russian text to any description,
docstring, comment, or `.md` file.

Commit messages must be written in English only.

## Versioning

Follow semver per package:

- `patch` for bug fixes, docs, and refactors without external contract changes.
- `minor` for backward-compatible feature additions.
- `major` for breaking changes in behavior, protocol, data format, or promised UX.

If a user-visible behavior change ships, bump the affected package version in the same change.
