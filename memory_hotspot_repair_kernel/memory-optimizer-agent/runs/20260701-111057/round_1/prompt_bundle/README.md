# External Run Instructions

This prompt bundle is host-neutral. It does not require Codex runtime integration.

## Suggested sequence

1. Run `check.prompt.md` in your preferred coding agent or CLI.
2. Save the structured output from that run as `check.result.json` beside the prompt bundle if your host supports JSON output.
3. Run `fix.prompt.md`, pasting or attaching the check output when the host cannot automatically chain context.
4. Apply and validate code changes in the workspace.
5. Run `review.prompt.md`, pasting or attaching the check result, fix summary, and validation result if needed.

## Files

- `check.prompt.md`: hotspot audit prompt
- `fix.prompt.md`: behavior-preserving remediation prompt
- `review.prompt.md`: post-fix review prompt
- `bundle.json`: machine-readable prompt bundle manifest

## Validation

Validation commands were executed locally by the orchestrator when possible. See the sibling `validation/` directory for command logs and pass/fail status.

## Notes

- Repository-specific overlays are already injected into the generated prompts when target paths matched an overlay rule.
- If your host does not support skill names like `$memory-check`, keep the prompt text but remove the `$...` token and retain the instructions.
- If your host cannot emit structured JSON, save its prose output separately and carry the relevant sections into the next prompt.
