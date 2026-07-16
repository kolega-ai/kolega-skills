# Contributing to Kolega Skills

Thank you for helping make Kolega more capable. Contributions may add a skill, improve an
existing skill, or strengthen repository tooling.

## Before writing

1. Check the [catalog](README.md#catalog) for overlapping skills.
2. Define at least three realistic requests that should activate the skill.
3. Define near-miss requests that should not activate it.
4. Identify which reusable resources are necessary. Do not add empty directories.
5. Confirm that every bundled dependency or asset can be redistributed.

## Skill requirements

Create skills at `skills/<skill-name>/SKILL.md`.

- Follow the [Agent Skills specification](https://agentskills.io/specification).
- Use a lowercase kebab-case name of at most 64 characters.
- Make the frontmatter `name` exactly match the directory name.
- Write a description that says both what the skill does and when an agent should use it.
- Keep `SKILL.md` focused. Move detailed material into `references/`.
- Put deterministic or repetitive operations in `scripts/`.
- Put output templates and static resources in `assets/`.
- Reference bundled files with paths relative to the skill root.
- Prefer imperative instructions and concrete examples.
- Document runtime dependencies and useful failure messages.
- Do not include generated output, caches, secrets, or machine-specific absolute paths.

The root Apache-2.0 license applies unless the skill includes different terms and declares
them in its `license` frontmatter. Include attribution and license files alongside all
third-party content. Do not copy source-available or proprietary skills without explicit
redistribution permission.

## Create a skill

Sync the root tooling environment with
[uv](https://docs.astral.sh/uv/) and use the generator:

```bash
uv sync --locked
uv run python scripts/new_skill.py my-skill \
  --description "What the skill does and the situations in which Kolega should use it."
```

Add `--resource scripts`, `--resource references`, or `--resource assets` only when needed.
For a non-Apache skill, also pass `--license "<identifier>" --license-file <path>` so its
terms remain available when the skill is packaged independently.
Skills remain self-contained and do not inherit the repository tooling environment; `uv`
manages only root validation, packaging, and test dependencies.

## Test a change

Run the same core checks as CI:

```bash
uv run python scripts/validate_skills.py
uv run python -m unittest discover -s tests -v
uv run ruff check .
uv run ruff format --check .
uv run python scripts/package_skill.py --all --output /tmp/kolega-skill-dist
```

Also exercise the skill on its activation examples and near misses. Run any tests belonging
to bundled scripts and document external services, credentials, or platforms that you could
not test.

## Pull requests

Keep each pull request focused. In the description:

- summarize the user problem and workflow;
- list representative activation and near-miss prompts;
- list checks you ran;
- identify third-party content and its provenance;
- note compatibility constraints or external dependencies.

Update the root catalog when adding, renaming, or removing a skill. A contribution is ready
when its instructions are complete, local links resolve with exact casing, scripts are
tested, and the skill packages successfully.
