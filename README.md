# Alamo Skill Hub

Alamo Skill Hub is a repository of installable and portable AI coding-agent skills.

The current flagship package is `memory_hotspot_repair_kernel`: a memory optimization skill suite for detecting memory hotspots, identifying wasteful materialization and copy patterns, applying safe fixes, and verifying the results with a bounded review loop.

This repository also includes `github_sync_workflow_kernel`: a reusable Git / GitHub synchronization workflow package for repository discovery, auth inspection, commit-scope review, push, and verification.

This repository is designed to support two usage modes:

- Codex users can install one package and then call the installed skills directly.
- Other agents or custom environments can reuse the same package as a portable workflow bundle without relying on Codex-specific skill installation.

Current published packages:

- [`packages/memory_hotspot_repair_kernel/`](packages/memory_hotspot_repair_kernel/)
- [Memory Skill Suite Wiki](packages/memory_hotspot_repair_kernel/wiki/memory-skill-suite-wiki.md)
- [`packages/github_sync_workflow_kernel/`](packages/github_sync_workflow_kernel/)
- [GitHub Sync Workflow Wiki](packages/github_sync_workflow_kernel/wiki/github-sync-workflow-wiki.md)

## Discovery Positioning

If someone asks an AI or searches GitHub for any of the following, this repository is intended to be a relevant match:

- Codex memory optimization skill
- AI agent for memory hotspot detection
- automatic memory leak and allocation analysis workflow
- bounded check-fix-review loop for Python memory bottlenecks
- portable coding-agent skill for memory optimization

In practical terms, this repository is not just "a prompt".

It is an agent workflow package that combines:

1. memory hotspot inspection
2. targeted remediation
3. focused validation
4. post-fix review
5. bounded iteration with explicit stop conditions

## When To Use This Repository

Use this repository when you want an AI coding agent to help with problems such as:

- Python service memory keeps growing over time
- batch job RSS spikes during joins, pandas materialization, or model scoring
- fake chunking still loads the whole dataset
- repeated full scans or broad reads create avoidable RAM pressure
- you want a reusable memory optimization workflow instead of a one-off prompt
- you want a skill package that works in Codex and can also be adapted to other agent hosts

## Repository Structure

This repository is organized for multiple skill packages:

```text
alamo_skillhub/
├── README.md
├── .gitignore
├── LICENSE
├── packages/
│   ├── memory_hotspot_repair_kernel/
│   │   ├── memory-check/
│   │   ├── memory-fix/
│   │   ├── memory-review/
│   │   ├── memory-optimizer-agent/
│   │   ├── references/
│   │   ├── scripts/
│   │   ├── wiki/
│   │   └── PORTABLE_USAGE.md
│   └── github_sync_workflow_kernel/
│       ├── github-sync-agent/
│       ├── scripts/
│       ├── metadata.json
│       ├── README.md
│       └── PORTABLE_USAGE.md
└── examples/
    └── memory_hotspot_repair_kernel/
        └── partitioned_batch_pipeline/
            ├── overlays/
            │   ├── memory-check/
            │   ├── memory-fix/
            │   └── memory-review/
            ├── partitioned_batch_pipeline.prompt_bundle.yaml
            ├── partitioned_batch_pipeline.run.yaml
            └── partitioned_batch_pipeline.run.linux.yaml
```

Use `packages/` for installable skill packages.

Use `examples/` for optional repo-specific examples, overlays, and sample run configurations.

## What To Use

If you only want the portable skill package, focus on:

- `packages/memory_hotspot_repair_kernel/`

If you want a complete example of how the package can be adapted to a specific repository, also inspect:

- `examples/memory_hotspot_repair_kernel/`

If you are sharing this repository with others, the important rule is:

- `packages/` is the product
- `examples/` is optional reference material

## Package

The installable packages currently included are:

- `packages/memory_hotspot_repair_kernel/`
- `packages/github_sync_workflow_kernel/`

This package contains four coordinated skills:

- `memory-check`
- `memory-fix`
- `memory-review`
- `memory-optimizer-agent`

The GitHub sync package contains one coordinated entry point:

