# Contributing & Local Docs

## Running docs locally

API docs are generated from the `ajishio` source using
[MkDocs Material](https://squidfunk.github.io/mkdocs-material/). Because `gen_api_ref.py` imports
`ajishio` at build time (which in turn imports pygame-ce), the `AJISHIO_DOCS=1` environment
variable must be set so the engine skips pygame initialisation:

```bash
AJISHIO_DOCS=1 uv run mkdocs serve
```

Then open <http://127.0.0.1:8000> in your browser. To build a static site instead:

```bash
AJISHIO_DOCS=1 uv run mkdocs build --clean
```

The generated site is written to `site/`.
