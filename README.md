# Kolega Skills

A public collection of Agent Skills maintained by [Kolega](https://github.com/kolega-ai).
Skills are self-contained folders of instructions and optional resources that give an AI
agent reliable workflows for specialized tasks.

This repository follows the open [Agent Skills specification](https://agentskills.io/specification)
and adds repository-level validation, deterministic packaging, tests, and CI.

## Catalog

| Skill | Use it for |
| --- | --- |
| [`bug-fix-loop`](skills/bug-fix-loop/SKILL.md) | Structured bug fixing with mandatory two-pass investigation — Reproduce → Investigate → Act → Check → Adapt → Report |
| [`docx`](skills/docx/SKILL.md) | Creating, inspecting, editing, and converting Microsoft Word `.docx` documents |
| [`pdf`](skills/pdf/SKILL.md) | PDF-native extraction, creation, page operations, forms, security, conversion, and explicit OCR routing |
| [`pptx`](skills/pptx/SKILL.md) | Building, inspecting, editing, and converting Microsoft PowerPoint `.pptx` presentations |
| [`review`](skills/review/SKILL.md) | Reviewing pull requests, local changes, or branch diffs, with help and optional GitHub comments |
| [`skill-authoring`](skills/skill-authoring/SKILL.md) | Creating, revising, and reviewing standards-compliant Agent Skills |
| [`xlsx`](skills/xlsx/SKILL.md) | Creating, inspecting, editing, cleaning, summarizing, and converting Microsoft Excel `.xlsx` workbooks |

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

Install a complete directory from `skills/` through any Agent Skills-compatible client's
skill-management flow, or copy it into a project or user skill directory configured by that
client. Keep the directory intact: resources are referenced relative to the skill root.

Once installed, describe the task normally. A compatible client uses each skill's `name` and
`description` to decide when to load its instructions.

### Document skill runtimes

Each document skill is independently installable and carries its own direct Python runtime
requirements with compatible release ranges. The skill selects any available Python 3.11+
interpreter rather than assuming that `python` or `python3` has a particular meaning. Before
installing anything, it tells the user what is missing, where it will be installed, and which
installer it intends to use.
Python packages are normally installed through the selected interpreter's `-m pip`.
Python itself and external applications use the platform's normal package manager, with
Homebrew preferred on macOS when available. A local environment is a fallback when direct
installation is blocked; it is not required.
The document skills do not require `uv`; `uv` is used only by the repository development
and validation commands below.

- DOCX-to-PDF and PPTX-to-PDF conversion optionally use a separately installed LibreOffice
  `soffice` executable. The source-format skill owns these conversions; use `pdf` for
  operations on an existing PDF.
- PDF OCR is optional and never runs automatically. Use `ocr-plan` first, then explicitly
  choose an independently installed engine and locally provisioned model or language data:
  Surya for modern layout-aware extraction when its model terms and runtime are suitable,
  PaddleOCR as the no-GPU fallback, or Tesseract as an explicit last-resort fallback when the
  preferred engines are unavailable. Tesseract is best suited to clean printed text on CPU
  when flat output is acceptable.
- No OCR engine, model weights, language data, or LibreOffice binary is bundled. Optional
  runtimes are installed only after the skill tells the user about the intended system
  change. OCR models and language data remain explicit, reviewed local artifacts and are
  never downloaded implicitly.
- Surya's code is Apache-2.0, but its current model weights use modified AI Pubs Open Rail-M
  terms with commercial-use eligibility limits. Review and approve the selected model's
  terms before provisioning it. Verify model and language-data licenses for every OCR engine.

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
