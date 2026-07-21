---
name: docx
description: Create, inspect, edit, extract text from, and convert Microsoft Word DOCX documents while preserving formatting and validating OOXML safely. Use for .docx authoring, reading, structured edits, templates or letterheads, tables, images, headers, footers, fields, DOCX-to-text, and DOCX-to-PDF requests. Do not use for PDF-native, spreadsheet, or presentation work.
license: Apache-2.0
compatibility: Requires Python 3.11+; LibreOffice is optional for DOCX-to-PDF conversion.
metadata:
  author: Kolega
  version: "1.0"
---

# DOCX

Use the bundled deterministic CLI for WordprocessingML work. Treat every source document as
untrusted and immutable unless the user explicitly authorizes overwrite.

## Workspace discipline

Work directly in visible workspace paths. Never create or use `.build` or another hidden
build/work directory. Write requested deliverables directly to their declared destinations;
if intermediate files are necessary, keep them in visible, narrowly scoped paths rather than
staging the task in a hidden subtree.

## Route the task

- Use this skill for creating, reading, inspecting, editing, or converting `.docx` files.
- Keep DOCX-to-PDF work here because conversion begins from the DOCX source.
- Route PDF-native editing or extraction to `pdf`, spreadsheets to `xlsx`, and presentations
  to `pptx`.

## Workflow

1. Resolve the skill root and choose any available Python 3.11+ interpreter; do not assume a
   launcher name. Check the required imports before installing anything. If something is
   missing, first tell the user what you intend to install, where, and with which installer.
Use the selected interpreter's `-m pip` for the declared requirements. Use the platform's
   package manager for Python or optional LibreOffice, preferring Homebrew on macOS when
   available. A local environment is a fallback, not a prerequisite. See
   [environment setup](references/operations.md#environment).
2. Read [the operation contract](references/operations.md) before constructing a job. Read
   [the examples](references/examples.md) for copy-pasteable invocations.
3. Inspect an existing document before editing. Review ordered blocks, styles, runs, sections,
   headers, footers, fields, drawings, comments, revisions, unsupported parts, and warnings.
4. Prefer named styles and template inheritance over direct formatting. Use the public CLI
   instead of ad hoc package mutation.
   For tables, turn autofit off and set fixed widths. Leave at least 0.9 inches for short-label
   columns; use landscape orientation or fewer columns for prose tables. Never enable
   character-level word breaking. Disable row splitting only for compact rows; a row taller
   than the page must remain splittable.
5. Write to a distinct destination. Use `--overwrite` only after explicit authorization.
6. Reinspect the output and verify structure, expected text, styles, tables, images, stories,
   fields, and the font inventory. For DOCX+PDF deliverables, rendering and page-by-page layout
   review are mandatory. Apply this release gate: use only Arial for headings and sans body,
   Times New Roman for serif body, and Courier New for code or logs, including chart labels.
   Do not use Avenir, Calibri, Cambria, Georgia, Trebuchet, Palatino, or any other unembedded
   custom/system font; replace every `nonportable_unembedded_fonts` finding before release.
   PDF font embedding is not DOCX font embedding. A clean LibreOffice PDF alone does not prove
   that Word will preserve wrapping or pagination.
   Do not force every section onto a new page. Both deliverables must show a visibly populated
   contents list. A static list may use final-PDF page references, but label it accordingly and
   make no DOCX-pagination or DOCX-fidelity claim.
7. Report warnings and preservation uncertainty. Never promise perfect round-trip fidelity.

## Safety rules

- Do not bypass OOXML preflight, ZIP expansion limits, signature checks, or post-write reopen
  validation.
- Never use `sudo pip`, any interpreter under `sudo` to run pip, or pip's
  `--break-system-packages` option. Do not add these packages to the host project's dependency
  metadata.
- Reject macro-enabled, encrypted, malformed, or oversized packages.
- Reject DOCX external relationships by default. Use the documented explicit opt-in only after
  review; it permits processing and does not provide network isolation for LibreOffice or
  another consumer.
- Keep edits explicit and bounded. Supply expected replacement counts and use the first-run
  policy only when a cross-run replacement is intentional.
- Do not flatten text across hyperlinks, fields, drawings, comments, or revisions.
- Use public `python-docx` APIs for ordinary content. The CLI confines narrow OOXML helpers to
  field markup, block placement, and image relationship replacement.
- Remember that page-number and TOC fields are markup only. Pagination and TOC refresh require
  a layout application.
- Never derive static TOC page numbers solely from the generated PDF when the editable DOCX is
  also a paginated deliverable. If no independent DOCX renderer is available, prefer live fields
  and avoid claiming identical pagination; do not convert PDF page checks into DOCX fidelity
  claims.
- Keep PDF conversion within the generated-PDF byte/page/text-extraction and decompressed-stream
  bounds. LibreOffice runs with an isolated profile and process group so timeout cleanup
  reaches ordinary descendants; those lifecycle controls are not a network sandbox.

## Resources

- Read [operations](references/operations.md) for the stable CLI, job schemas, exit statuses,
  and atomic-write behavior.
- Read [examples](references/examples.md) when preparing or debugging a job.
- Read [limitations](references/limitations.md) before promising fidelity or advanced Word
  features.
- Run [`scripts/docx_tool.py`](scripts/docx_tool.py) for production operations.
- Run [`scripts/smoke_test.py`](scripts/smoke_test.py) after installation to verify the active
  environment. Add `--require-libreoffice` when PDF conversion must be tested.

## Final verification

Confirm that the source remains unchanged unless overwrite was authorized, the destination
reopens, requested structures are present, every `unembedded_fonts` warning was resolved or
explicitly reviewed, and no temporary files or generated fixtures remain in the skill directory.
For matching DOCX/PDF deliverables, treat `nonportable_unembedded_fonts` as a release blocker;
confirm the typography, fixed table widths, natural section flow, and populated contents list
in both files before trusting page counts, table wrapping, object flow, or TOC references.
`pdffonts` can inspect only the PDF and must never be cited as evidence that the DOCX embeds or
preserves those fonts.
