# Portable Usage

This document explains how to use `github_sync_workflow_kernel` outside Codex-specific skill installation flows.

## Scope

Use this guide when:

- the target environment is not Codex
- the host does not support `$CODEX_HOME/skills`
- the host does not support skill tokens such as `$github-sync-agent`
- the package needs to be reused in a more general agent or CLI environment

## What Is Portable

The portable part of this package is:

- the workflow definition in `github-sync-agent/SKILL.md`
- the reference material under `github-sync-agent/references/`
- the generic starter bundle under `github-sync-agent/references/generic.prompt_bundle.yaml`
- the general process: discover -> inspect -> classify -> commit -> push -> verify

The non-portable part is mainly:

- Codex skill installation into `$CODEX_HOME/skills`
- host-specific skill token syntax such as `$github-sync-agent`
- any local credential helper or SSH agent behavior that must be provided by the target machine

## Recommended Entry Point

Even outside Codex, the recommended logical entry point remains:

- `github-sync-agent`

This means:

- use the full GitHub sync workflow as the main path
- do not skip repository discovery or commit-scope classification just because the host is different

## Recommended Starting Files

For a portable first run, start with:

- `github-sync-agent/references/generic.prompt_bundle.yaml`

Use these files as supporting references:

- `github-sync-agent/SKILL.md`
- `github-sync-agent/references/checklist.md`
- `github-sync-agent/references/wsl-github-setup.md`
- `github-sync-agent/references/remote-strategy.md`
- `github-sync-agent/references/commit-scope-policy.md`

## Portable Workflow

The recommended portable workflow is:

1. identify the actual target repository
2. inspect branch, remotes, and worktree state
3. verify GitHub auth path for the target machine
4. decide whether the task is:
   - push existing commits only
   - prepare a new commit and then push
5. classify the remaining diff into:
   - intended source or docs changes
   - whitespace or line-ending noise
   - generated or restored outputs
6. stage only the intended scope
7. create the commit if needed
8. push the chosen remote
9. verify final branch, remote, and leftover worktree state

## If the Host Does Not Support Skill Tokens

Some hosts do not understand forms such as:

- `$github-sync-agent`

In that case:

- remove the `$...` token
- keep the prompt body
- keep the workflow order
- keep the output contract and reference instructions

The token is host syntax, not the core method.
