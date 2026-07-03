# Portable Usage

This document explains how to use `memory_hotspot_repair_kernel` outside Codex-specific skill installation flows.

## Scope

Use this guide when:

- the target environment is not Codex
- the host does not support `$CODEX_HOME/skills`
- the host does not support skill tokens such as `$memory-check`
- the package needs to be reused in a more general agent or CLI environment

## What Is Portable

The portable part of this package is:

- the skill workflow definitions in `SKILL.md`
- the reference material in `references/`
- the generic starter configs under `memory-optimizer-agent/references/`
- the general process: check -> fix -> validate -> review

The non-portable part is mainly:

- Codex skill installation into `$CODEX_HOME/skills`
- host-specific skill token syntax such as `$memory-check`
- Codex-specific runtime wiring

## Recommended Entry Point

Even outside Codex, the recommended logical entry point remains:

- `memory-optimizer-agent`

This means:

- use the bounded loop as the main workflow
- use `memory-check`, `memory-fix`, and `memory-review` as substeps or independent tools only when needed

## Recommended Starting Files

For a portable first run, start with:

- `memory-optimizer-agent/references/generic.prompt_bundle.yaml`

Use these files as supporting references:

- `memory-check/SKILL.md`
- `memory-fix/SKILL.md`
- `memory-review/SKILL.md`
- `memory-optimizer-agent/SKILL.md`
- `memory-optimizer-agent/references/usage-notes.md`

## Portable Workflow

The recommended portable workflow is:

1. select target paths in the repository
2. use the generic prompt-bundle configuration as a template
3. replace placeholder validation commands with repository-specific commands
4. generate or manually prepare the three prompts:
   - check
   - fix
   - review
5. execute them in order in the target host
6. carry validation results into the review step

## If the Host Does Not Support Skill Tokens

Some hosts do not understand forms such as:

- `$memory-check`
- `$memory-fix`
- `$memory-review`
- `$memory-optimizer-agent`

In that case:

- remove the `$...` token
- keep the prompt body
- keep the workflow order
- keep the output contract and reference instructions

The token is host syntax, not the core method.

## Role of Examples

The repository `examples/` tree is optional.

It provides:

- repo-specific overlays
- sample run configurations
- concrete examples of how the portable core can be specialized

It is not required for first use of the portable package.

## Recommended Delivery Model

When sharing this package with non-Codex users, recommend this interpretation:

- `packages/` contains reusable installable or reusable method packages
- `examples/` contains optional specialization examples

Users should not need to download examples separately. They can clone the whole repository and ignore `examples/` unless they need a concrete reference.