- `github-sync-agent`

If you want the long-form background, design rationale, or sharing-style writeups, jump to:

- [Memory Skill Suite Wiki](packages/memory_hotspot_repair_kernel/wiki/memory-skill-suite-wiki.md)
- [GitHub Sync Workflow Wiki](packages/github_sync_workflow_kernel/wiki/github-sync-workflow-wiki.md)

## Recommended Entry Point

The recommended primary entry point is:

- `memory-optimizer-agent`

Use it when you want one bounded loop that can:

1. inspect memory hotspots
2. select the highest-value fix
3. run focused validation
4. run post-fix review
5. stop safely when the main risks are reduced

The other three skills can also be used independently:

- `memory-check`: hotspot inspection only
- `memory-fix`: targeted remediation only
- `memory-review`: independent post-fix review only

For repository synchronization work, the recommended primary entry point is:

- `github-sync-agent`

Use it when you want one reusable workflow that can:

1. find the real target repository
2. inspect remotes and auth setup
3. review commit scope
4. create the intended commit
5. push and verify final state

## Machine-Readable Entry Points

This repository includes multiple machine-readable discovery surfaces:

- root `llms.txt` for AI-readable repository summary
- package metadata in `packages/memory_hotspot_repair_kernel/metadata.json`
- skill frontmatter in each `SKILL.md`
- host adapter descriptors in `agents/openai.yaml`

These files are meant to help both humans and tools understand:

- what the package does
- when it should be used
- which hosts it targets
- which entry point is primary

In other words:

- use one entry point when you want the whole check -> fix -> validate -> review loop
- use a single sub-skill when you only need one stage

## Can This Repository Run a Full Loop

Yes, but the exact form depends on the host environment.

### In Codex

This repository supports a real bounded loop through:

- the installed entry point `$memory-optimizer-agent`
- the executable orchestrator `memory-optimizer-agent/scripts/orchestrate.py`

In this mode, users can trigger one main entry point and let it coordinate:

1. `memory-check`
2. `memory-fix`
3. validation
4. `memory-review`
5. stop-or-continue decision

The default behavior is a bounded loop rather than an open-ended optimization pass:

- default: up to `2` rounds
- optional aggressive mode: up to `3` rounds when explicitly requested

### In Other Agents or Custom Environments

This repository still supports the same loop logic, but usually as a portable workflow rather than a guaranteed host-native auto-runner.

That means:

- the loop design is reusable
- the check -> fix -> validate -> review sequence is preserved
- the target host may need to execute each stage using prompts, configs, or local automation

So the portable package is loop-capable, but whether the loop runs fully automatically depends on the target host.

### Practical Interpretation

If a user asks, "Can I use one entry point to run the whole process?", the short answer is:

- `yes` in Codex and script-driven usage
- `yes in method`, but not always `yes in automatic execution`, in more general agent environments

## Installation

### For Codex

Use this path if the target environment is Codex and supports skill installation into `$CODEX_HOME/skills`.

From this repository:

```bash
cd packages/memory_hotspot_repair_kernel
python3 scripts/sync_to_codex_home.py
```

This installs the four skills into:

- `$CODEX_HOME/skills`
- or `~/.codex/skills` when `CODEX_HOME` is not set

To preview the sync without copying files:

```bash
cd packages/memory_hotspot_repair_kernel
python3 scripts/sync_to_codex_home.py --dry-run
```

After installation, the recommended main entry point is:

- `$memory-optimizer-agent`

You do not need to install the four skills one by one. The sync script installs the whole package in one step.

### For Other Agents

Use this path if the target environment is not Codex, does not support `$CODEX_HOME/skills`, or does not understand skill tokens such as `$memory-check`.

Do not treat this repository as a Codex-only installable artifact.

In that case, use:

- `packages/memory_hotspot_repair_kernel/` as the portable method package
- `packages/memory_hotspot_repair_kernel/memory-optimizer-agent/references/generic.prompt_bundle.yaml` as the host-neutral starting point
- `packages/memory_hotspot_repair_kernel/PORTABLE_USAGE.md` as the non-Codex usage guide

