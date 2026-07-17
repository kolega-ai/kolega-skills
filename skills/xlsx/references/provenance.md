# XLSX provenance

## Official references

This skill is an original implementation based on public specifications and official library
documentation:

- [ECMA-376 Office Open XML](https://ecma-international.org/publications-and-standards/standards/ecma-376/)
- [Microsoft Open Specifications: SpreadsheetML](https://learn.microsoft.com/en-us/openspecs/office_standards/ms-xlsx/)
- [Python `zipfile` documentation](https://docs.python.org/3/library/zipfile.html)
- [Python `csv` documentation](https://docs.python.org/3/library/csv.html)
- [Python `os.replace` documentation](https://docs.python.org/3/library/os.html#os.replace)
- [openpyxl documentation](https://openpyxl.readthedocs.io/en/stable/)
- [pandas user guide](https://pandas.pydata.org/docs/user_guide/)
- [NumPy documentation](https://numpy.org/doc/stable/)

## Selected dependency versions

The Python 3.11+ environment is fully pinned in `requirements.txt`.

| Package | Version | Role | Declared license |
| --- | ---: | --- | --- |
| openpyxl | 3.1.5 | OOXML workbook semantics | MIT |
| pandas | 3.0.3 | Rectangular cleanup, summaries, CSV/TSV interchange | BSD-3-Clause |
| NumPy | 2.4.6 | pandas numerical runtime | BSD-3-Clause AND 0BSD AND MIT AND Zlib AND CC0-1.0 |
| et_xmlfile | 2.0.0 | openpyxl XML serialization dependency | MIT |
| python-dateutil | 2.9.0.post0 | pandas date/time dependency | Apache-2.0 OR BSD-3-Clause |
| six | 1.17.0 | python-dateutil compatibility dependency | MIT |

Dependency license identifiers above reflect package metadata and official project
documentation reviewed for these selected versions. NumPy's expression includes licenses
declared for bundled components in the selected distribution, rather than incorrectly
describing the complete distribution only as the NumPy project's BSD-3-Clause license. No
dependency source, model, font, image, template, or binary workbook is redistributed by this
skill.

## Generated artifacts

The smoke test creates workbook and delimited fixtures at runtime in a temporary directory.
The skill contains no sample workbook, external asset, model weight, or generated document.
