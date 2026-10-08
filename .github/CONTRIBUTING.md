# Contributing

This is a monorepo: each directory under [`packages/`](../packages) with a `pyproject.toml` and a `tests/` directory is an independent, publishable Python package, managed with [`uv`](https://docs.astral.sh/uv/).

## Adding a new package

```bash
mkdir packages/my_package && cd packages/my_package
uv init --lib --name my-package
```

A package needs, at minimum:

- `pyproject.toml`: standard `uv`/setuptools project config.
- `.python-version`: the Python version used for this package.
- `my_package/`: the importable package.
- `tests/`: pytest suite (`testpaths = ["tests"]` in `pyproject.toml`).
- `README.md`: what it's for and how to use it.
- `LICENSE`: package-local copy of the repo-root license.

[`.github/workflows/test_python.yml`](workflows/test_python.yml) auto-discovers any directory under `packages/` matching that shape, so no workflow edits are required. [`.github/workflows/lint.yml`](workflows/lint.yml) covers the whole repo through the root `pyproject.toml` ruff config.

### Coverage floor

CI fails a package's tests if coverage drops below **95%**. Add `pytest-cov` as a dev dependency:

```toml
[project.optional-dependencies]
dev = ["pytest>=9.1.1", "pytest-cov>=7.0.0"]

[tool.coverage.run]
source = ["my_package"]
```

## Cross-package dependencies

Reference a sibling package by version range in `dependencies`, and add a `[tool.uv.sources]` path override so local dev resolves it from the checkout:

```toml
dependencies = ["my-other-package>=0.1.0"]

[tool.uv.sources]
my-other-package = { path = "../my_other_package" }
```

## Local development

```bash
cd packages/my_package
uv sync --extra dev
uv run pytest -v
uv run ruff format .
uv run ruff check .
```
