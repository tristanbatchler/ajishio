# Contributing & Local Docs

## API reference generation

The API reference page at [docs/api.md](docs/api.md) is generated automatically from the
public `ajishio` facade exports (`ajishio.__all__`) by
[scripts/gen_api_ref.py](../scripts/gen_api_ref.py).

Do not edit [docs/api.md](docs/api.md) by hand.

Regenerate locally:

```bash
uv run python scripts/gen_api_ref.py
```

Verify it is up to date (used by CI):

```bash
uv run python scripts/gen_api_ref.py --check
```

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

### Why CI does not open a pygame window

The API generator imports `ajishio` for introspection, but it forces a headless SDL backend
(`SDL_VIDEODRIVER=dummy`) during that import. This allows pygame initialization to succeed in CI
without creating a real window.

The docs workflow also runs:

```bash
uv run python scripts/gen_api_ref.py --check
```

before MkDocs build, so documentation deploy fails if [docs/api.md](docs/api.md) is stale.
