# Remote Strategy

This reference defines the preferred strategy when a repository keeps both HTTPS and SSH remotes.

## Default Policy

- keep the user's existing remote layout unless they ask to replace it
- allow HTTPS and SSH to coexist
- prefer explicit remote names over silent URL rewrites

## Recommended Naming

- keep the original remote name, often `origin`, for the user's established path
- add a dedicated SSH remote such as `github-ssh` when the user wants explicit SSH pushes

Example:

```text
origin      https://github.com/<user>/<repo>.git
github-ssh  git@github.com:<user>/<repo>.git
```

## When To Push Which Remote

- user asks for SSH: push `github-ssh`
- user asks for the default remote only: push the upstream remote
- user has mixed history across remotes: say which remote is behind and update only the requested one

## Important Clarification

Two remotes can point at the same GitHub repository but still appear out of sync locally if one remote ref has not been fetched or pushed recently.

Always distinguish:

- local branch location
- HTTPS remote-tracking branch
- SSH remote-tracking branch

Do not assume that one remote's branch pointer proves the other one already moved.
