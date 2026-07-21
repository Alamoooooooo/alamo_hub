---
name: github-sync-agent
description: Coordinate an end-to-end GitHub synchronization workflow over a target repository by discovering the real repo root, inspecting auth and remotes, classifying local changes, preparing the right commit scope, pushing the chosen remote, and verifying final state. Use when a user wants one reusable skill for GitHub setup, search, sync, commit, and push instead of ad hoc terminal steps.
---

# GitHub Sync Agent

Act like a dedicated mini-agent that coordinates repository discovery, GitHub auth inspection, commit-scope review, commit creation, push, and verification.

This skill is the workflow and host-adapter layer. Keep reusable Git/GitHub policy in the `references/` files, not in one-off chat explanations.

## Core Policy

- Treat the current directory as a router until the real repository is identified.
- Inspect before mutating: branch, remotes, worktree, and tracking must be known first.
- Separate auth setup from repository changes.
- Preserve the user's remote strategy when possible.
- Prefer explicit push targets over guessing.
- Exclude whitespace-only noise and obvious generated-output noise unless the user explicitly wants them committed.

## Default Workflow

1. Identify the actual target repository.
2. Inspect:
   - current branch
   - upstream tracking
   - remotes
   - worktree state
3. Inspect the auth path:
   - SSH vs HTTPS
   - credential or SSH readiness
   - WSL-specific GitHub SSH routing when relevant
4. Decide which path applies:
   - push existing commits only
   - stage and create a new commit first
5. Review the remaining diff and classify it:
   - intended source or docs changes
   - whitespace or line-ending noise
   - generated artifacts or restored copies
6. Stage only the intended scope.
7. Create the commit when needed.
8. Push the chosen remote.
9. Verify:
   - new commit location
   - remote tracking state
   - leftover local modifications

## Multi-Repo Rule

- In a multi-repo workspace, do not assume the workspace root is the target repo.
- Find the real repo root first.
- Report other nearby repos only as context, not as push targets.

## Remote Strategy Rule

- If the user keeps both HTTPS and SSH remotes, preserve both unless explicitly told otherwise.
- If a dedicated SSH remote such as `github-ssh` exists, use it when the user asks for SSH.
- If `origin` is HTTPS and cannot authenticate, do not pretend the push succeeded.
- Say clearly whether:
  - SSH remote is up to date
  - HTTPS remote is behind
  - auth is missing for one remote path

## Commit-Scope Rule

- Prefer one coherent commit per logical change set.
- Avoid mixing active source/docs work with restored outputs or noisy format-only diffs.
- Check whitespace-only candidates with line-ending-insensitive diff logic before including them.
- If a repo contains many categories of changes, split into multiple commits when that improves clarity.

## Stop Conditions

Stop after any of these is true:

- the requested remote is up to date and no new commit is required
- the intended commit is created, pushed, and verified
- the remaining work requires new credentials or user approval outside the current environment
- the remaining diff cannot be classified safely without broader user input

## Output Per Run

Produce:

- `Target Repo`: the actual repository path and branch
- `Remote Summary`: remotes, chosen push target, and tracking state
- `Auth Summary`: SSH or HTTPS readiness and any missing setup
- `Commit Scope`: what was included, excluded, and why
- `Push Result`: the push command path and final commit location
- `Residual State`: what remains uncommitted or unsynced

## Reference Use

- Read `references/checklist.md` for the end-to-end workflow checklist.
- Read `references/wsl-github-setup.md` for WSL SSH setup and `ssh.github.com:443` routing.
- Read `references/remote-strategy.md` for HTTPS + SSH coexistence and explicit remote naming.
- Read `references/commit-scope-policy.md` for diff classification and split-commit rules.
- Read `references/report-template.md` when the user wants a formal sync summary.
- Read `references/generic.prompt_bundle.yaml` when adapting this workflow to a non-Codex host.

## Execution Notes

- A successful sync is not just `git push`; it also proves the right repo, right commit scope, and right remote.
- If the repo already contains committed local history that a secondary remote lacks, pushing that history can be enough even when the worktree is dirty.
- If HTTPS auth is missing but SSH works, report the divergence honestly instead of masking it.
- When a commit is created, verify the worktree again so the user can see what still remains locally.
