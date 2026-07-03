# Alamo Skill Hub

This repository is a multi-skill hub for directly installable Codex skill packages.

Current published package:

- `packages/memory_hotspot_repair_kernel/`

## Repository Structure

This repository is organized for multiple skill packages:

```text
alamo_skillhub/
├── README.md
├── .gitignore
├── LICENSE
├── packages/
│   └── memory_hotspot_repair_kernel/
└── examples/
    └── memory_hotspot_repair_kernel/
        └── segment_causal_pipeline_v2/
```

Use `packages/` for installable skill packages.

Use `examples/` for optional repo-specific examples, overlays, and sample run configurations.

## Package

The installable package currently included is:

- `packages/memory_hotspot_repair_kernel/`

This package contains four coordinated skills:

- `memory-check`
- `memory-fix`
- `memory-review`
- `memory-optimizer-agent`

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

## Installation

### For Codex

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

### For Other Agents

If the target environment is not Codex, do not treat this repository as a Codex-only installable artifact.

In that case, use:

- `packages/memory_hotspot_repair_kernel/` as the portable method package
- `packages/memory_hotspot_repair_kernel/memory-optimizer-agent/references/generic.prompt_bundle.yaml` as the host-neutral starting point
- `packages/memory_hotspot_repair_kernel/PORTABLE_USAGE.md` as the non-Codex usage guide

No Codex skill installation is required for this path.

## Usage

### For Codex

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

## Notes on Examples and Overlays

Some files reference `segment_causal_pipeline_v2`. These materials are treated as optional examples.

They are stored under:

- `examples/memory_hotspot_repair_kernel/segment_causal_pipeline_v2/`

This examples tree currently includes:

- example repo-specific run configs
- example repo-specific overlays for `memory-check`, `memory-fix`, and `memory-review`

They are not required for installation and do not block use of the portable core skills in other repositories.

## Documentation

Background design documentation is available at:

- `packages/memory_hotspot_repair_kernel/wiki/memory-skill-suite-wiki.md`
- `packages/memory_hotspot_repair_kernel/PORTABLE_USAGE.md`
