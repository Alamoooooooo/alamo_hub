# WSL GitHub Setup

This reference captures a practical WSL-first GitHub setup that works well when port `22` is unreliable.

## Git Identity

```bash
git config --global user.name "<your-github-name>"
git config --global user.email "<your-github-email>"
git config --global init.defaultBranch main
git config --global core.autocrlf input
```

## SSH Key

Generate an `ed25519` key if one does not already exist:

```bash
ssh-keygen -t ed25519 -C "<your-github-email>"
```

Add the public key to:

- GitHub
- Settings
- SSH and GPG keys

## Recommended SSH Config For Restricted Port 22 Environments

```sshconfig
Host github.com
  HostName ssh.github.com
  User git
  Port 443
  IdentityFile ~/.ssh/id_ed25519
  IdentitiesOnly yes
```

## Verification

```bash
ssh -T git@github.com
```

Expected proof string:

```text
Hi <your-name>! You've successfully authenticated, but GitHub does not provide shell access.
```

## Multi-Repo Reminder

In WSL workspaces that contain multiple repositories, do not run `git push` from the workspace root unless that root is intentionally the target repository.

Check the actual repo first:

```bash
git status
git remote -v
```
