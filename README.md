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

To see more substantial examples, check out the [`demo_projects`](/demo_projects/) directory. You can 
also run these in the same way, e.g. running the following command from the root of the repository 
will bring up a pre-made platformer game:
```bash
python -m ajishio.demo_projects.platformer
```

## VS Code Integration

Firstly, it is recommended to install the 
[Python extension](https://marketplace.visualstudio.com/items?itemName=ms-python.python) before 
editing your game in VS Code. Once it is installed, ensure that the Python interpreter is set to the 
one in the virtual environment you created earlier. You can do this by opening the command palette 
(`Ctrl+Shift+P`) and typing `Python: Select Interpreter` and choose `./.venv/bin/python` or 
`./.venv/Scripts/python.exe` on Windows.

![Select Python Interpreter](/.github/assets/select_python_interpreter.png)


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
![VS Code Debug Tab](/.github/assets/vscode_debug_tab.png)

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
![Mypy Integration](/.github/assets/mypy_integration.png)

> Note: Mypy requires that you have an `__init__.py` file in your project directory, alongside your 
> `__main__.py` file. If you are not seeing any type errors, check that at least an empty 
> `__init__.py` file exists. If you still don't see any errors, try running `mypy .` in your 
> activated virtual environment and check the output.

## Loading Rooms

Currently, Ajishio only supports loading rooms in [LDtk](https://ldtk.io) format. First download 
the LDtk editor from the website, and create your room (there are some good tutorials out there on 
how to do this). Once you have your room, make sure to enable the "Super simple export" option in 
the Project Settings tab. This will export the room as a set of files in a folder that Ajishio can 
load directly.
![Super simple export](/.github/assets/super_simple_export.png)

To load the room in your game, copy the folder called `simplified/` which is generated by LDtk into 
your project directory somewhere. Then, to load the room, use the `aj.load_ldtk_levels` function, 
passing the path to the `simplified/` folder you copied as the argument. It will return a list of 
`aj.GameLevel` objects which you need to pass to the `aj.set_rooms` function.

In order for the engine to instance your tiles and entities, you need to define classes for each of 
them with the same name as it appears in LDtk. Tiles need to accept integer `tile_width` and 
`tile_height` arguments in their constructor. To make the engine aware of these classes, you need to 
inject them into the engine's namespace by calling the `aj.register_objects` function.

> Tip: It is recommended to save your LDtk project directly in your project directory, so that you can 
easily update the rooms without having to copy them over every time.

To see an example of this in action, check out the 
[`platformer`](/demo_projects/platformer/__main__.py) demo project.

## TODO

- [x] Support to load rooms from files (only support for LDtk at the moment)
- [x] Room editor (use [LDtk](https://ldtk.io))
- [x] Support for multiple rooms in a single game
- [x] Support to load and draw sprites from files
- [ ] Sprite editor to define collision masks and load into the game
- [x] Sprite editor to define animations and load into the game