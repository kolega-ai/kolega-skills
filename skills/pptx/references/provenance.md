# Provenance and dependency review

This skill contains original instructions and source code. It redistributes no templates, sample
presentations, fonts, media, model weights, or third-party source files.

## Official specifications and documentation

- ECMA International, **ECMA-376 Office Open XML File Formats**:
  <https://ecma-international.org/publications-and-standards/standards/ecma-376/>
- Microsoft Learn, **Structure of a PresentationML document**:
  <https://learn.microsoft.com/en-us/office/open-xml/presentation/structure-of-a-presentationml-document>
- `python-pptx` documentation:
  <https://python-pptx.readthedocs.io/en/latest/>
- `lxml` parsing documentation:
  <https://lxml.de/parsing.html>
- `pypdf` documentation:
  <https://pypdf.readthedocs.io/en/stable/>
- LibreOffice command-line parameter documentation:
  <https://help.libreoffice.org/latest/en-US/text/shared/guide/start_parameters.html>
- Python standard-library documentation for `zipfile`, `argparse`, `tempfile`, `subprocess`, and
  atomic `os.replace`: <https://docs.python.org/3/library/>

## Pinned dependency licenses

Versions are fixed in `requirements.txt`; package license metadata and upstream project
documentation were reviewed for this dependency set.

| Package | Version | Role | Declared license |
|---|---:|---|---|
| `python-pptx` | 1.0.2 | Presentation API | MIT |
| `lxml` | 6.1.1 | Hardened direct XML inspection | BSD-3-Clause |
| `pypdf` | 6.14.2 | Converted-PDF verification | BSD-3-Clause |
| `Pillow` | 12.3.0 | Image validation; `python-pptx` transitive | MIT-CMU |
| `XlsxWriter` | 3.2.9 | Native chart workbook data; transitive | BSD-2-Clause |
| `typing-extensions` | 4.16.0 | Runtime typing compatibility; transitive | PSF-2.0 |

LibreOffice is not bundled. Its installation, version, fonts, filters, and license obligations
remain the operator's responsibility.
