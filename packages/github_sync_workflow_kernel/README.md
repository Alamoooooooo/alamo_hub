# GitHub Sync Workflow Kernel

`github_sync_workflow_kernel` is an installable and portable AI coding-agent skill package for handling the end-to-end GitHub synchronization workflow.

It is designed for tasks such as:

- configuring Git identity and GitHub authentication in a fresh WSL or Linux environment
- discovering which directory is the real target repository in a multi-repo workspace
- checking branch, remotes, and uncommitted changes before a push
- deciding whether to push existing commits or prepare a new commit
- separating real content changes from line-ending noise or generated-output noise
- committing the intended scope and pushing it to the selected remote
- verifying final branch and remote state after synchronization

## Primary Entry Point

The main entry point is `github-sync-agent`.

It orchestrates:

1. repository discovery
2. Git / GitHub auth and remote inspection
3. commit-scope review
4. commit creation when needed
5. push and verification

## Best Fit

Use this package when you want:

- a Codex skill for repository sync and GitHub push workflows
- a reusable checklist for WSL + GitHub SSH setup
- a consistent multi-repo workflow that does not accidentally treat a workspace root as one repo
- a repeatable way to stage, commit, push, and verify without mixing in noise

## Start Here

- For Codex: read `../README.md`, then run `python3 scripts/sync_to_codex_home.py`
- For other hosts: read `PORTABLE_USAGE.md`
- For the orchestration contract: read `github-sync-agent/SKILL.md`

## Included Skill

- `github-sync-agent`: one entry point for GitHub sync preparation, commit, push, and verification

## Metadata

This package also includes machine-readable metadata in `metadata.json`.
