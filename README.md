# Kolega Skills

A public collection of Agent Skills maintained by [Kolega](https://github.com/kolega-ai).
Skills are self-contained folders of instructions and optional resources that give an AI
agent reliable workflows for specialized tasks.

This repository follows the open [Agent Skills specification](https://agentskills.io/specification).
It takes inspiration from [Anthropic's skills collection](https://github.com/anthropics/skills)
while adding repository-level validation, deterministic packaging, tests, and CI.

## Catalog

| Skill | Use it for |
| --- | --- |
| [`skill-authoring`](skills/skill-authoring/SKILL.md) | Creating, revising, and reviewing standards-compliant Agent Skills |

Every directory under [`skills/`](skills/) is an independently installable skill. A skill
contains a required `SKILL.md` and may include:

```text
skill-name/
├── SKILL.md       # Required metadata and instructions
├── scripts/       # Optional deterministic utilities
├── references/    # Optional documentation loaded as needed
└── assets/        # Optional templates and static resources
```

## Use a skill

Install a complete directory from `skills/` through your Kolega client's skill-management
flow, or copy it into one of the project or user skill directories configured by your
client. Keep the directory intact: resources are referenced relative to the skill root.

Once installed, describe the task normally. Kolega uses each skill's `name` and
`description` to decide when to load its instructions.

## Create a skill

Requirements:

- [uv](https://docs.astral.sh/uv/)

Sync the repository tooling environment:

```bash
uv sync --locked
```

Create a skill from the repository template:

```bash
uv run python scripts/new_skill.py my-skill \
  --description "Describe what the skill does and when Kolega should use it." \
  --resource references \
  --resource scripts
```

Only request resource directories the skill actually needs. Then replace the generated
instructions with a complete workflow and add focused resources.

## Validate and package

Validate every skill and run the tooling tests:

```bash
uv run python scripts/validate_skills.py
uv run python -m unittest discover -s tests -v
uv run ruff check .
uv run ruff format --check .
```

Build deterministic `.skill` archives with SHA-256 sidecars:

```bash
# Package every skill into dist/
uv run python scripts/package_skill.py --all

# Package one skill elsewhere
uv run python scripts/package_skill.py skills/skill-authoring --output /tmp/kolega-skills
```

A `.skill` file is a ZIP archive whose top-level directory is the skill name. Packaging
first runs the same validation used in CI.

## Contribute

Read [`CONTRIBUTING.md`](CONTRIBUTING.md) before submitting a skill. Contributions must be
original or redistributable, self-contained, narrowly scoped, and free of secrets. CI
validates metadata, local links, file safety, tests, and package reproducibility.

## License

Unless a skill states otherwise, this repository is licensed under the
[Apache License 2.0](LICENSE). Third-party content must include its own license and
attribution inside the skill.
