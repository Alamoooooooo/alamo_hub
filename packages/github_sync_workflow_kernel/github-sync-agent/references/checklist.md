# GitHub Sync Checklist

Use this checklist when driving a real GitHub synchronization task.

## Phase 1: Target Repo Discovery

- confirm whether the current directory is:
  - the actual repository
  - a workspace router
  - a container directory around a nested repo
- if needed, discover the true repo root before running any mutating Git command

## Phase 2: Git State Inspection

- current branch
- upstream branch
- remotes and URLs
- uncommitted tracked changes
- untracked files
- whether the task is:
  - push existing commits only
  - prepare a new commit

## Phase 3: Auth Path Inspection

- SSH or HTTPS
- if SSH:
  - key exists
  - host routing is correct
  - remote naming is clear
- if HTTPS:
  - credential helper or PAT availability
  - whether the remote can actually authenticate in the current environment

## Phase 4: Commit-Scope Review

- intended source or docs changes
- whitespace or line-ending-only noise
- generated outputs
- restored copies or mail-check artifacts
- whether the user wants one commit or split commits

## Phase 5: Commit and Push

- stage only intended files
- create commit message that matches the actual scope
- push the selected remote explicitly
- do not assume other remotes updated automatically

## Phase 6: Verification

- latest local commit id
- chosen remote branch position
- whether another remote is still behind
- remaining uncommitted changes
- remaining untracked files
