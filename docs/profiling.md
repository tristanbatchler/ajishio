# Profiling

Ajishio ships a `@aj.profile` decorator. Apply it to your `main()` function and pass `--profile`
on the command line to collect a `cProfile` run and save a `.prof` file to the current working
directory (named after the project folder, e.g. `platformer.prof`):

```python
@aj.profile
def main() -> None:
    aj.game_start()

if __name__ == "__main__":
    main()
```

```bash
uv run -m demo_projects.platformer --profile
```

This prints a summary of the top 30 hotspots sorted by cumulative time. Without `--profile` the
decorator is a no-op and adds zero overhead.

## Visualising Results

[snakeviz](https://jiffyclub.github.io/snakeviz/) is included in the dev dependency group. Open a
saved `.prof` file with:

```bash
uv run snakeviz platformer.prof
```

This starts a local web server and opens an interactive flame-graph in your browser. Press `Ctrl-C`
to stop it.
