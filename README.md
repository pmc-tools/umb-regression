UMB regression models
=====================

Small stored `.umb` files that every tool must be able to **read**. They are used by the tests in
[umb-observatory](https://github.com/pmc-tools/umb-observatory) (`tests/test_regression.py`), which locate
a checkout of this repository through `UMB_REGRESSION_DIR`.

- `models/*.umb`: the files. Keep them small.
- `manifest.json`: per file, `source` (tool and version that wrote it) and optional
  `"known_issues": {"StormCLI": "link to issue"}` for failures we tolerate for now (the tool is still run; a failure is reported as xfail).
- `generate.py`: regenerates the umbi-made files (`source: "umbi"`). Needs `pip install umbi "bitstring<5"`.

Add a file when a tool misreads one: drop it in `models/` and add a manifest entry.
