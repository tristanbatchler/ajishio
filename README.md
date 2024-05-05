# Ajishio

![Ajishio Taro](/.github/assets/ajishio_taro.png)

Ajishio is a stripped-down [pygame](https://www.pygame.org)-based game engine for creating 2D games. 
Its API is modelled after old [GameMaker](https://gamemaker.io) versions, think pre-Studio 1.4. The 
reason for this is that I wanted to create something that feels the same way as when I first started 
making games in GameMaker 7, but with the optional features of a modern language and the choice of 
using whatever text editor I want.

The name "Ajishio" is a reference to 
[Noboru Yamaguchi](https://cromartiehigh.fandom.com/wiki/Noboru_Yamaguchi), the most misunderstood 
comedian in Japan. No reason this would ever be relevant to the game engine, but I thought it was a 
cool name.

## Installation

Ajishio is not yet available on PyPI, so you'll have to install it from source. To do so, clone this 
repository and install the dependencies:

```bash
git clone https://github.com/tristanbatchler/ajishio
cd ajishio
python -m venv .venv
source .venv/bin/activate # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
```

To verify that the installation was successful, run the following command and you should see a blank 
window pop up:

```bash
python -m demo_projects.hello_world
```

## Quick Start

Inside the cloned repository, create a new directory for your project and create a new Python file 
inside it called `__main__.py`. Getting a blank window up and running is as simple as putting the 
following code in that file:
```python
import ajishio as aj

aj.room_set_caption("Hello, World!")
aj.game_start()
```

To run the game, execute the following command from the root of the repository:
```bash
python -m ajishio <your_project_directory>
```

To see more substantial examples, check out the [`demo_projects`](/demo_project/) directory. You can 
also run these in the same way, e.g. running the following command from the root of the repository 
will bring up a pre-made platformer game:
```bash
python -m ajishio.demo_projects.platformer
```

## VS Code Integration

If you're using VS Code, you can set up a task to debug your game with F5. To do this, add to the 
`.vscode/launch.json` file's `"configuration"` array the following:
```json
{
    "name": "<your project name>",
    "type": "debugpy",
    "request": "launch",
    "module": "<your.dot.separated.project.directory>"
}
```

For example, if your game script relative to the root of the repository is in 
`my_stuff/games/ziltoid_the_destroyer/__main__.py`, your `launch.json` file should look like this:
```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Ziltoid the Destroyer",
            "type": "debugpy",
            "request": "launch",
            "module": "my_stuff.games.ziltoid_the_destroyer"
        }
    ]
}
```

Now, if you go to the debug tab in VS Code (`Ctrl+Shift+D`), you should see your project name 
available to select in the dropdown list up top. Select it and press F5 to run and debug your game.

## Mypy Integration

Ajishio is fully typed with [mypy](https://mypy.readthedocs.io). If you're using VS Code, you can 
install the [mypy extension](https://marketplace.visualstudio.com/items?itemName=matangover.mypy) to 
get real-time type checking. 

First you need to tell the extension where to locate the Mypy daemon executable. To do this, go to 
your settings (`Ctrl+,`), find the `Mypy: Dmypy Executable` setting, and set it to 
```
${workspaceFolder}/.venv/bin/dmypy
```
or for Windows,
```
${workspaceFolder}/.venv/Scripts/dmypy.exe
```

Now, if you open a Python file in your project, you should see type errors and warnings underlined.

## TODO

- [x] Support to load rooms from files (only support for LDtk at the moment)
- [x] Room editor (use [LDtk](https://ldtk.io))
- [ ] Support for multiple rooms in a single game
- [ ] Support to load and draw sprites from files
- [ ] Sprite editor to define collision masks and load into the game
- [ ] Sprite editor to define animations and load into the game