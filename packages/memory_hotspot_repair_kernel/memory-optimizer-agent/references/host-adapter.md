# Host Adapter Notes

This file defines what belongs in the Codex-hosted adapter layer versus the portable skill core.

## Portable Core

Keep these in the reusable skills and references:

- memory-hotspot workflow
- severity rules
- pattern catalog
- report fields
- remediation ordering

## Codex Adapter Layer

Keep these in the orchestrator or UI metadata:

- prompt phrasing that names specific skills
- Codex CLI flags and schema wiring
- sandbox and approval settings
- run directories, dashboard, resume behavior
- UI-facing default prompts in `agents/openai.yaml`

## Generic Adapter Layer

If a host cannot execute Codex reliably, keep the portable core and switch the orchestrator to a host-neutral adapter such as:

- prompt bundle generation
- validation-only mode
- external runner integration

## Adapter Rules

- Do not bury core risk logic inside host-specific prompt strings.
- Keep prompts thin and delegate policy to the underlying skill files.
- When a host-specific trigger syntax is needed, isolate it here or in the script rather than spreading it across the reusable references.
- If a runtime knob is configurable, make sure the actual CLI call passes it through.
