<p align="center">
	<img src=".github/assets/logo.png" width="96" alt="Ajishio logo" />
</p>

<h1 align="center">Ajishio</h1>

<p align="center">
	A relaxed, GameMaker-inspired 2D engine built on <a href="https://github.com/pygame-community/pygame-ce">pygame-ce</a>.<br/>
	Designed for rapid prototyping, integrated Python workflows, and portable game development.
</p>

<p align="center">
	<a href="#why-ajishio">Why Ajishio</a> •
	<a href="#quick-start">Quick Start</a> •
	<a href="#demo-showcase">Demo Showcase</a> •
	<a href="#documentation">Documentation</a> •
	<a href="#web-export">Web Export</a> •
	<a href="#roadmap">Roadmap</a>
</p>

<p align="center">
	<a href="https://github.com/tristanbatchler/ajishio/actions/workflows/build_site.yml">
		<img src="https://github.com/tristanbatchler/ajishio/actions/workflows/build_site.yml/badge.svg" alt="Docs Build" />
	</a>
	<img src="https://img.shields.io/badge/python-3.14%2B-3776AB.svg" alt="Python 3.14+" />
	<img src="https://img.shields.io/badge/engine-pygame--ce-4B8BBE.svg" alt="pygame-ce" />
	<a href="https://tristanbatchler.github.io/ajishio/docs/">
		<img src="https://img.shields.io/badge/docs-online-1f883d.svg" alt="Online docs" />
	</a>
	<a href="https://tristanbatchler.github.io/ajishio/docs/demo-projects/">
		<img src="https://img.shields.io/badge/web%20demos-play%20now-f59e0b.svg" alt="Web demos" />
	</a>
</p>

---

## Why Ajishio

Ajishio aims to recreate the "open a file and start making a game" feeling from classic GameMaker,
but with modern Python ergonomics.

- Familiar object lifecycle with `step()` and `draw()` hooks
- Fast iteration loop for prototypes and game jam ideas
- Room loading with LDtk and sprite workflows via Aseprite exports
- Built-in paths for desktop and browser deployment
- Practical examples in `demo_projects/` that are meant to be copied and hacked

The name "Ajishio" is a reference to
[Noboru Yamaguchi](https://cromartiehigh.fandom.com/wiki/Noboru_Yamaguchi), the greatest comedian 
in all of Japan. There's no other reason.

## Quick Start

### 1) Clone and install

Ajishio uses [uv](https://github.com/astral-sh/uv) for workspace and environment management.

```bash
git clone https://github.com/tristanbatchler/ajishio
cd ajishio
uv sync
```

### 2) Run the hello world demo

```bash
uv run -m demo_projects.hello_world.main
```

<details>
<summary><strong>More demo launch commands</strong></summary>

```bash
uv run -m demo_projects.platformer.main
uv run -m demo_projects.pong.main
uv run -m demo_projects.sokoban.main
uv run -m demo_projects.multiplayerv2.client.main
```

</details>

### 3) Build your own minimal game

Create `your_project/main.py` (the `main.py` is actually important if you want to export to web later):

```python
import ajishio as aj

aj.room_set_caption("Hello, Ajishio")
aj.room_set_size(640, 360)
aj.game_start()
```

Run from repository root:

```bash
uv run -m your_project.main
```

Try one of the larger examples:

```bash
uv run -m demo_projects.platformer.main
```

## Demo Showcase

Ajishio ships with multiple complete demos for platformers, puzzle games, arcade clones, and
event a multiplayer example.

<table>
	<tr>
		<td align="center" width="50%">
			<a href="./demo_projects/platformer/main.py">
				<img src=".github/assets/demo_previews/platformer.gif" width="100%" alt="Platformer preview" />
			</a>
			<br />
			<a href="./demo_projects/platformer/main.py">Platformer</a>
		</td>
		<td align="center" width="50%">
			<a href="./demo_projects/pong/main.py">
				<img src=".github/assets/demo_previews/pong.gif" width="100%" alt="Pong preview" />
			</a>
			<br />
			<a href="./demo_projects/pong/main.py">Pong</a>
		</td>
	</tr>
	<tr>
		<td align="center" width="50%">
			<a href="./demo_projects/snake/main.py">
				<img src=".github/assets/demo_previews/snake.gif" width="100%" alt="Snake preview" />
			</a>
			<br />
			<a href="./demo_projects/snake/main.py">Snake</a>
		</td>
		<td align="center" width="50%">
			<a href="./demo_projects/tetris/main.py">
				<img src=".github/assets/demo_previews/tetris.gif" width="100%" alt="Tetris preview" />
			</a>
			<br />
			<a href="./demo_projects/tetris/main.py">Tetris</a>
		</td>
	</tr>
	<tr>
		<td align="center" width="50%">
			<a href="./demo_projects/minesweeper/main.py">
				<img src=".github/assets/demo_previews/minesweeper.gif" width="100%" alt="Minesweeper preview" />
			</a>
			<br />
			<a href="./demo_projects/minesweeper/main.py">Minesweeper</a>
		</td>
		<td align="center" width="50%">
			<a href="./demo_projects/sokoban/main.py">
				<img src=".github/assets/demo_previews/sokoban.gif" width="100%" alt="Sokoban preview" />
			</a>
			<br />
			<a href="./demo_projects/sokoban/main.py">Sokoban</a>
		</td>
	</tr>
	<tr>
		<td align="center" width="50%">
			<a href="./demo_projects/spinning_cube/main.py">
				<img src=".github/assets/demo_previews/spinning_cube.gif" width="100%" alt="Spinning cube preview" />
			</a>
			<br />
			<a href="./demo_projects/spinning_cube/main.py">Spinning Cube</a>
		</td>
		<td align="center" width="50%">
			<a href="./demo_projects/multiplayerv2/client/main.py">
				<img src=".github/assets/demo_previews/multiplayerv2_client.gif" width="100%" alt="Multiplayer demo preview" />
			</a>
			<br />
			<a href="./demo_projects/multiplayerv2/client/main.py">Multiplayer</a>
		</td>
	</tr>
</table>

- Run any demo locally:

```bash
uv run -m demo_projects.sokoban.main
```

- Play browser versions instantly:
	[Web Demos](https://tristanbatchler.github.io/ajishio/docs/demo-projects/)

## Web Export

Export any demo to a playable browser build with pygbag:

```bash
uv run pygbag_export.py demo_projects/platformer
```

The build artifacts are generated under the demo's `_web_build/` directory.

<details>
<summary><strong>Build-only mode (skip local server)</strong></summary>

```bash
uv run pygbag_export.py demo_projects/platformer --build
```

</details>


## Documentation

View the full documentation online:
[https://tristanbatchler.github.io/ajishio/docs/](https://tristanbatchler.github.io/ajishio/docs/)

If you're just looking for the API reference, it's available as a single page here:
[https://tristanbatchler.github.io/ajishio/docs/api/](https://tristanbatchler.github.io/ajishio/docs/api/)

The API page is auto-generated from the public `ajishio` facade. To refresh it locally:

```bash
uv run python scripts/gen_api_ref.py
```


## Roadmap

- [x] Load rooms from files (LDtk)
- [x] Support multiple rooms per game
- [x] Load and animate sprites (Aseprite export workflow)
- [x] Load and play sound/music
- [x] Support persistent objects
- [x] Profiling workflow docs and support
- [x] API docs generation via MkDocs
- [x] Browser export via pygbag
- [x] Faster collision checks using a spatial quadtree

## Contributing

Contributions are welcome. For development and documentation workflow details, start with
[docs/contributing.md](docs/contributing.md).