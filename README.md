# Ajishio

![Ajishio Taro](/.github/assets/ajishio_taro.png)

Ajishio is a stripped-down [pygame-ce](https://github.com/pygame-community/pygame-ce)-based game engine for creating 2D games. 
Its API is modelled after old [GameMaker](https://gamemaker.io) versions, think pre-Studio 1.4. The 
reason for this is that I wanted to create something that feels the same way as when I first started 
making games in GameMaker 7, but with the optional features of a modern language and the choice of 
using whatever text editor I want.

The name "Ajishio" is a reference to 
[Noboru Yamaguchi](https://cromartiehigh.fandom.com/wiki/Noboru_Yamaguchi), the most misunderstood 
comedian in Japan. No reason this would ever be relevant to the game engine, but I thought it was a 
cool name.

## Installation

Ajishio is managed with [uv](https://github.com/astral-sh/uv). To get started, clone this repository
and let `uv` create and manage the virtual environment for you:

```bash
git clone https://github.com/tristanbatchler/ajishio
cd ajishio
uv sync
```

To verify that the installation was successful, run the following command and you should see a blank
window pop up:

```bash
uv run demo_projects/hello_world/main.py
```

## Quick Start

Inside the cloned repository, create a new directory for your project and create a new Python file 
inside it called `main.py`. Getting a blank window up and running is as simple as putting the 
following code in that file:
```python
import ajishio as aj

aj.room_set_caption("Hello, World!")
aj.game_start()
```

To run the game, execute the following command from the root of the repository:

```bash
uv run <your_project_directory>/main.py
```

```bash
uv run demo_projects/platformer/main.py
```
## Documentation
View tips and tricks, as well as an API reference, which aims to be similar to the GameMaker 8.1 API: 
[https://tristanbatchler.github.io/ajishio/docs](https://tristanbatchler.github.io/ajishio/docs)

## Demo projects

This repository comes loaded with heaps of example projects both to showcase what's possible, but to 
also provide example code snippets. To run them locally, simply run

```bash
uv run demo_projects/sokoban/main.py # Or minesweeper, platformer, tetris, etc...
```

If you just want to have a look now, you can instantly play all Ajishio demo projects in your 
browser, thanks to [pygbag](https://github.com/nicegui-org/pygbag) and GitHub Pages.

See [Web Demos](https://tristanbatchler.github.io/ajishio/docs/demo-projects) for the full, 
up-to-date list and links to play every demo.

## TODO

- [x] Support to load rooms from files (only support for LDtk at the moment)
- [x] Room editor (use [LDtk](https://ldtk.io))
- [x] Support for multiple rooms in a single game
- [x] Support to load and draw sprites from files (only support for Aseprite at the moment)
- [x] Sprite editor to define animations and load into the game
- [x] Load and play sounds
- [x] Load and play music
- [x] Support persistant objects
- [x] Support easy profiling
- [x] Add library mkdocs generation and docstrings for all exposed objects
- [x] Web export via pygbag
- [x] Faster collision detection using spatial quadtree