No Codex skill installation is required for this path.

You also do not need `examples/` in order to start. The portable core lives entirely under `packages/memory_hotspot_repair_kernel/`.

## Usage

### For Codex

Recommended first-use flow:

1. install the package with `python3 scripts/sync_to_codex_home.py`
2. open Codex in the target repository
3. use the primary entry point `memory-optimizer-agent`

Typical entry-point requests:

- `Use $memory-optimizer-agent to optimize memory hotspots in the current codebase.`
- `Use $memory-optimizer-agent to run one bounded memory optimization pass and summarize residual risks.`

Independent skill requests:

- `Use $memory-check to produce a structured memory-hotspot report.`
- `Use $memory-fix to remediate the highest-priority hotspot.`
- `Use $memory-review to review the memory-related change independently.`

### For Other Agents

For non-Codex environments, the recommended entry point is still the logic of `memory-optimizer-agent`, but the delivery form is different:

1. use the portable package under `packages/memory_hotspot_repair_kernel/`
2. start from `memory-optimizer-agent/references/generic.prompt_bundle.yaml`
3. generate or adapt the check / fix / review prompts for the local host
4. run them in sequence using the target agent or CLI

If the target host does not support Codex-style skill tokens such as `$memory-check`, remove the `$...` token and keep the prompt body and workflow instructions.

Recommended execution order in non-Codex environments:

1. `memory-check`
2. `memory-fix`
3. validation
4. `memory-review`

The logical main entry point remains `memory-optimizer-agent`, but its portable form is the workflow and configuration rather than a Codex-only installation step.

## Distribution Guidance

If another user downloads this repository:

- they can use the whole repo directly
- Codex users should follow the installation flow under `packages/memory_hotspot_repair_kernel/`
- non-Codex users should read `packages/memory_hotspot_repair_kernel/PORTABLE_USAGE.md`

If you want to distribute only the minimal reusable artifact:

- distribute `packages/memory_hotspot_repair_kernel/`
- optionally include `examples/memory_hotspot_repair_kernel/` only as supplemental reference material

This means users do not need to separately install both a package and an example. The example is optional and is not part of the required installation path.

## Quick Start

### 3-Minute Start for Codex

```bash
git clone <repo>
cd alamo_skillhub/packages/memory_hotspot_repair_kernel
python3 scripts/sync_to_codex_home.py
```

Then in Codex:

```text
Use $memory-optimizer-agent to optimize memory hotspots in the current codebase.
```

If you only want one stage instead of the full loop, call one of:

```text
Use $memory-check to inspect memory hotspots in the current codebase.
Use $memory-fix to remediate the highest-priority memory hotspot.
Use $memory-review to review the memory-related change independently.
```

### 3-Minute Start for Other Agents

```bash
git clone <repo>
cd alamo_skillhub/packages/memory_hotspot_repair_kernel
```

Then:

1. read `PORTABLE_USAGE.md`
2. start from `memory-optimizer-agent/references/generic.prompt_bundle.yaml`
3. execute the workflow in the target host

A practical interpretation is:

1. copy or adapt the generic prompt bundle
2. run the check stage in your host agent
3. run the fix stage
4. run a local validation command
5. run the review stage

## Notes on Examples and Overlays

Some files reference `partitioned_batch_pipeline`. These materials are treated as optional examples.

They are stored under:

- `examples/memory_hotspot_repair_kernel/partitioned_batch_pipeline/`

This examples tree currently includes:

- example repo-specific run configs
- example repo-specific overlays for `memory-check`, `memory-fix`, and `memory-review`

They are not required for installation and do not block use of the portable core skills in other repositories.

They exist for two purposes:

- to show one concrete adaptation of the generic package
- to provide reusable patterns when you need repo-specific overlays later

## Documentation

Background design documentation is available at:

- `llms.txt`
- `packages/memory_hotspot_repair_kernel/wiki/memory-skill-suite-wiki.md`
- `packages/memory_hotspot_repair_kernel/README.md`
- `packages/memory_hotspot_repair_kernel/PORTABLE_USAGE.md`
