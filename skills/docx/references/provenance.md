# Provenance and dependency review

## Contents

- [Implementation basis](#implementation-basis)
- [Official documentation](#official-documentation)
- [Pinned dependency review](#pinned-dependency-review)
- [Redistributed materials](#redistributed-materials)

## Implementation basis

The skill's instructions, schemas, scripts, and examples are original expression written for
this package. The implementation follows the public file-format and library interfaces listed
below. It uses public `python-docx` APIs for ordinary document content and confines direct
OOXML work to field markup, ordered block placement, feature detection, protected-boundary
analysis, repeating table-header markup, and inline-image relationship replacement.

## Official documentation

- [Agent Skills specification](https://agentskills.io/specification) for skill metadata and
  package organization.
- [ECMA-376 Office Open XML](https://ecma-international.org/publications-and-standards/standards/ecma-376/)
  for WordprocessingML and Open Packaging Convention structures.
- [Microsoft Open XML SDK documentation](https://learn.microsoft.com/en-us/office/open-xml/word/)
  for element-level WordprocessingML concepts.
- [python-docx documentation](https://python-docx.readthedocs.io/en/latest/) for document,
  paragraph, run, table, section, header/footer, image, style, and core-property APIs.
- [lxml documentation](https://lxml.de/) for bounded XML parsing controls.
- [pypdf documentation](https://pypdf.readthedocs.io/en/stable/) for bounded PDF reopen,
  page-count, decompressed-stream, and text verification.
- [LibreOffice command-line parameter documentation](https://help.libreoffice.org/latest/en-US/text/shared/guide/start_parameters.html)
  for headless conversion and isolated user profiles.
- [Python `zipfile` documentation](https://docs.python.org/3/library/zipfile.html) for package
  member inspection.
- [Python `subprocess` documentation](https://docs.python.org/3/library/subprocess.html) for
  new-session process launch, timeout handling, diagnostic capture, and process cleanup.

## Pinned dependency review

`requirements.in` records the three direct dependencies. `requirements.txt` pins direct and
transitive runtime packages for an independently installed Python 3.11+ environment.

| Package | Version | Role | Declared license reviewed |
|---|---:|---|---|
| `python-docx` | `1.2.0` | DOCX object model and save/reopen | MIT |
| `lxml` | `6.1.1` | Direct secure OOXML parsing and narrow XML helpers | BSD-3-Clause |
| `pypdf` | `6.14.2` | Optional PDF export validation | BSD-3-Clause |
| `typing_extensions` | `4.16.0` | `python-docx` transitive runtime support | PSF-2.0 |

Version and license metadata were reviewed from each project's official distribution metadata
and documentation. The dependencies are imported at runtime; their source, wheels, license
files, and assets are not copied into this skill.

LibreOffice is not a Python dependency and is not redistributed. It is an optional external
capability used only when the user requests DOCX-to-PDF conversion.
Its unique user profile, home/temp directories, and process group isolate configuration and
support bounded lifecycle cleanup. They do not enforce network isolation; explicitly allowed
DOCX external relationships may still be accessed by LibreOffice.

## Redistributed materials

This package redistributes no third-party source, templates, fonts, images, model weights,
fixtures, or generated documents. The standalone `LICENSE` covers this skill's own files.
Smoke-test images and documents are generated programmatically inside a temporary directory
and removed when the test exits.
